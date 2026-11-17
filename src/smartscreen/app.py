"""SmartScreen OS Core v0.4."""

import argparse
from pathlib import Path

from .api import ApiApplication, run_api
from .config_loader import load_all
from .core import SmartScreenCore
from .models import Device, Room
from .registry import DeviceRegistry, RoomRegistry
from .state_store import StateStore


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
WEB_ROOT = ROOT / "dashboard"


def build_core():
    config = load_all(CONFIG_DIR)

    rooms = RoomRegistry(
        Room(
            id=item["id"],
            name=item["name"],
            area=item["area"],
            order=int(item.get("order", 0)),
        )
        for item in config["home"]["rooms"]
    )

    devices = DeviceRegistry(
        (
            Device(
                id=item["id"],
                name=item["name"],
                room=item["room"],
                type=item["type"],
                adapter=item["adapter"],
                capabilities=list(item.get("capabilities", [])),
                adapter_config=dict(item.get("adapter_config", {})),
            )
            for item in config["devices"]["devices"]
        ),
        rooms,
    )

    states = StateStore()
    for device in devices.all():
        states.initialize(device.id)

    core = SmartScreenCore(
        config,
        rooms,
        devices,
        states,
        ROOT,
    )
    core.configure_adapters()

    return config, rooms, devices, states, core


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()

    config, rooms, devices, states, core = build_core()
    system = config["system"]["system"]
    home = config["home"]["home"]

    print("")
    print("========================================")
    print("SmartScreen OS Core v0.4")
    print("========================================")
    print("Version :", system["version"])
    print("Home    :", home["name"])
    print("Rooms   :", len(rooms.all()))
    print("Devices :", len(devices.all()))
    print("Dev port:", system["development_port"])
    print("Stable  :", system["stable_port"])
    print("========================================")
    print("")

    core.start()

    if not args.serve:
        print("Adapters:", core.adapters.health())
        print("Device model validation passed.")
        core.stop()
        return

    app = ApiApplication(
        config,
        rooms,
        devices,
        states,
        core,
    )

    try:
        run_api(
            app,
            host="0.0.0.0",
            port=int(system["development_port"]),
            web_root=WEB_ROOT,
        )
    finally:
        core.stop()


if __name__ == "__main__":
    main()
