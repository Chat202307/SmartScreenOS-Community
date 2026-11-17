#!/usr/bin/env python3
"""Synthetic Docker execution on GitHub-hosted Linux only. Never SSH to NAS."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid


LABEL = "org.smartscreenos.synthetic-caldav"
ROOT = Path(__file__).resolve().parents[1]


class CommandFailure(RuntimeError):
    def __init__(self, stderr):
        super().__init__("synthetic runner command failed")
        self.diagnostic = stderr[-8000:]


def command(*args, check=True):
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode:
        # Only this synthetic runner may retain a bounded diagnostic. Never use
        # this helper for NAS export, production processes or real credentials.
        raise CommandFailure(result.stderr)
    return result


def require_hosted_runner(environ):
    if (environ.get("GITHUB_ACTIONS") != "true" or environ.get("RUNNER_ENVIRONMENT") != "github-hosted"
            or environ.get("RUNNER_OS") != "Linux" or environ.get("DOCKER_HOST")
            or environ.get("DOCKER_CONTEXT", "default") != "default"):
        raise RuntimeError("execution is restricted to the GitHub-hosted Linux runner")


def execute(image, report_file):
    require_hosted_runner(os.environ)
    endpoint = command("docker", "context", "inspect", "default", "--format", "{{.Endpoints.docker.Host}}").stdout.strip()
    if endpoint != "unix:///var/run/docker.sock":
        raise RuntimeError("remote Docker endpoints are forbidden")
    scope = "ssos-caldav-e2e-" + uuid.uuid4().hex[:12]
    ids, network_created = [], False
    report = {"executed_at_utc": datetime.now(timezone.utc).isoformat(),
              "environment": "GitHub-hosted Linux; Work has no container runtime",
              "real_apple_credentials": False, "nas_access": False,
              "home_services_connected": False, "published_ports": [], "cleanup_passed": False}
    report_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        report["image_id"] = command("docker", "image", "inspect", image, "--format", "{{.Id}}").stdout.strip()
        report["docker_version"] = command("docker", "version", "--format", "{{.Server.Version}}").stdout.strip()
        command("docker", "network", "create", "--internal", "--label", LABEL + "=" + scope, scope)
        network_created = True
        if command("docker", "network", "inspect", "--format", "{{.Internal}}", scope).stdout.strip() != "true":
            raise RuntimeError("test network is not internal")
        report["network_internal"] = True
        with tempfile.TemporaryDirectory(prefix="ssos-caldav-fixtures-") as workspace:
            directory = Path(workspace)
            cert, key = directory / "test-ca.pem", directory / "test-key.pem"
            command("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                    "-subj", "/CN=mock-caldav", "-addext", "subjectAltName=DNS:mock-caldav",
                    "-keyout", str(key), "-out", str(cert))
            # Synthetic TLS key, not an account credential; private host directory,
            # file-only binds and no artifact upload of this temporary directory.
            for path in (cert, key):
                path.chmod(0o444)
            password, readable, restricted = (directory / name for name in ("mock-password", "readable.json", "restricted.json"))
            password.write_text("fixture-password")
            readable.write_text('{"synthetic":true}')
            restricted.write_text('{"synthetic-restricted":true}')
            password.chmod(0o444)
            readable.chmod(0o444)
            restricted.chmod(0o600)  # Owned by CI host UID, not container UID 10001.

            def bind(source, target):
                return ("--mount", "type=bind,source=" + str(source) + ",target=" + target + ",readonly")

            def start(role, alias, module, arguments, mounts=(), detached=True):
                name = scope + "-" + role
                # Even `docker run` that fails after create must be scoped for cleanup.
                ids.append(name)
                args = ["docker", "run", "--name", name, "--label", LABEL + "=" + scope,
                        "--network", scope, "--network-alias", alias, "--user", "10001:10001",
                        "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                        "--pids-limit", "32", "--memory", "256m", "--cpus", "1.0",
                        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,uid=10001,gid=10001,mode=0700,size=16m",
                        "--tmpfs", "/test-data:rw,noexec,nosuid,nodev,uid=10001,gid=10001,mode=0700,size=8m"]
                for variable in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
                    args += ["--env", variable + "="]
                args += ["--env", "NO_PROXY=*"]
                for source, target in mounts:
                    args += bind(source, target)
                args += ["--entrypoint", "python"]
                if detached:
                    args += ["-d"]
                args += [image] + (["-m", module] if module else []) + list(arguments)
                result = command(*args)
                if detached:
                    identifier = result.stdout.strip()
                    if not re.fullmatch(r"[0-9a-f]{64}", identifier):
                        raise RuntimeError("unexpected container identity")
                return result

            start("mock", "mock-caldav", "src.smartscreen_display.calendar_mock_dav",
                  ["--cert", "/test/ca.pem", "--key", "/test/key.pem"], [(cert, "/test/ca.pem"), (key, "/test/key.pem")])
            start("probe", "calendar-probe", "src.smartscreen_display.calendar_test_server",
                  ["--host", "0.0.0.0", "--port", "19081", "--mock-caldav", "--mock-ca-file", "/test/ca.pem",
                   "--mock-password-file", "/test/mock-password"], [(cert, "/test/ca.pem"), (password, "/test/mock-password")])

            start("background", "calendar-background", "src.smartscreen_display.calendar_test_server",
                  ["--host", "0.0.0.0", "--port", "19081", "--mock-caldav", "--background",
                   "--mock-ca-file", "/test/ca.pem", "--mock-password-file", "/test/mock-password"],
                  [(cert, "/test/ca.pem"), (password, "/test/mock-password")])

            # Explicitly check actual mounts and network isolation, not just YAML.
            for identifier in ids:
                template = ('{"ReadonlyRootfs":{{json .HostConfig.ReadonlyRootfs}},'
                            '"User":{{json .Config.User}},"Ports":{{json .HostConfig.PortBindings}},'
                            '"Networks":{{json .NetworkSettings.Networks}},"Mounts":{{json .Mounts}}}')
                state = json.loads(command("docker", "inspect", "--format", template, identifier).stdout)
                if not state["ReadonlyRootfs"] or state["User"] != "10001:10001" or state["Ports"]:
                    raise RuntimeError("container runtime isolation mismatch")
                if set(state["Networks"]) != {scope} or any(mount.get("RW") for mount in state["Mounts"] if mount["Type"] == "bind"):
                    raise RuntimeError("container network/mount isolation mismatch")
            result = start("checker", "checker", None, ["/test/verify.py"], [
                (cert, "/test/ca.pem"), (readable, "/test/readable.json"), (restricted, "/test/restricted.json"),
                (ROOT / "tools/verify_mock_caldav_container.py", "/test/verify.py"),
                (ROOT / "tools/check_lab_permissions.py", "/test/check_lab_permissions.py"),
            ], detached=False)
            report["checks"] = json.loads(result.stdout.strip())
            report["result"] = "passed"
    except Exception as error:
        report["result"] = "failed"
        if isinstance(error, CommandFailure):
            report["synthetic_diagnostic_tail"] = error.diagnostic
        raise
    finally:
        cleanup_ok = True
        for identifier in reversed(ids):
            owner = command("docker", "inspect", "--format", '{{index .Config.Labels "' + LABEL + '"}}', identifier, check=False)
            if owner.returncode:
                continue
            if owner.stdout.strip() != scope:
                cleanup_ok = False
                continue
            if command("docker", "rm", "-f", identifier, check=False).returncode:
                cleanup_ok = False
        if network_created:
            template = '{"owner":{{json (index .Labels "' + LABEL + '")}},"members":{{json .Containers}}}'
            state = command("docker", "network", "inspect", "--format", template, scope, check=False)
            if state.returncode:
                cleanup_ok = False
            else:
                data = json.loads(state.stdout)
                if data["owner"] != scope or data["members"]:
                    cleanup_ok = False
                elif command("docker", "network", "rm", scope, check=False).returncode:
                    cleanup_ok = False
        report["cleanup_passed"] = cleanup_ok
        if not cleanup_ok:
            report["result"] = "failed"
        report_file.write_text(json.dumps(report, indent=2) + "\n")
        if not cleanup_ok:
            raise RuntimeError("scoped test cleanup failed")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="smartscreenos:caldav-ci")
    parser.add_argument("--report", type=Path, default=Path("test-results/isolated-caldav.json"))
    parser.add_argument("--execute-ci", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute_ci:
        print("DRY RUN: synthetic Docker tests require the verified GitHub-hosted runner. No Docker or SSH executed.")
        return
    result = execute(args.image, args.report)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
