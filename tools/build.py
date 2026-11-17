#!/usr/bin/env python3
import json, py_compile, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def main():
    print("SmartScreen OS build check")
    for name in ("system","home","devices"):
        dst=ROOT/"config"/f"{name}.json"
        src=ROOT/"config"/f"{name}.example.json"
        if not dst.exists():
            shutil.copy2(src,dst)
            print("Created:",dst.relative_to(ROOT))
    for path in sorted((ROOT/"config").glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
        print("JSON OK:",path.relative_to(ROOT))
    for path in sorted((ROOT/"src").rglob("*.py")):
        py_compile.compile(str(path),doraise=True)
        print("Python OK:",path.relative_to(ROOT))
    print("Build check passed.")

if __name__=="__main__":
    main()
