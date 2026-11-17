import json

from src.smartscreen_display.server import (
    SnapshotApplication,
)
from src.smartscreen_platform.device_control import (
    DeviceControlDefinition,
)
from src.smartscreen_platform.device_data import (
    DeviceDefinition,
    DeviceParameterDefinition,
)


class FakeHost:
    def snapshot(self):
        return {}


def make_devices():
    return [
        DeviceDefinition(
            device_id=(
                "xingoo_test_device_1"
            ),
            name="IAM消毒空气净化器",
            location_id="open_public_area",
            adapter_id="xingoo",
            parameters={
                "power": (
                    DeviceParameterDefinition(
                        parameter="power",
                        source_id=(
                            "iot-secret:"
                            "PowerSwitch"
                        ),
                        value_type="bool",
                    )
                ),
                "mode": (
                    DeviceParameterDefinition(
                        parameter="mode",
                        source_id=(
                            "iot-secret:"
                            "WorkMode"
                        ),
                        value_type="int",
                    )
                ),
            },
            controls={
                "power": (
                    DeviceControlDefinition(
                        control_id="power",
                        kind="boolean",
                        parameter="power",
                    )
                ),
                "mode": (
                    DeviceControlDefinition(
                        control_id="mode",
                        kind="select",
                        parameter="mode",
                        options=(
                            "smart",
                            "sleep",
                        ),
                    )
                ),
            },
            adapter_config={},
        ),
        DeviceDefinition(
            device_id="corridor.light_1",
            name="走廊灯",
            location_id="corridor",
            adapter_id="home_assistant",
            parameters={
                "power": (
                    DeviceParameterDefinition(
                        parameter="power",
                        source_id=(
                            "light."
                            "dnake_secret"
                        ),
                        value_type="bool",
                    )
                ),
            },
            controls={
                "power": (
                    DeviceControlDefinition(
                        control_id="power",
                        kind="boolean",
                        parameter="power",
                    )
                ),
                "brightness": (
                    DeviceControlDefinition(
                        control_id="brightness",
                        kind="number",
                        parameter="brightness",
                        minimum=0,
                        maximum=100,
                        step=1,
                    )
                ),
            },
            adapter_config={
                "entity_id": (
                    "light."
                    "dnake_secret"
                ),
            },
        ),
        DeviceDefinition(
            device_id="living.sensor_1",
            name="只读传感器",
            location_id="living",
            adapter_id="home_assistant",
            parameters={
                "temperature": (
                    DeviceParameterDefinition(
                        parameter=(
                            "temperature"
                        ),
                        source_id=(
                            "sensor."
                            "private_temperature"
                        ),
                        value_type="float",
                    )
                ),
            },
            controls={},
            adapter_config={},
        ),
    ]


def test_dashboard_api_exposes_generic_controllable_devices():
    app = SnapshotApplication(
        FakeHost(),
        device_definitions=make_devices(),
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200

    assert payload["devices"] == [
        {
            "device_id": (
                "xingoo_test_device_1"
            ),
            "name": (
                "IAM消毒空气净化器"
            ),
            "location_id": (
                "open_public_area"
            ),
            "controls": [
                {
                    "control_id": (
                        "power"
                    ),
                    "kind": (
                        "boolean"
                    ),
                    "parameter": (
                        "power"
                    ),
                    "options": [],
                },
                {
                    "control_id": (
                        "mode"
                    ),
                    "kind": (
                        "select"
                    ),
                    "parameter": (
                        "mode"
                    ),
                    "options": [
                        "smart",
                        "sleep",
                    ],
                },
            ],
        },
        {
            "device_id": (
                "corridor.light_1"
            ),
            "name": "走廊灯",
            "location_id": (
                "corridor"
            ),
            "controls": [
                {
                    "control_id": (
                        "power"
                    ),
                    "kind": (
                        "boolean"
                    ),
                    "parameter": (
                        "power"
                    ),
                    "options": [],
                },
                {
                    "control_id": (
                        "brightness"
                    ),
                    "kind": (
                        "number"
                    ),
                    "parameter": (
                        "brightness"
                    ),
                    "options": [],
                    "min": 0,
                    "max": 100,
                    "step": 1,
                },
            ],
        },
    ]


def test_dashboard_device_metadata_excludes_read_only_devices():
    app = SnapshotApplication(
        FakeHost(),
        device_definitions=make_devices(),
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    device_ids = {
        item["device_id"]
        for item in payload["devices"]
    }

    assert (
        "living.sensor_1"
        not in device_ids
    )


def test_dashboard_device_metadata_hides_adapter_protocol_details():
    app = SnapshotApplication(
        FakeHost(),
        device_definitions=make_devices(),
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    text = body.decode("utf-8")

    for private_value in (
        "adapter_id",
        "adapter_config",
        "source_id",
        "iot-secret",
        "dnake_secret",
        "home_assistant",
        '"xingoo"',
    ):
        assert (
            private_value
            not in text
        )



def make_power_dependent_devices():
    return [
        DeviceDefinition(
            device_id="dining.light_power_1",
            name="餐灯",
            location_id="dining",
            adapter_id="home_assistant",
            parameters={
                "power": (
                    DeviceParameterDefinition(
                        parameter="power",
                        source_id=(
                            "light."
                            "dnake_dining_power"
                        ),
                        value_type="bool",
                    )
                ),
            },
            controls={
                "power": (
                    DeviceControlDefinition(
                        control_id="power",
                        kind="boolean",
                        parameter="power",
                    )
                ),
            },
        ),
        DeviceDefinition(
            device_id="dining.table_light_east",
            name="餐桌灯东",
            location_id="dining",
            adapter_id="home_assistant",
            parameters={
                "power": (
                    DeviceParameterDefinition(
                        parameter="power",
                        source_id=(
                            "light."
                            "table_light_east"
                        ),
                        value_type="bool",
                    )
                ),
            },
            controls={
                "power": (
                    DeviceControlDefinition(
                        control_id="power",
                        kind="boolean",
                        parameter="power",
                    )
                ),
            },
            power_source_device_id=(
                "dining.light_power_1"
            ),
        ),
    ]


def test_dashboard_device_explains_upstream_power_off():
    from src.smartscreen_platform.device_data import (
        DeviceParameterStore,
        DeviceRegistry,
    )

    devices = make_power_dependent_devices()
    registry = DeviceRegistry(
        devices=devices
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
    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value=None,
        available=False,
    )

    from src.smartscreen_platform.device_data.power_dependency import (
        DevicePowerDependencyResolver,
    )

    resolver = DevicePowerDependencyResolver(
        registry=registry,
        store=store,
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=devices,
        device_power_dependency_resolver=resolver,
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    by_id = {
        item["device_id"]: item
        for item in payload["devices"]
    }

    assert (
        by_id[
            "dining.table_light_east"
        ]["availability_reason"]
        == "powered_off_by_upstream"
    )


def test_dashboard_device_does_not_mislabel_independent_unavailable_device():
    from src.smartscreen_platform.device_data import (
        DeviceParameterStore,
        DeviceRegistry,
    )

    devices = make_devices()
    registry = DeviceRegistry(
        devices=devices
    )
    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="corridor.light_1",
        parameter="power",
        value=None,
        available=False,
    )

    from src.smartscreen_platform.device_data.power_dependency import (
        DevicePowerDependencyResolver,
    )

    resolver = DevicePowerDependencyResolver(
        registry=registry,
        store=store,
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=devices,
        device_power_dependency_resolver=resolver,
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    by_id = {
        item["device_id"]: item
        for item in payload["devices"]
    }

    assert (
        by_id[
            "corridor.light_1"
        ].get("availability_reason")
        != "powered_off_by_upstream"
    )


def test_dashboard_api_exposes_device_parameter_state_separately_from_observations():
    from src.smartscreen_platform.device_data import (
        DeviceParameterStore,
        DeviceRegistry,
    )

    devices = make_power_dependent_devices()

    registry = DeviceRegistry(
        devices=devices
    )

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="dining.light_power_1",
        parameter="power",
        value=True,
        available=True,
    )

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value=False,
        available=True,
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=devices,
        device_parameter_store=store,
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert payload["device_states"] == [
        {
            "device_id": "dining.light_power_1",
            "parameter": "power",
            "value": True,
            "available": True,
        },
        {
            "device_id": "dining.table_light_east",
            "parameter": "power",
            "value": False,
            "available": True,
        },
    ]


def test_dashboard_device_states_keep_same_location_same_parameter_devices_distinct():
    from src.smartscreen_platform.device_data import (
        DeviceParameterStore,
        DeviceRegistry,
    )

    devices = [
        DeviceDefinition(
            device_id="dining.table_light_east",
            name="餐桌灯东",
            location_id="dining",
            adapter_id="home_assistant",
            parameters={
                "power": DeviceParameterDefinition(
                    parameter="power",
                    source_id="light.east",
                    value_type="bool",
                ),
            },
        ),
        DeviceDefinition(
            device_id="dining.table_light_west",
            name="餐桌灯西",
            location_id="dining",
            adapter_id="home_assistant",
            parameters={
                "power": DeviceParameterDefinition(
                    parameter="power",
                    source_id="light.west",
                    value_type="bool",
                ),
            },
        ),
    ]

    registry = DeviceRegistry(
        devices=devices
    )

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="dining.table_light_east",
        parameter="power",
        value=True,
        available=True,
    )

    store.update(
        device_id="dining.table_light_west",
        parameter="power",
        value=False,
        available=True,
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=devices,
        device_parameter_store=store,
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    states = {
        (
            item["device_id"],
            item["parameter"],
        ): item["value"]
        for item in payload["device_states"]
    }

    assert states == {
        (
            "dining.table_light_east",
            "power",
        ): True,
        (
            "dining.table_light_west",
            "power",
        ): False,
    }


def test_dashboard_api_exposes_optional_device_type():
    device = DeviceDefinition(
        device_id="air_purifier_001",
        device_type="air_purifier",
        name="空气净化器",
        location_id="living",
        adapter_id="xingoo",
        parameters={
            "power": (
                DeviceParameterDefinition(
                    parameter="power",
                    source_id=(
                        "device:PowerSwitch"
                    ),
                    value_type="bool",
                )
            ),
        },
        controls={
            "power": (
                DeviceControlDefinition(
                    control_id="power",
                    kind="boolean",
                    parameter="power",
                )
            ),
        },
        adapter_config={},
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=[
            device
        ],
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload["devices"] == [
        {
            "device_id": (
                "air_purifier_001"
            ),
            "device_type": (
                "air_purifier"
            ),
            "name": "空气净化器",
            "location_id": "living",
            "controls": [
                {
                    "control_id": (
                        "power"
                    ),
                    "kind": (
                        "boolean"
                    ),
                    "parameter": (
                        "power"
                    ),
                    "options": [],
                },
            ],
        }
    ]


def test_dashboard_device_exposes_optional_power_source_device_id():
    devices = make_power_dependent_devices()

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=devices,
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    by_id = {
        item["device_id"]: item
        for item in payload["devices"]
    }

    assert status == 200

    assert (
        by_id[
            "dining.table_light_east"
        ]["power_source_device_id"]
        == "dining.light_power_1"
    )

    assert (
        "power_source_device_id"
        not in by_id[
            "dining.light_power_1"
        ]
    )



def test_dashboard_device_exposes_optional_power_control_device_id():
    device = DeviceDefinition(
        device_id="room.smart_light_1",
        name="智能灯",
        location_id="room",
        adapter_id="home_assistant",
        parameters={
            "power": (
                DeviceParameterDefinition(
                    parameter="power",
                    source_id="light.smart_light",
                    value_type="bool",
                )
            ),
        },
        controls={
            "power": (
                DeviceControlDefinition(
                    control_id="power",
                    kind="boolean",
                    parameter="power",
                )
            ),
        },
        power_source_device_id=(
            "room.light_power_1"
        ),
        power_control_device_id=(
            "room.light_power_1"
        ),
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=[
            device,
        ],
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200

    assert payload["devices"][0][
        "power_control_device_id"
    ] == "room.light_power_1"


def test_dashboard_does_not_infer_power_control_from_power_source():
    devices = make_power_dependent_devices()

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=devices,
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    by_id = {
        item["device_id"]: item
        for item in payload["devices"]
    }

    assert status == 200

    assert (
        by_id[
            "dining.table_light_east"
        ]["power_source_device_id"]
        == "dining.light_power_1"
    )

    assert (
        "power_control_device_id"
        not in by_id[
            "dining.table_light_east"
        ]
    )



def test_dashboard_includes_area_readonly_device_without_controls():
    device = DeviceDefinition(
        device_id="room.door_1",
        name="门磁",
        location_id="room",
        adapter_id="home_assistant",
        parameters={},
        area_readonly=True,
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=[device],
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200

    assert payload["devices"] == [
        {
            "device_id": "room.door_1",
            "name": "门磁",
            "location_id": "room",
            "controls": [],
            "area_readonly": True,
        }
    ]


def test_dashboard_still_hides_plain_uncontrolled_sensor():
    device = DeviceDefinition(
        device_id="room.sensor_1",
        name="普通传感器",
        location_id="room",
        adapter_id="home_assistant",
        parameters={},
    )

    app = SnapshotApplication(
        FakeHost(),
        device_definitions=[device],
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert "devices" not in payload
