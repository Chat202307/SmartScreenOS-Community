import pytest

from src.smartscreen_display.xingoo_device_data import (
    XingooDeviceDataAdapter,
)
from src.smartscreen_platform.device_data import (
    DeviceDataIngestionService,
    DeviceDefinition,
    DeviceParameterDefinition,
    DeviceParameterStore,
    DeviceRegistry,
)


IOT_ID = (
    "enVCpNrvUesXVopdNvTD000000"
)


def make_registry():
    return DeviceRegistry(
        devices=[
            DeviceDefinition(
                device_id=(
                    "xingoo_test_device_1"
                ),
                name="IAM消毒空气净化器",
                location_id=(
                    "open_public_area"
                ),
                adapter_id="xingoo",
                parameters={
                    "temperature": (
                        DeviceParameterDefinition(
                            parameter=(
                                "temperature"
                            ),
                            source_id=(
                                IOT_ID
                                + ":"
                                + "CurrentTemperature"
                            ),
                            value_type="float",
                            unit="degC",
                        )
                    ),
                    "humidity": (
                        DeviceParameterDefinition(
                            parameter=(
                                "humidity"
                            ),
                            source_id=(
                                IOT_ID
                                + ":"
                                + "CurrentHumidity"
                            ),
                            value_type="float",
                            unit="percent",
                        )
                    ),
                    "pm25": (
                        DeviceParameterDefinition(
                            parameter="pm25",
                            source_id=(
                                IOT_ID
                                + ":PM25"
                            ),
                            value_type="float",
                        )
                    ),
                    "hcho": (
                        DeviceParameterDefinition(
                            parameter="hcho",
                            source_id=(
                                IOT_ID
                                + ":HCHO"
                            ),
                            value_type="float",
                        )
                    ),
                    "power": (
                        DeviceParameterDefinition(
                            parameter="power",
                            source_id=(
                                IOT_ID
                                + ":PowerSwitch"
                            ),
                            value_type="bool",
                        )
                    ),
                    "mode": (
                        DeviceParameterDefinition(
                            parameter="mode",
                            source_id=(
                                IOT_ID
                                + ":WorkMode"
                            ),
                            value_type="int",
                        )
                    ),
                    "wind_speed": (
                        DeviceParameterDefinition(
                            parameter="wind_speed",
                            source_id=(
                                IOT_ID
                                + ":WindSpeed"
                            ),
                            value_type="int",
                        )
                    ),
                    "ions": (
                        DeviceParameterDefinition(
                            parameter="ions",
                            source_id=(
                                IOT_ID
                                + ":IonsSwitch"
                            ),
                            value_type="bool",
                        )
                    ),
                    "disinfection": (
                        DeviceParameterDefinition(
                            parameter="disinfection",
                            source_id=(
                                IOT_ID
                                + ":DisinfectSwitch"
                            ),
                            value_type="bool",
                        )
                    ),
                    "screen_on": (
                        DeviceParameterDefinition(
                            parameter="screen_on",
                            source_id=(
                                IOT_ID
                                + ":ScreenSwitch"
                            ),
                            value_type="bool",
                        )
                    ),
                    "child_lock": (
                        DeviceParameterDefinition(
                            parameter="child_lock",
                            source_id=(
                                IOT_ID
                                + ":ChildLockSwitch"
                            ),
                            value_type="bool",
                        )
                    ),
                },
            )
        ]
    )


def make_adapter():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    ingestion = (
        DeviceDataIngestionService(
            registry=registry,
            store=store,
        )
    )

    adapter = (
        XingooDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        )
    )

    return adapter, store


def test_adapter_builds_stable_source_id():
    assert (
        XingooDeviceDataAdapter
        .make_source_id(
            IOT_ID,
            "PM25",
        )
        == IOT_ID + ":PM25"
    )


def test_adapter_ingests_supported_properties():
    adapter, store = (
        make_adapter()
    )

    observations = (
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties={
                "CurrentTemperature": 28,
                "CurrentHumidity": 74,
                "PM25": 33,
                "HCHO": 0.02,
            },
        )
    )

    by_parameter = {
        observation.parameter:
        observation
        for observation
        in observations
    }

    assert set(
        by_parameter
    ) == {
        "temperature",
        "humidity",
        "pm25",
        "hcho",
    }

    assert (
        by_parameter[
            "temperature"
        ].value
        == 28.0
    )

    assert (
        by_parameter[
            "humidity"
        ].value
        == 74.0
    )

    assert (
        by_parameter[
            "pm25"
        ].value
        == 33.0
    )

    assert (
        by_parameter[
            "hcho"
        ].value
        == 0.02
    )

    assert (
        store.get(
            (
                "xingoo_test_device_1"
            ),
            "pm25",
        ).value
        == 33.0
    )


def test_adapter_ignores_unconfigured_properties():
    adapter, _ = (
        make_adapter()
    )

    observations = (
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties={
                "PM25": 33,
                "FilterReset": 0,
                "TimingOn": 0,
            },
        )
    )

    assert len(
        observations
    ) == 1

    assert (
        observations[0]
        .parameter
        == "pm25"
    )


def test_adapter_preserves_device_traceability():
    adapter, _ = (
        make_adapter()
    )

    observation = (
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties={
                "PM25": 33,
            },
        )[0]
    )

    payload = (
        observation.to_dict()
    )

    assert (
        "device_id"
        not in payload
    )

    assert (
        payload[
            "provenance"
        ][
            "device_id"
        ]
        == (
            "xingoo_test_device_1"
        )
    )

    assert (
        payload[
            "provenance"
        ][
            "adapter_id"
        ]
        == "xingoo"
    )

    assert (
        payload[
            "provenance"
        ][
            "source_id"
        ]
        == IOT_ID + ":PM25"
    )


def test_adapter_marks_unavailable_property():
    adapter, store = (
        make_adapter()
    )

    observation = (
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties={
                "PM25": (
                    "unavailable"
                ),
            },
        )[0]
    )

    assert (
        observation.quality
        == "unavailable"
    )

    entry = store.get(
        (
            "xingoo_test_device_1"
        ),
        "pm25",
    )

    assert (
        entry.available
        is False
    )


def test_adapter_rejects_invalid_properties_payload():
    adapter, _ = (
        make_adapter()
    )

    with pytest.raises(
        TypeError
    ):
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties=[],
        )



def test_adapter_ingests_control_state_properties():
    adapter, _ = make_adapter()

    observations = (
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties={
                "PowerSwitch": 1,
                "WorkMode": 2,
                "WindSpeed": 3,
                "IonsSwitch": 1,
                "DisinfectSwitch": 0,
                "ScreenSwitch": 0,
                "ChildLockSwitch": 1,
            },
        )
    )

    by_parameter = {
        item.parameter: item.value
        for item in observations
    }

    assert by_parameter == {
        "power": True,
        "mode": 2,
        "wind_speed": 3,
        "ions": True,
        "disinfection": False,
        "screen_on": True,
        "child_lock": True,
    }


def test_adapter_inverts_m8_screen_switch_semantics():
    adapter, _ = make_adapter()

    screen_on = (
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties={
                "ScreenSwitch": 0,
            },
        )[0]
    )

    screen_off = (
        adapter.ingest_properties(
            iot_id=IOT_ID,
            properties={
                "ScreenSwitch": 1,
            },
        )[0]
    )

    assert screen_on.parameter == "screen_on"
    assert screen_on.value is True

    assert screen_off.parameter == "screen_on"
    assert screen_off.value is False
