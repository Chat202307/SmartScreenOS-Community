from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from .bootstrap import create_runtime_host_from_config
from .host import RuntimeHost


DEFAULT_CONFIG_PATH = Path("config/runtime.yaml")


def run_runtime(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    host_factory: Callable[[Path], RuntimeHost] = (
        create_runtime_host_from_config
    ),
    wait: Callable[[], None] | None = None,
) -> int:
    print("SmartScreenOS Runtime starting...")
    print(f"Config: {config_path}")

    try:
        host = host_factory(config_path)
    except Exception as exc:
        print(
            "SmartScreenOS Runtime failed to start:",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1

    resolved_wait = wait or (lambda: time.sleep(3600))

    try:
        host.start_background()

        print("Runtime started.")
        print("Press Ctrl+C to stop.")

        while True:
            resolved_wait()

            if host.scheduler.background_failed:
                error = host.scheduler.last_background_error

                print(
                    "SmartScreenOS Runtime "
                    "background scheduler failed:",
                    file=sys.stderr,
                )

                print(
                    str(error)
                    if error is not None
                    else "unknown background scheduler error",
                    file=sys.stderr,
                )

                return 1

    except KeyboardInterrupt:
        return 0

    finally:
        print("SmartScreenOS Runtime stopping...")

        host.stop()
        host.join(timeout=5.0)

        print("SmartScreenOS Runtime stopped.")


def run_snapshot(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    host_factory: Callable[[Path], RuntimeHost] = (
        create_runtime_host_from_config
    ),
    wait: Callable[[], None] | None = None,
    timeout_seconds: float = 15.0,
    clock: Callable[[], float] | None = None,
) -> int:
    if timeout_seconds <= 0:
        raise ValueError(
            "Snapshot timeout must be greater than zero."
        )

    try:
        host = host_factory(config_path)
    except Exception as exc:
        print(
            "SmartScreenOS Runtime snapshot failed to start:",
            file=sys.stderr,
        )
        print(str(exc), file=sys.stderr)
        return 1

    resolved_wait = wait or (lambda: time.sleep(0.2))
    resolved_clock = clock or time.monotonic

    try:
        host.start_background()

        engine = getattr(host, "engine", None)
        get_health_summary = getattr(
            engine,
            "get_tick_health_summary",
            None,
        )

        if callable(get_health_summary):
            deadline = resolved_clock() + timeout_seconds

            while True:
                if get_health_summary():
                    break

                if host.scheduler.background_failed:
                    error = host.scheduler.last_background_error

                    print(
                        "SmartScreenOS Runtime "
                        "background scheduler failed:",
                        file=sys.stderr,
                    )
                    print(
                        str(error)
                        if error is not None
                        else "unknown background scheduler error",
                        file=sys.stderr,
                    )
                    return 1

                if resolved_clock() >= deadline:
                    break

                resolved_wait()
        else:
            # Compatibility path for simple hosts that do not expose
            # runtime tick-health information.
            resolved_wait()

        if host.scheduler.background_failed:
            error = host.scheduler.last_background_error

            print(
                "SmartScreenOS Runtime "
                "background scheduler failed:",
                file=sys.stderr,
            )
            print(
                str(error)
                if error is not None
                else "unknown background scheduler error",
                file=sys.stderr,
            )
            return 1

        print(
            json.dumps(
                host.snapshot(),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        return 0

    finally:
        host.stop()
        host.join(timeout=5.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smartscreen-runtime",
        description="Run the SmartScreenOS runtime host.",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the runtime YAML configuration file.",
    )

    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Print one runtime status snapshot and exit.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.snapshot:
        return run_snapshot(
            config_path=args.config,
        )

    return run_runtime(
        config_path=args.config,
    )


if __name__ == "__main__":
    raise SystemExit(main())
