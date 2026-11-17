#!/usr/bin/env python3
"""Build and smoke-test only this offline demo; never touch a production host."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.release-validation'


def run(*args, timeout=60):
    return subprocess.run(['docker', *args], cwd=ROOT, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, check=True)


def main():
    OUTPUT.mkdir(exist_ok=True)
    report = {'schema': 1, 'complete': False, 'image_published': False,
              'nas_accessed': False, 'production_accessed': False,
              'platform': 'linux/amd64', 'checks': {}}
    token = uuid.uuid4().hex[:12]
    tag = 'smartscreenos-oss-verify:' + token
    name = 'smartscreenos-oss-verify-' + token
    cid = None
    stage = 'docker_available'
    try:
        if not shutil.which('docker'):
            raise RuntimeError('Docker CLI missing; install/start Docker Desktop')
        # No remote Docker daemon: this tool must run locally on the iMac.
        stage = 'local_docker_context'
        if os.environ.get('DOCKER_HOST') and not os.environ['DOCKER_HOST'].startswith('unix://'):
            raise RuntimeError('Remote DOCKER_HOST is not allowed')
        context = json.loads(run('context', 'inspect').stdout)
        endpoint = context[0]['Endpoints']['docker']['Host']
        if not endpoint.startswith('unix://'):
            raise RuntimeError('Select a local Docker Desktop context; remote daemons are not allowed')
        run('info', '--format', '{{.OSType}}')
        stage = 'source_inventory'
        inventory_path = ROOT / 'FILE_INVENTORY.json'
        raw_inventory = inventory_path.read_bytes()
        inventory = json.loads(raw_inventory)
        for item in inventory['files']:
            path = ROOT / item['path']
            if not path.resolve().is_relative_to(ROOT.resolve()) or path.is_symlink():
                raise RuntimeError('Invalid inventory path')
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                raise RuntimeError('Candidate files changed; use the original release package')
        report['inventory_sha256'] = hashlib.sha256(raw_inventory).hexdigest()
        stage = 'docker_build'
        print('构建演示镜像；不连接 NAS，不推送镜像。', flush=True)
        # Build output stays local; no credentials/log contents enter the report.
        with (OUTPUT / 'docker-build.log').open('w') as log:
            subprocess.run(['docker', 'build', '--platform', 'linux/amd64',
                            '--tag', tag, '.'], cwd=ROOT, stdout=log,
                           stderr=subprocess.STDOUT, timeout=1800, check=True)
        report['checks']['docker_build'] = True
        image = json.loads(run('image', 'inspect', tag).stdout)[0]
        report['image_id'] = image['Id']
        if image['Architecture'] != 'amd64' or image['Os'] != 'linux':
            raise RuntimeError('Unexpected image platform')
        if image['Config']['User'] != '10001:10001':
            raise RuntimeError('Image must run as UID/GID 10001')
        stage = 'demo_container'
        cid = run('create', '--name', name, '--label', 'smartscreenos.oss-verification=true',
                  '--platform', 'linux/amd64', '--read-only', '--cap-drop', 'ALL',
                  '--security-opt', 'no-new-privileges:true',
                  '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,uid=10001,gid=10001,mode=0700,size=32m',
                  '-p', '127.0.0.1::8080', tag).stdout.strip()
        run('start', cid)
        state = json.loads(run('inspect', cid).stdout)[0]
        if any(m['Type'] == 'bind' for m in state['Mounts']):
            raise RuntimeError('Host bind mounts are not allowed')
        binding = state['NetworkSettings']['Ports']['8080/tcp'][0]
        if binding['HostIp'] != '127.0.0.1':
            raise RuntimeError('Demo port is not loopback-only')
        base = 'http://127.0.0.1:' + binding['HostPort']
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        stage = 'demo_http'
        deadline = time.monotonic() + 60
        while True:
            try:
                with opener.open(base + '/', timeout=3) as response:
                    if response.status != 200:
                        raise RuntimeError('Unexpected homepage response')
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Demo did not become ready')
                time.sleep(1)
        for path in ('/api/dashboard', '/api/todos'):
            with opener.open(base + path, timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError('Unexpected API response')
                json.load(response)
        report['checks']['demo_http'] = True
        stage = 'runtime_and_notices'
        script = "import os,pathlib,json; assert os.getuid()==10001; assert pathlib.Path('/app/LICENSE').is_file(); assert pathlib.Path('/app/third_party/licenses/LGPL-3.0.txt').is_file(); print(json.dumps({'uid':os.getuid()}))"
        run('exec', cid, 'python', '-c', script)
        state = json.loads(run('inspect', cid).stdout)[0]
        if not state['State']['Running']:
            raise RuntimeError('Demo container stopped')
        report['checks']['nonroot_runtime_and_notices'] = True
        report['complete'] = True
    except Exception as exc:
        report['failure_stage'] = stage
        # Do not serialize daemon errors, env vars, stdout or source data.
        report['error_type'] = type(exc).__name__
        if isinstance(exc, RuntimeError):
            print(str(exc), file=sys.stderr)
    finally:
        if cid:
            try:
                run('rm', '-f', cid)
                report['own_container_removed'] = True
            except Exception:
                report['own_container_removed'] = False
                report['complete'] = False
                print('请手动删除本工具的临时容器：' + name, file=sys.stderr)
        else:
            report['own_container_removed'] = True
        report_path = OUTPUT / 'docker-verification.json'
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        print('结果文件：' + str(report_path))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
