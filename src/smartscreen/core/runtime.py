from pathlib import Path

from ..adapters.manager import AdapterManager
from ..adapters.mock import MockAdapter
from ..adapters.mqtt import MqttAdapter
from ..connection import ConnectionManager
from ..events import EventBus
from ..house import HouseModel
from ..feed import FeedGenerator
from ..context import ContextEngine
from ..home_profile import HomeProfile
from ..policy import PolicyEngine
from ..home_event import HomeEvent
from ..home_event_bus import HomeEventBus
from ..home_event_mapper import HomeEventMapper
from ..state_change import StateChangeDetector


class SmartScreenCore:
    def __init__(self, config, rooms, devices, states, project_root: Path):
        self.config = config
        self.rooms = rooms
        self.devices = devices
        self.states = states
        self.project_root = project_root
        self.adapters = AdapterManager()
        self.connections = ConnectionManager()
        self.events = EventBus()
        self.state_changes = StateChangeDetector()
        profile_config = config.get("home_profile", {}).get("home_profile", {})
        self.home_profile = HomeProfile(profile_config)
        self.policy = PolicyEngine()
        self.home_events = HomeEventBus()
        self.home_event_mapper = HomeEventMapper(devices)
        self.house = HouseModel(
            config["home"],
            rooms,
            devices,
            states,
            self.events,
        )
        self.feed = FeedGenerator(
            devices,
            self.events,
        )
        self.context = ContextEngine(
            self.house,
        )

    def configure_adapters(self):
        def update_state(device_id, available, state, attributes):
            if self.devices.get(device_id) is None:
                return

            result = self.state_changes.evaluate(
                device_id,
                available,
                state,
                attributes,
            )

            self.states.update(
                device_id,
                available=available,
                state=state,
                attributes=attributes,
            )

            if result["changed"]:
                payload = {
                    "device_id": device_id,
                    "available": bool(available),
                    "state": str(state),
                    "attributes": dict(attributes or {}),
                    "previous": result["previous"],
                    "current": result["current"],
                }
                self.events.publish(
                    "device.state_changed",
                    source="adapter",
                    payload=payload,
                )
                self.home_events.publish(
                    self.home_event_mapper.from_device_state(
                        device_id=device_id,
                        available=available,
                        state=state,
                        attributes=attributes,
                        previous=result["previous"],
                        current=result["current"],
                        source="adapter",
                    )
                )
            else:
                self.events.publish(
                    "device.state_seen",
                    source="adapter",
                    payload={
                        "device_id": device_id,
                        "available": bool(available),
                        "state": str(state),
                    },
                )

        adapter_config = self.config["adapters"]["adapters"]
        active = adapter_config.get("active", "mock")

        if active == "mqtt":
            adapter = MqttAdapter(
                update_state,
                self.devices.all(),
                dict(adapter_config.get("mqtt", {})),
                self.connections,
                self.events,
            )
            self.adapters.register(adapter)
            return

        if active == "mock":
            settings = dict(adapter_config.get("mock", {}))
            state_file = settings.get(
                "state_file",
                "config/mock_states.json",
            )
            adapter = MockAdapter(
                update_state,
                self.project_root / state_file,
            )
            self.adapters.register(adapter)
            return

        raise ValueError("Unsupported active adapter: " + active)

    def start(self):
        self.events.publish(
            "core.starting",
            source="core",
            payload={},
        )
        self.adapters.start_all()
        self.events.publish(
            "core.started",
            source="core",
            payload={},
        )

    def stop(self):
        self.events.publish(
            "core.stopping",
            source="core",
            payload={},
        )
        self.adapters.stop_all()
        self.events.publish(
            "core.stopped",
            source="core",
            payload={},
        )

    def command(self, device_id, command, value=None):
        device = self.devices.get(device_id)
        if device is None:
            raise ValueError("Unknown device: " + device_id)

        if command not in device.capabilities:
            raise ValueError(
                "Device %s does not support command: %s"
                % (device_id, command)
            )

        adapter_id = device.adapter

        self.events.publish(
            "device.command_requested",
            source="api",
            payload={
                "device_id": device_id,
                "command": command,
                "value": value,
                "adapter": adapter_id,
            },
        )

        self.adapters.send_command(
            adapter_id,
            device_id,
            command,
            value,
        )
