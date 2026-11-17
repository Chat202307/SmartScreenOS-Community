from types import SimpleNamespace

from src.smartscreen_display.dnake_mqtt_device_control_executor import (
    DnakeMqttDeviceControlExecutor,
)


class FakeMqttClient:
    def __init__(self):
        self.published = []

    def publish(
        self,
        topic,
        payload,
        *,
        retain=False,
    ):
        self.published.append(
            (
                topic,
                payload,
                retain,
            )
        )
        return "published"


def _binding():
    return SimpleNamespace(
        adapter_id="dnake_mqtt",
        device_id="living.curtain_1",
        control=SimpleNamespace(
            control_id="state",
        ),
    )


def _executor():
    client = FakeMqttClient()

    executor = (
        DnakeMqttDeviceControlExecutor(
            client=client,
            device_topics={
                "living.curtain_1": (
                    "dnake/curtain/"
                    "客厅窗帘/set"
                ),
            },
        )
    )

    return executor, client


def test_open_publishes_open_command():
    executor, client = _executor()

    result = executor.execute(
        binding=_binding(),
        value="open",
    )

    assert result == "published"
    assert client.published == [
        (
            "dnake/curtain/"
            "客厅窗帘/set",
            "OPEN",
            False,
        ),
    ]


def test_close_publishes_close_command():
    executor, client = _executor()

    executor.execute(
        binding=_binding(),
        value="closed",
    )

    assert client.published[-1][1] == "CLOSE"


def test_stop_publishes_stop_command():
    executor, client = _executor()

    executor.execute(
        binding=_binding(),
        value="stopped",
    )

    assert client.published[-1][1] == "STOP"


def test_does_not_publish_retained_commands():
    executor, client = _executor()

    executor.execute(
        binding=_binding(),
        value="open",
    )

    assert client.published[-1][2] is False


def _air_binding(control_id):
    return SimpleNamespace(
        adapter_id="dnake_mqtt",
        device_id="air_conditioner_001",
        control=SimpleNamespace(
            control_id=control_id,
        ),
    )


def _air_executor():
    client = FakeMqttClient()

    executor = (
        DnakeMqttDeviceControlExecutor(
            client=client,
            device_topics={},
            device_control_topics={
                "air_conditioner_001": {
                    "operating_state": (
                        "dnake/air/"
                        "客厅空调/mode/set"
                    ),
                    "target_temperature": (
                        "dnake/air/"
                        "客厅空调/temp/set"
                    ),
                    "fan_mode": (
                        "dnake/air/"
                        "客厅空调/fan/set"
                    ),
                },
            },
        )
    )

    return executor, client


def test_air_operating_state_publishes_mode_command():
    executor, client = _air_executor()

    result = executor.execute(
        binding=_air_binding(
            "operating_state"
        ),
        value="cool",
    )

    assert result == "published"

    assert client.published == [
        (
            "dnake/air/"
            "客厅空调/mode/set",
            "COOL",
            False,
        ),
    ]


def test_air_off_publishes_off_mode_command():
    executor, client = _air_executor()

    executor.execute(
        binding=_air_binding(
            "operating_state"
        ),
        value="off",
    )

    assert client.published == [
        (
            "dnake/air/"
            "客厅空调/mode/set",
            "OFF",
            False,
        ),
    ]


def test_air_target_temperature_uses_temperature_topic():
    executor, client = _air_executor()

    executor.execute(
        binding=_air_binding(
            "target_temperature"
        ),
        value="23",
    )

    assert client.published == [
        (
            "dnake/air/"
            "客厅空调/temp/set",
            "23",
            False,
        ),
    ]


def test_air_fan_mode_uses_fan_topic():
    executor, client = _air_executor()

    executor.execute(
        binding=_air_binding(
            "fan_mode"
        ),
        value="medium",
    )

    assert client.published == [
        (
            "dnake/air/"
            "客厅空调/fan/set",
            "MEDIUM",
            False,
        ),
    ]


def _light_binding():
    return SimpleNamespace(
        adapter_id="dnake_mqtt",
        device_id="living.light_strip_1",
        control=SimpleNamespace(
            control_id="power",
        ),
    )


def _light_executor():
    client = FakeMqttClient()

    executor = (
        DnakeMqttDeviceControlExecutor(
            client=client,
            device_topics={},
            device_control_topics={
                "living.light_strip_1": {
                    "power": (
                        "dnake/light/"
                        "客厅灯带/set"
                    ),
                },
            },
        )
    )

    return executor, client


def test_light_on_publishes_on_command():
    executor, client = _light_executor()

    result = executor.execute(
        binding=_light_binding(),
        value=True,
    )

    assert result == "published"
    assert client.published == [
        (
            "dnake/light/"
            "客厅灯带/set",
            "ON",
            False,
        ),
    ]


def test_light_off_publishes_off_command():
    executor, client = _light_executor()

    executor.execute(
        binding=_light_binding(),
        value=False,
    )

    assert client.published[-1] == (
        "dnake/light/"
        "客厅灯带/set",
        "OFF",
        False,
    )
