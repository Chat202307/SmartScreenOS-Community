import unittest

from src.smartscreen.core import SmartScreenCore
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore


class RecordingAdapters:
    def __init__(self):
        self.commands = []

    def send_command(
        self,
        adapter_id,
        device_id,
        command,
        value=None,
    ):
        self.commands.append(
            (adapter_id, device_id, command, value)
        )


class CoreAdapterRoutingTests(unittest.TestCase):
    def test_command_uses_device_adapter(self):
        rooms = RoomRegistry([
            Room("living", "客厅", "public_area", 10),
        ])

        devices = DeviceRegistry([
            Device(
                "living.light",
                "客厅灯",
                "living",
                "light",
                "home_assistant",
                ["turn_on", "turn_off"],
            ),
        ], rooms)

        states = StateStore()
        states.initialize("living.light")

        config = {
            "adapters": {
                "adapters": {
                    "active": "mqtt",
                }
            },
            "home": {
                "home": {
                    "name": "测试家庭",
                }
            },
        }

        core = SmartScreenCore(
            config,
            rooms,
            devices,
            states,
            project_root=None,
        )

        recording = RecordingAdapters()
        core.adapters = recording

        core.command(
            "living.light",
            "turn_on",
        )

        self.assertEqual(
            recording.commands,
            [
                (
                    "home_assistant",
                    "living.light",
                    "turn_on",
                    None,
                )
            ],
        )
    def test_command_event_uses_device_adapter(self):
        rooms = RoomRegistry([
            Room("living", "客厅", "public_area", 10),
        ])

        devices = DeviceRegistry([
            Device(
                "living.light",
                "客厅灯",
                "living",
                "light",
                "home_assistant",
                ["turn_on", "turn_off"],
            ),
        ], rooms)

        states = StateStore()
        states.initialize("living.light")

        config = {
            "adapters": {
                "adapters": {
                    "active": "mqtt",
                }
            },
            "home": {
                "home": {
                    "name": "测试家庭",
                }
            },
        }

        core = SmartScreenCore(
            config,
            rooms,
            devices,
            states,
            project_root=None,
        )

        core.adapters = RecordingAdapters()

        core.command(
            "living.light",
            "turn_on",
        )

        events = core.events.recent(10)
        requested = [
            event
            for event in events
            if event.name == "device.command_requested"
        ]

        self.assertEqual(len(requested), 1)
        self.assertEqual(
            requested[0].payload["adapter"],
            "home_assistant",
        )


if __name__ == "__main__":
    unittest.main()
