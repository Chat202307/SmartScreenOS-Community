#!/usr/bin/env python3
from __future__ import print_function

import importlib.util
import sys
import traceback
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
TESTS = PROJECT / "tests"


def category_for(path):
    relative = path.relative_to(TESTS)
    parts = relative.parts

    if parts and parts[0] == "platform":
        return "Platform"
    if parts and parts[0] == "architecture":
        return "Architecture"
    if len(parts) == 1:
        return "Runtime"
    return "Other"


def module_name_for(path):
    relative = path.relative_to(PROJECT)
    safe = "_".join(relative.with_suffix("").parts)
    return "smartscreen_test_" + safe.replace("-", "_")


def load_module(path):
    name = module_name_for(path)
    spec = importlib.util.spec_from_file_location(name, str(path))

    if spec is None or spec.loader is None:
        raise ImportError("Cannot create module spec for %s" % path)

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def collect():
    grouped = {
        "Runtime": [],
        "Platform": [],
        "Architecture": [],
        "Other": [],
    }

    for path in sorted(TESTS.rglob("test_*.py")):
        grouped[category_for(path)].append(path)

    return grouped


def run_group(name, paths):
    suite = unittest.TestSuite()
    import_errors = []

    for path in paths:
        try:
            module = load_module(path)
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(module)
            )
        except Exception as exc:
            import_errors.append((path, exc, traceback.format_exc()))

    print("")
    print("=" * 72)
    print("%s tests" % name)
    print("=" * 72)

    if not paths:
        print("No test files found.")
        return {
            "name": name,
            "files": 0,
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "import_errors": 0,
            "successful": True,
        }

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    for path, exc, details in import_errors:
        print("")
        print("IMPORT ERROR:", path)
        print(details)

    return {
        "name": name,
        "files": len(paths),
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "import_errors": len(import_errors),
        "successful": result.wasSuccessful() and not import_errors,
    }


def print_summary(results):
    print("")
    print("=" * 72)
    print("SmartScreen Test Summary")
    print("=" * 72)

    total_files = 0
    total_tests = 0
    all_ok = True

    for item in results:
        total_files += item["files"]
        total_tests += item["tests"]
        all_ok = all_ok and item["successful"]

        status = "PASS" if item["successful"] else "FAIL"
        print(
            "{:<14} {:<4}  files={:<3} tests={:<4} "
            "failures={} errors={} import_errors={}".format(
                item["name"],
                status,
                item["files"],
                item["tests"],
                item["failures"],
                item["errors"],
                item["import_errors"],
            )
        )

    print("-" * 72)
    print("Total files :", total_files)
    print("Total tests :", total_tests)
    print("Result      :", "PASS" if all_ok else "FAIL")
    print("=" * 72)

    return all_ok


def main():
    if not TESTS.is_dir():
        print("ERROR: tests directory not found:", TESTS, file=sys.stderr)
        return 2

    if str(PROJECT) not in sys.path:
        sys.path.insert(0, str(PROJECT))

    grouped = collect()
    results = []

    for name in ("Runtime", "Platform", "Architecture", "Other"):
        results.append(run_group(name, grouped[name]))

    return 0 if print_summary(results) else 1


if __name__ == "__main__":
    sys.exit(main())
