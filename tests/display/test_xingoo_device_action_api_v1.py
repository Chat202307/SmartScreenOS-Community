import json

from src.smartscreen_display.server import (
    SnapshotApplication,
)


class FakeHost:
    def snapshot(self):
        return {
            "capabilities": {},
        }


class FakeDeviceControlDispatcher:
    def __init__(self):
        self.calls = []

    def execute(
        self,
        *,
        device_id,
        control_id,
        value,
    ):
        self.calls.append(
            (
                device_id,
                control_id,
                value,
            )
        )

        return "generic-command"


def create_generic_control_app(
    dispatcher=None,
    refresher=None,
):
    return SnapshotApplication(
        FakeHost(),
        device_control_dispatcher=(
            dispatcher
        ),
        device_state_refresher=(
            refresher
        ),
    )


def test_device_action_api_dispatches_generic_power_control():
    dispatcher = (
        FakeDeviceControlDispatcher()
    )

    app = create_generic_control_app(
        dispatcher
    )

    status, _, body = app.handle(
        method="POST",
        path="/api/device/actions",
        body=json.dumps(
            {
                "device_id": "device-1",
                "control_id": "power",
                "value": True,
            }
        ).encode("utf-8"),
    )

    assert status == 200

    assert dispatcher.calls == [
        (
            "device-1",
            "power",
            True,
        )
    ]

    assert json.loads(
        body.decode("utf-8")
    ) == {
        "result": "generic-command",
    }


def test_device_action_api_dispatches_generic_select_control():
    dispatcher = (
        FakeDeviceControlDispatcher()
    )

    app = create_generic_control_app(
        dispatcher
    )

    status, _, _ = app.handle(
        method="POST",
        path="/api/device/actions",
        body=json.dumps(
            {
                "device_id": "device-1",
                "control_id": "mode",
                "value": "sleep",
            }
        ).encode("utf-8"),
    )

    assert status == 200

    assert dispatcher.calls == [
        (
            "device-1",
            "mode",
            "sleep",
        )
    ]


def test_device_action_api_requires_generic_dispatcher():
    app = create_generic_control_app()

    status, _, body = app.handle(
        method="POST",
        path="/api/device/actions",
        body=json.dumps(
            {
                "device_id": "device-1",
                "control_id": "power",
                "value": True,
            }
        ).encode("utf-8"),
    )

    assert status == 503

    assert (
        "dispatcher"
        in json.loads(
            body.decode("utf-8")
        )["error"]
    )


def test_device_action_api_rejects_unknown_generic_control():
    class RejectingDispatcher:
        def execute(
            self,
            *,
            device_id,
            control_id,
            value,
        ):
            raise ValueError(
                "unknown device control: "
                + device_id
                + " / "
                + control_id
            )

    app = create_generic_control_app(
        RejectingDispatcher()
    )

    status, _, body = app.handle(
        method="POST",
        path="/api/device/actions",
        body=json.dumps(
            {
                "device_id": "device-1",
                "control_id": "unknown",
                "value": True,
            }
        ).encode("utf-8"),
    )

    assert status == 403

    assert (
        "unknown device control"
        in json.loads(
            body.decode("utf-8")
        )["error"]
    )


def test_generic_device_action_refreshes_state_after_command():
    events = []

    class Dispatcher:
        def execute(
            self,
            *,
            device_id,
            control_id,
            value,
        ):
            events.append(
                "execute"
            )
            return "command"

    class Refresher:
        def refresh(self):
            events.append(
                "refresh"
            )

    app = create_generic_control_app(
        Dispatcher(),
        Refresher(),
    )

    status, _, _ = app.handle(
        method="POST",
        path="/api/device/actions",
        body=json.dumps(
            {
                "device_id": "device-1",
                "control_id": "power",
                "value": True,
            }
        ).encode("utf-8"),
    )

    assert status == 200

    assert events == [
        "execute",
        "refresh",
    ]


def test_device_action_api_rejects_control_when_upstream_power_is_off():
    from src.smartscreen_platform.device_data import (
        DeviceDefinition,
        DeviceParameterDefinition,
        DeviceParameterStore,
        DevicePowerDependencyResolver,
        DeviceRegistry,
    )

    upstream = DeviceDefinition(
        device_id="dining.light_power_1",
        name="餐灯物理电源",
        location_id="dining",
        adapter_id="home_assistant",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id="light.dining_power",
                value_type="bool",
            ),
        },
    )

    child = DeviceDefinition(
        device_id="dining.table_light_east",
        name="餐桌灯东",
        location_id="dining",
        adapter_id="home_assistant",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id="light.table_light_east",
                value_type="bool",
            ),
        },
        power_source_device_id=(
            "dining.light_power_1"
        ),
    )

    registry = DeviceRegistry(
        devices=[
            upstream,
            child,
        ]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="dining.light_power_1",
        parameter="power",
        value=False,
        available=True,
    )

    # Deliberately preserve a stale-but-available
    # downstream state. Physical upstream OFF must
    # still take precedence.
    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value=True,
        available=True,
    )

    resolver = DevicePowerDependencyResolver(
        registry=registry,
        store=store,
    )

    dispatcher = FakeDeviceControlDispatcher()

    app = SnapshotApplication(
        FakeHost(),
        device_control_dispatcher=dispatcher,
        device_power_dependency_resolver=resolver,
    )

    status, _, body = app.handle(
        method="POST",
        path="/api/device/actions",
        body=json.dumps(
            {
                "device_id": (
                    "dining.table_light_east"
                ),
                "control_id": "power",
                "value": False,
            }
        ).encode("utf-8"),
    )

    assert status == 403

    assert json.loads(
        body.decode("utf-8")
    ) == {
        "error": "powered_off_by_upstream",
    }

    assert dispatcher.calls == []
