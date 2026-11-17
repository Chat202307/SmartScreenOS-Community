#!/usr/bin/env python3
"""Run as UID/GID 10001 in an approved isolated test container; no chmod/chown."""
import argparse
import os
from pathlib import Path
import tempfile


def check(root, *, write_probe=False):
    root = Path(root)
    # Never accept production /persistent, /share or arbitrary traversal/symlinks.
    if root != Path("/test-data") or root.is_symlink() or root.resolve() != root:
        raise ValueError("only the isolated /test-data mount is permitted")
    if os.geteuid() != 10001 or os.getegid() != 10001:
        raise ValueError("run the check as UID/GID 10001")
    mounts = Path("/proc/self/mountinfo").read_text().splitlines()
    if not any(line.split(" - ", 1)[0].split()[4] == str(root)
               and line.split(" - ", 1)[1].split()[0] == "tmpfs" for line in mounts):
        raise ValueError("only the dedicated test tmpfs mount is permitted")
    if not os.access(root, os.R_OK | os.W_OK | os.X_OK):
        raise ValueError("isolated test directory permissions failed")
    if write_probe:
        # Only a new temporary file in the dedicated test mount; never edit data.
        with tempfile.TemporaryFile(dir=root) as stream:
            stream.write(b"lab-permission-probe")
            stream.flush()
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-probe", action="store_true")
    args = parser.parse_args(argv)
    check("/test-data", write_probe=args.write_probe)
    print("isolated UID/GID permission check passed")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("isolated permission check refused or failed") from None
