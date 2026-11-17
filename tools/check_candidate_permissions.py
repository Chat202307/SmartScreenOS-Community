#!/usr/bin/env python3
"""Read-only candidate mount/DAC preflight. No chmod/chown, network or writes."""
import json
import os
from pathlib import Path
import stat


def check(config=Path('/candidate-config'), data=Path('/candidate-data'),
          secrets=Path('/run/secrets')):
    if os.geteuid() != 10001 or os.getegid() != 10001:
        raise ValueError('candidate UID/GID required')
    for root in (config, data):
        if root.is_symlink() or not root.is_dir() or not os.access(root, os.R_OK | os.X_OK):
            raise ValueError('candidate directory access refused')
    if not os.statvfs(config).f_flag & os.ST_RDONLY:
        raise ValueError('candidate config must be mounted read-only')
    count = 0
    for path in config.rglob('*'):
        if path.is_symlink():
            raise ValueError('candidate symlinks require private review')
        if path.is_file():
            with path.open('rb') as stream:
                stream.read(1)
            count += 1
    for name in ('icloud_username', 'icloud_app_password'):
        path = secrets / name
        mode = stat.S_IMODE(path.stat().st_mode)
        if (path.is_symlink() or not path.is_file() or mode not in (0o400, 0o440, 0o600, 0o640)
                or not os.statvfs(path).f_flag & os.ST_RDONLY):
            raise ValueError('candidate secret permissions refused')
        with path.open('rb') as stream:
            value = stream.read(4097)
        if not value.strip() or len(value) > 4096:
            raise ValueError('candidate secret unavailable')
    photos, todos = data / 'photos', data / 'todos'
    if (photos.is_symlink() or todos.is_symlink() or not photos.is_dir() or not todos.is_dir()
            or os.statvfs(data).f_flag & os.ST_RDONLY or not os.access(photos, os.R_OK | os.X_OK)
            or not os.access(todos, os.R_OK | os.W_OK | os.X_OK)):
        raise ValueError('candidate data access refused')
    todo_file = todos / 'todos.json'
    if todo_file.exists() and (todo_file.is_symlink() or not os.access(todo_file, os.R_OK | os.W_OK)):
        raise ValueError('candidate todo access refused')
    return dict(uid_gid_verified=True, config_readonly_readable=True,
                config_file_count=count, secret_readonly_private_readable=True,
                candidate_data_access_reported=True, actual_write_probe_executed=False)


if __name__ == '__main__':
    try:
        print(json.dumps(check()))
    except Exception:
        raise SystemExit('candidate permission preflight refused; no paths or values logged') from None
