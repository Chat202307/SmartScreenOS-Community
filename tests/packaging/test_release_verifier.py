import importlib.util
import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


def setup_tool(monkeypatch, tmp_path, fail=None, endpoint='unix:///tmp/docker.sock'):
    path = Path(__file__).resolve().parents[2] / 'tools/verify_docker_release.py'
    spec = importlib.util.spec_from_file_location('release_verify', path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    monkeypatch.setattr(tool, 'ROOT', tmp_path)
    monkeypatch.setattr(tool, 'OUTPUT', tmp_path / '.release-validation')
    monkeypatch.setattr(tool.shutil, 'which', lambda _: '/fake/docker')
    monkeypatch.delenv('DOCKER_HOST', raising=False)
    (tmp_path / 'FILE_INVENTORY.json').write_text('{"files": []}')
    calls = []

    def run(*args, **kwargs):
        calls.append(args)
        if fail == args[0]:
            raise subprocess.CalledProcessError(1, args)
        if args[:2] == ('context', 'inspect'):
            value = [{'Endpoints': {'docker': {'Host': endpoint}}}]
        elif args[:2] == ('image', 'inspect'):
            value = [{'Id': 'sha256:synthetic', 'Architecture': 'amd64', 'Os': 'linux',
                      'Config': {'User': '10001:10001'}}]
        elif args[0] == 'inspect':
            value = [{'Mounts': [], 'State': {'Running': True},
                      'NetworkSettings': {'Ports': {'8080/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '51234'}]}}}]
        else:
            return SimpleNamespace(stdout='synthetic-cid')
        return SimpleNamespace(stdout=json.dumps(value))

    monkeypatch.setattr(tool, 'run', run)
    def build(args, **kwargs):
        calls.append(tuple(args))
        assert args[:2] == ['docker', 'build']
        if fail == 'build':
            raise subprocess.CalledProcessError(1, args)
    monkeypatch.setattr(tool.subprocess, 'run', build)
    class Response(io.BytesIO):
        status = 200
    monkeypatch.setattr(tool.urllib.request, 'build_opener', lambda *a: SimpleNamespace(open=lambda *a, **k: Response(b'{}')))
    return tool, calls


def result(tool):
    return json.loads((tool.OUTPUT / 'docker-verification.json').read_text())


def test_success_builds_only_local_demo_and_removes_own_container(monkeypatch, tmp_path):
    tool, calls = setup_tool(monkeypatch, tmp_path)
    assert tool.main() == 0
    assert result(tool)['complete']
    assert ('rm', '-f', 'synthetic-cid') in calls
    assert not any(c[0] in ('ssh', 'sudo', 'push', 'pull') for c in calls)
    run = next(c for c in calls if c[0] == 'create')
    assert '-v' not in run and '--mount' not in run
    assert '127.0.0.1::8080' in run


def test_failure_after_start_cleans_up_only_own_container(monkeypatch, tmp_path):
    tool, calls = setup_tool(monkeypatch, tmp_path, fail='exec')
    assert tool.main() == 1
    report = result(tool)
    assert not report['complete'] and report['own_container_removed']
    assert ('rm', '-f', 'synthetic-cid') in calls


def test_failed_build_does_not_start_container(monkeypatch, tmp_path):
    tool, calls = setup_tool(monkeypatch, tmp_path, fail='build')
    assert tool.main() == 1
    assert result(tool)['failure_stage'] == 'docker_build'
    assert not any(c[0] in ('create', 'start', 'rm') for c in calls)


def test_remote_daemon_is_rejected(monkeypatch, tmp_path):
    tool, calls = setup_tool(monkeypatch, tmp_path, endpoint='ssh://nas.example.invalid')
    assert tool.main() == 1
    assert result(tool)['failure_stage'] == 'local_docker_context'
    assert not any(c[0] in ('docker', 'create', 'start', 'rm') for c in calls)


def test_changed_source_is_rejected_before_build(monkeypatch, tmp_path):
    tool, calls = setup_tool(monkeypatch, tmp_path)
    (tmp_path / 'FILE_INVENTORY.json').write_text(json.dumps({'files': [{'path': 'LICENSE', 'sha256': 'bad'}]}))
    (tmp_path / 'LICENSE').write_text('modified')
    assert tool.main() == 1
    assert result(tool)['failure_stage'] == 'source_inventory'
    assert not any(c[0] == 'docker' for c in calls)


def test_start_failure_cleans_created_container(monkeypatch, tmp_path):
    tool, calls = setup_tool(monkeypatch, tmp_path, fail='start')
    assert tool.main() == 1
    assert result(tool)['own_container_removed']
    assert ('rm', '-f', 'synthetic-cid') in calls
