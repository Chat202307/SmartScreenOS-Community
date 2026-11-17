from src.smartscreen_display.home_status import (
    HomeAssistantHomeStatusProvider,
)


class FakeClient:
    def __init__(self, states):
        self.states = states
        self.requests = []

    def get_json(self, path):
        self.requests.append(path)
        return self.states


def test_home_assistant_provider_reads_entities():
    client = FakeClient(
        [
            {
                "entity_id": "binary_sensor.front_door",
                "state": "off",
                "attributes": {
                    "friendly_name": "门窗",
                },
            },
            {
                "entity_id": "binary_sensor.living_room_motion",
                "state": "off",
                "attributes": {
                    "friendly_name": "客厅人体",
                },
            },
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {
                    "friendly_name": "客厅灯",
                },
            },
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "binary_sensor.front_door",
                "states": {
                    "on": "已打开",
                    "off": "已关闭",
                },
            },
            {
                "entity_id": "binary_sensor.living_room_motion",
                "states": {
                    "on": "有人",
                    "off": "无人",
                },
            },
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            },
        ],
    )

    assert provider.get_items() == [
        {
            "name": "门窗",
            "state": "已关闭",
        },
        {
            "name": "客厅人体",
            "state": "无人",
        },
        {
            "name": "客厅灯",
            "state": "关闭",
        },
    ]


def test_home_assistant_provider_requests_states():
    client = FakeClient([])

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[],
    )

    provider.get_items()

    assert client.requests == [
        "/api/states",
    ]


def test_home_assistant_provider_ignores_unknown_entities():
    client = FakeClient(
        [
            {
                "entity_id": "sensor.temperature",
                "state": "24",
                "attributes": {
                    "friendly_name": "温度",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    assert provider.get_items() == []


def test_home_assistant_provider_falls_back_to_entity_id():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "light.living_room",
            "state": "开启",
        }
    ]


def test_home_assistant_provider_uses_raw_state_when_unmapped():
    client = FakeClient(
        [
            {
                "entity_id": "sensor.mode",
                "state": "eco",
                "attributes": {
                    "friendly_name": "模式",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "sensor.mode",
                "states": {},
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "模式",
            "state": "eco",
        }
    ]


def test_home_assistant_provider_maps_unknown_state():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "unknown",
                "attributes": {
                    "friendly_name": "客厅灯",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅灯",
            "state": "未知",
        }
    ]


def test_home_assistant_provider_maps_unavailable_state():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "unavailable",
                "attributes": {
                    "friendly_name": "客厅灯",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅灯",
            "state": "离线",
        }
    ]


def test_entity_state_mapping_overrides_default_semantics():
    client = FakeClient(
        [
            {
                "entity_id": "sensor.mode",
                "state": "unknown",
                "attributes": {
                    "friendly_name": "模式",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "sensor.mode",
                "states": {
                    "unknown": "待确认",
                },
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "模式",
            "state": "待确认",
        }
    ]


def test_provider_uses_configured_display_name():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {
                    "friendly_name": "DNAKE 本地设备 客厅主灯1",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "name": "客厅主灯",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅主灯",
            "state": "开启",
        }
    ]


def test_light_uses_default_state_semantics():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {
                    "friendly_name": "客厅灯",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅灯",
            "state": "开启",
        }
    ]


def test_contact_sensor_uses_contact_semantics():
    client = FakeClient(
        [
            {
                "entity_id": "binary_sensor.front_door",
                "state": "on",
                "attributes": {
                    "friendly_name": "入户门",
                    "device_class": "door",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "binary_sensor.front_door",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "入户门",
            "state": "已打开",
        }
    ]


def test_occupancy_sensor_uses_presence_semantics():
    client = FakeClient(
        [
            {
                "entity_id": "binary_sensor.living_room_presence",
                "state": "off",
                "attributes": {
                    "friendly_name": "客厅人体",
                    "device_class": "occupancy",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "binary_sensor.living_room_presence",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅人体",
            "state": "无人",
        }
    ]


def test_motion_sensor_uses_presence_semantics():
    client = FakeClient(
        [
            {
                "entity_id": "binary_sensor.motion",
                "state": "on",
                "attributes": {
                    "friendly_name": "移动检测",
                    "device_class": "motion",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "binary_sensor.motion",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "移动检测",
            "state": "有人",
        }
    ]


def test_cover_uses_default_state_semantics():
    client = FakeClient(
        [
            {
                "entity_id": "cover.living_room",
                "state": "closed",
                "attributes": {
                    "friendly_name": "客厅窗帘",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅窗帘",
            "state": "已关闭",
        }
    ]


def test_climate_uses_default_state_semantics():
    client = FakeClient(
        [
            {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "friendly_name": "客厅空调",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅空调",
            "state": "制冷",
        }
    ]


def test_entity_mapping_still_overrides_device_defaults():
    client = FakeClient(
        [
            {
                "entity_id": "light.special",
                "state": "on",
                "attributes": {
                    "friendly_name": "特殊灯",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.special",
                "states": {
                    "on": "工作中",
                },
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "特殊灯",
            "state": "工作中",
        }
    ]


def test_home_assistant_provider_includes_configured_icon():
    client = FakeClient(
        [
            {
                "entity_id": "binary_sensor.front_door",
                "state": "off",
                "attributes": {
                    "friendly_name": "入户门",
                    "device_class": "door",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "binary_sensor.front_door",
                "name": "幸福开门",
                "icon": "door",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "幸福开门",
            "state": "已关闭",
            "icon": "door",
        }
    ]


def test_home_assistant_provider_omits_icon_when_not_configured():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {
                    "friendly_name": "客厅灯",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "name": "客厅灯",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅灯",
            "state": "关闭",
        }
    ]


def test_home_assistant_provider_includes_configured_action():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {
                    "friendly_name": "客厅主灯",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "name": "客厅主灯",
                "action": "toggle",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅主灯",
            "state": "关闭",
            "action": "toggle",
            "entity_id": "light.living_room",
            "raw_state": "off",
        }
    ]


def test_home_assistant_provider_omits_action_when_not_configured():
    client = FakeClient(
        [
            {
                "entity_id": "binary_sensor.front_door",
                "state": "off",
                "attributes": {
                    "friendly_name": "幸福开门",
                    "device_class": "door",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "binary_sensor.front_door",
                "name": "幸福开门",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "幸福开门",
            "state": "已关闭",
        }
    ]


def test_home_assistant_provider_performs_configured_action():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                }
            )

            return {
                "ok": True,
            }

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "name": "客厅主灯",
                "action": "toggle",
            }
        ],
    )

    result = provider.perform_action(
        "light.living_room",
        "toggle",
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        {
            "domain": "light",
            "service": "toggle",
            "entity_id": "light.living_room",
        }
    ]


def test_home_assistant_provider_rejects_unconfigured_action():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                }
            )

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "name": "客厅主灯",
            }
        ],
    )

    try:
        provider.perform_action(
            "light.living_room",
            "toggle",
        )
    except ValueError as exc:
        assert str(exc) == "action not allowed"
    else:
        raise AssertionError(
            "Expected ValueError for unconfigured action"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_wrong_action():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                }
            )

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "name": "客厅主灯",
                "action": "toggle",
            }
        ],
    )

    try:
        provider.perform_action(
            "light.living_room",
            "turn_on",
        )
    except ValueError as exc:
        assert str(exc) == "action not allowed"
    else:
        raise AssertionError(
            "Expected ValueError for wrong action"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_unknown_entity():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                }
            )

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[],
    )

    try:
        provider.perform_action(
            "light.unknown",
            "toggle",
        )
    except ValueError as exc:
        assert str(exc) == "action not allowed"
    else:
        raise AssertionError(
            "Expected ValueError for unknown entity"
        )

    assert client.calls == []


def test_home_assistant_provider_performs_action_from_actions_list():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                }
            )

            return {
                "ok": True,
            }

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "actions": [
                    "turn_on",
                    "turn_off",
                ],
            }
        ],
    )

    result = provider.perform_action(
        "climate.living_room",
        "turn_on",
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        {
            "domain": "climate",
            "service": "turn_on",
            "entity_id": "climate.living_room",
        }
    ]


def test_home_assistant_provider_rejects_action_not_in_actions_list():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                }
            )

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "actions": [
                    "turn_on",
                    "turn_off",
                ],
            }
        ],
    )

    try:
        provider.perform_action(
            "climate.living_room",
            "toggle",
        )
    except ValueError as exc:
        assert str(exc) == "action not allowed"
    else:
        raise AssertionError(
            "Expected ValueError for unsupported action"
        )

    assert client.calls == []


def test_home_assistant_provider_includes_configured_actions():
    client = FakeClient(
        [
            {
                "entity_id": "climate.living_room",
                "state": "off",
                "attributes": {
                    "friendly_name": "客厅空调",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "actions": [
                    "turn_on",
                    "turn_off",
                ],
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅空调",
            "state": "关闭",
            "actions": [
                "turn_on",
                "turn_off",
            ],
            "entity_id": "climate.living_room",
            "raw_state": "off",
        }
    ]


def test_home_assistant_provider_includes_raw_state_for_actionable_entity():
    client = FakeClient(
        [
            {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "friendly_name": "客厅空调",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "actions": [
                    "turn_on",
                    "turn_off",
                ],
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅空调",
            "state": "制冷",
            "raw_state": "cool",
            "actions": [
                "turn_on",
                "turn_off",
            ],
            "entity_id": "climate.living_room",
        }
    ]


def test_home_assistant_provider_includes_climate_details():
    client = FakeClient(
        [
            {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "friendly_name": "客厅空调",
                    "current_temperature": 24,
                    "temperature": 23,
                    "fan_mode": "low",
                    "min_temp": 16,
                    "max_temp": 30,
                    "target_temp_step": 1.0,
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "actions": [
                    "turn_on",
                    "turn_off",
                ],
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅空调",
            "state": "制冷",
            "raw_state": "cool",
            "actions": [
                "turn_on",
                "turn_off",
            ],
            "entity_id": "climate.living_room",
            "current_temperature": 24,
            "temperature": 23,
            "fan_mode": "low",
            "min_temp": 16,
            "max_temp": 30,
            "target_temp_step": 1.0,
        }
    ]


def test_home_assistant_provider_omits_missing_climate_details():
    client = FakeClient(
        [
            {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "friendly_name": "客厅空调",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅空调",
            "state": "制冷",
        }
    ]


def test_home_assistant_provider_sets_temperature():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "temperature_control": True,
            }
        ],
    )

    result = provider.set_temperature(
        "climate.living_room",
        24,
        min_temp=16,
        max_temp=30,
        step=1,
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        {
            "domain": "climate",
            "service": "set_temperature",
            "entity_id": "climate.living_room",
            "service_data": {
                "temperature": 24,
            },
        }
    ]


def test_home_assistant_provider_rejects_temperature_control_when_not_configured():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
            }
        ],
    )

    try:
        provider.set_temperature(
            "climate.living_room",
            24,
            min_temp=16,
            max_temp=30,
            step=1,
        )
    except ValueError as exc:
        assert str(exc) == "temperature control not allowed"
    else:
        raise AssertionError(
            "Expected ValueError for disabled temperature control"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_temperature_out_of_range():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "temperature_control": True,
            }
        ],
    )

    try:
        provider.set_temperature(
            "climate.living_room",
            31,
            min_temp=16,
            max_temp=30,
            step=1,
        )
    except ValueError as exc:
        assert str(exc) == "temperature out of range"
    else:
        raise AssertionError(
            "Expected ValueError for out-of-range temperature"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_invalid_temperature_step():
    class ActionClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ActionClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "temperature_control": True,
            }
        ],
    )

    try:
        provider.set_temperature(
            "climate.living_room",
            23.5,
            min_temp=16,
            max_temp=30,
            step=1,
        )
    except ValueError as exc:
        assert str(exc) == "invalid temperature step"
    else:
        raise AssertionError(
            "Expected ValueError for invalid temperature step"
        )

    assert client.calls == []


def test_home_assistant_provider_uses_live_temperature_limits():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            assert path == (
                "/api/states/"
                "climate.living_room"
            )

            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "min_temp": 16,
                    "max_temp": 30,
                    "target_temp_step": 1.0,
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "temperature_control": True,
            }
        ],
    )

    result = provider.set_temperature(
        "climate.living_room",
        24,
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        {
            "domain": "climate",
            "service": "set_temperature",
            "entity_id": "climate.living_room",
            "service_data": {
                "temperature": 24,
            },
        }
    ]


def test_home_assistant_provider_rejects_temperature_above_live_max():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "min_temp": 16,
                    "max_temp": 30,
                    "target_temp_step": 1.0,
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "temperature_control": True,
            }
        ],
    )

    try:
        provider.set_temperature(
            "climate.living_room",
            31,
        )
    except ValueError as exc:
        assert str(exc) == "temperature out of range"
    else:
        raise AssertionError(
            "Expected ValueError for live max temperature"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_missing_temperature_limits():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "min_temp": 16,
                    # max_temp deliberately missing
                    "target_temp_step": 1.0,
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "temperature_control": True,
            }
        ],
    )

    try:
        provider.set_temperature(
            "climate.living_room",
            24,
        )
    except ValueError as exc:
        assert str(exc) == "temperature limits unavailable"
    else:
        raise AssertionError(
            "Expected ValueError for missing temperature limits"
        )

    assert client.calls == []


def test_home_assistant_provider_sets_supported_fan_mode():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            assert path == (
                "/api/states/"
                "climate.living_room"
            )

            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "fan_modes": [
                        "low",
                        "medium",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "fan_control": True,
            }
        ],
    )

    result = provider.set_fan_mode(
        "climate.living_room",
        "medium",
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        {
            "domain": "climate",
            "service": "set_fan_mode",
            "entity_id": "climate.living_room",
            "service_data": {
                "fan_mode": "medium",
            },
        }
    ]


def test_home_assistant_provider_sets_low_fan_mode():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "fan_modes": [
                        "low",
                        "medium",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "fan_control": True,
            }
        ],
    )

    provider.set_fan_mode(
        "climate.living_room",
        "low",
    )

    assert client.calls == [
        {
            "domain": "climate",
            "service": "set_fan_mode",
            "entity_id": "climate.living_room",
            "service_data": {
                "fan_mode": "low",
            },
        }
    ]


def test_home_assistant_provider_rejects_unsupported_fan_mode():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "fan_modes": [
                        "low",
                        "medium",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "fan_control": True,
            }
        ],
    )

    try:
        provider.set_fan_mode(
            "climate.living_room",
            "turbo",
        )
    except ValueError as exc:
        assert str(exc) == "fan mode not supported"
    else:
        raise AssertionError(
            "Expected ValueError for unsupported fan mode"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_fan_control_when_not_configured():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "fan_modes": [
                        "low",
                        "medium",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
            }
        ],
    )

    try:
        provider.set_fan_mode(
            "climate.living_room",
            "medium",
        )
    except ValueError as exc:
        assert str(exc) == "fan control not allowed"
    else:
        raise AssertionError(
            "Expected ValueError for disabled fan control"
        )

    assert client.calls == []


def test_home_assistant_provider_sets_supported_hvac_mode():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            assert path == (
                "/api/states/"
                "climate.living_room"
            )

            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "hvac_modes": [
                        "off",
                        "cool",
                        "heat",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "name": "客厅空调",
                "hvac_mode_control": True,
            }
        ],
    )

    result = provider.set_hvac_mode(
        "climate.living_room",
        "heat",
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        {
            "domain": "climate",
            "service": "set_hvac_mode",
            "entity_id": "climate.living_room",
            "service_data": {
                "hvac_mode": "heat",
            },
        }
    ]


def test_home_assistant_provider_sets_cool_hvac_mode():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "heat",
                "attributes": {
                    "hvac_modes": [
                        "off",
                        "cool",
                        "heat",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "hvac_mode_control": True,
            }
        ],
    )

    provider.set_hvac_mode(
        "climate.living_room",
        "cool",
    )

    assert client.calls[0]["service_data"] == {
        "hvac_mode": "cool",
    }


def test_home_assistant_provider_rejects_unsupported_hvac_mode():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "hvac_modes": [
                        "off",
                        "cool",
                        "heat",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
                "hvac_mode_control": True,
            }
        ],
    )

    try:
        provider.set_hvac_mode(
            "climate.living_room",
            "auto",
        )
    except ValueError as error:
        assert str(error) == (
            "hvac mode not supported"
        )
    else:
        raise AssertionError(
            "ValueError was not raised"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_hvac_mode_control_when_not_configured():
    class ClimateClient:
        def __init__(self):
            self.calls = []

        def get_json(self, path):
            return {
                "entity_id": "climate.living_room",
                "state": "cool",
                "attributes": {
                    "hvac_modes": [
                        "off",
                        "cool",
                        "heat",
                    ],
                },
            }

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = ClimateClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "climate.living_room",
            }
        ],
    )

    try:
        provider.set_hvac_mode(
            "climate.living_room",
            "heat",
        )
    except ValueError as error:
        assert str(error) == (
            "hvac mode control not allowed"
        )
    else:
        raise AssertionError(
            "ValueError was not raised"
        )

    assert client.calls == []


def test_home_assistant_provider_opens_cover():
    class CoverClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = CoverClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
                "cover_control": True,
            }
        ],
    )

    result = provider.perform_cover_action(
        "cover.living_room",
        "open",
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        {
            "domain": "cover",
            "service": "open_cover",
            "entity_id": "cover.living_room",
            "service_data": None,
        }
    ]


def test_home_assistant_provider_stops_cover():
    class CoverClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = CoverClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
                "cover_control": True,
            }
        ],
    )

    provider.perform_cover_action(
        "cover.living_room",
        "stop",
    )

    assert client.calls[0]["service"] == "stop_cover"


def test_home_assistant_provider_closes_cover():
    class CoverClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

            return {
                "ok": True,
            }

    client = CoverClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
                "cover_control": True,
            }
        ],
    )

    provider.perform_cover_action(
        "cover.living_room",
        "close",
    )

    assert client.calls[0]["service"] == "close_cover"


def test_home_assistant_provider_rejects_unknown_cover_action():
    class CoverClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = CoverClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
                "cover_control": True,
            }
        ],
    )

    try:
        provider.perform_cover_action(
            "cover.living_room",
            "toggle",
        )
    except ValueError as exc:
        assert str(exc) == "cover action not supported"
    else:
        raise AssertionError(
            "Expected ValueError for unsupported cover action"
        )

    assert client.calls == []


def test_home_assistant_provider_rejects_cover_control_when_not_configured():
    class CoverClient:
        def __init__(self):
            self.calls = []

        def call_service(
            self,
            domain,
            service,
            entity_id,
            *,
            service_data=None,
        ):
            self.calls.append(
                {
                    "domain": domain,
                    "service": service,
                    "entity_id": entity_id,
                    "service_data": service_data,
                }
            )

    client = CoverClient()

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
            }
        ],
    )

    try:
        provider.perform_cover_action(
            "cover.living_room",
            "open",
        )
    except ValueError as exc:
        assert str(exc) == "cover control not allowed"
    else:
        raise AssertionError(
            "Expected ValueError for disabled cover control"
        )

    assert client.calls == []


def test_home_assistant_provider_includes_cover_control_metadata():
    client = FakeClient(
        [
            {
                "entity_id": "cover.living_room",
                "state": "unknown",
                "attributes": {
                    "friendly_name": "客厅窗帘",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
                "name": "客厅窗帘",
                "cover_control": True,
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅窗帘",
            "state": "未知",
            "cover_control": True,
            "entity_id": "cover.living_room",
            "raw_state": "unknown",
        }
    ]


def test_home_assistant_provider_omits_cover_control_when_disabled():
    client = FakeClient(
        [
            {
                "entity_id": "cover.living_room",
                "state": "unknown",
                "attributes": {
                    "friendly_name": "客厅窗帘",
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.living_room",
                "name": "客厅窗帘",
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "客厅窗帘",
            "state": "未知",
        }
    ]


def test_home_assistant_provider_includes_cover_position():
    client = FakeClient(
        [
            {
                "entity_id": "cover.xiaomi_curtain",
                "state": "open",
                "attributes": {
                    "friendly_name": "小米窗帘",
                    "current_position": 72,
                    "supported_features": 15,
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.xiaomi_curtain",
                "name": "小米窗帘",
                "cover_control": True,
            }
        ],
    )

    assert provider.get_items() == [
        {
            "name": "小米窗帘",
            "state": "已打开",
            "cover_control": True,
            "entity_id": "cover.xiaomi_curtain",
            "raw_state": "open",
            "position": 72,
        }
    ]


def test_home_assistant_provider_omits_missing_cover_position():
    client = FakeClient(
        [
            {
                "entity_id": "cover.dnake_curtain",
                "state": "unknown",
                "attributes": {
                    "friendly_name": "DNAKE窗帘",
                    "is_closed": None,
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.dnake_curtain",
                "name": "DNAKE窗帘",
                "cover_control": True,
            }
        ],
    )

    item = provider.get_items()[0]

    assert "position" not in item


def test_home_assistant_provider_omits_invalid_cover_position():
    client = FakeClient(
        [
            {
                "entity_id": "cover.test_curtain",
                "state": "open",
                "attributes": {
                    "friendly_name": "测试窗帘",
                    "current_position": 101,
                },
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "cover.test_curtain",
                "name": "测试窗帘",
                "cover_control": True,
            }
        ],
    )

    item = provider.get_items()[0]

    assert "position" not in item


def test_home_assistant_provider_refreshes_state_cache():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    assert client.requests == [
        "/api/states",
    ]


def test_home_assistant_provider_can_read_cached_items():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()
    client.requests.clear()

    assert provider.get_cached_items() == [
        {
            "name": "light.living_room",
            "state": "开启",
        }
    ]

    assert client.requests == []


def test_home_assistant_provider_refresh_replaces_cached_state():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    client.states = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {},
        }
    ]

    provider.refresh()

    assert provider.get_cached_items() == [
        {
            "name": "light.living_room",
            "state": "开启",
        }
    ]


def test_home_assistant_provider_updates_cached_entity_state():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()
    client.requests.clear()

    provider.update_state(
        "light.living_room",
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {},
        },
    )

    assert provider.get_cached_items() == [
        {
            "name": "light.living_room",
            "state": "开启",
        }
    ]

    assert client.requests == []


def test_home_assistant_provider_update_preserves_other_cached_states():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {},
            },
            {
                "entity_id": "binary_sensor.front_door",
                "state": "off",
                "attributes": {},
            },
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            },
            {
                "entity_id": "binary_sensor.front_door",
                "states": {
                    "on": "已打开",
                    "off": "已关闭",
                },
            },
        ],
    )

    provider.refresh()

    provider.update_state(
        "light.living_room",
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {},
        },
    )

    assert provider.get_cached_items() == [
        {
            "name": "light.living_room",
            "state": "开启",
        },
        {
            "name": "binary_sensor.front_door",
            "state": "已关闭",
        },
    ]


def test_home_assistant_provider_removes_cached_entity():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    provider.update_state(
        "light.living_room",
        None,
    )

    assert provider.get_cached_items() == []


def test_home_assistant_provider_rejects_mismatched_updated_state():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    try:
        provider.update_state(
            "light.living_room",
            {
                "entity_id": "light.bedroom",
                "state": "on",
                "attributes": {},
            },
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "mismatched entity state was accepted"
        )

    assert provider.get_cached_items() == [
        {
            "name": "light.living_room",
            "state": "关闭",
        }
    ]


def test_home_assistant_provider_revision_changes_on_state_update():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    initial_revision = provider.revision

    provider.update_state(
        "light.living_room",
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {},
        },
    )

    assert provider.revision == initial_revision + 1


def test_home_assistant_provider_revision_unchanged_on_mismatched_update():
    client = FakeClient([])

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[],
    )

    initial_revision = provider.revision

    try:
        provider.update_state(
            "light.living_room",
            {
                "entity_id": "light.bedroom",
                "state": "on",
                "attributes": {},
            },
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "mismatched entity state was accepted"
        )

    assert provider.revision == initial_revision


def test_home_assistant_provider_revision_changes_when_entity_removed():
    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    initial_revision = provider.revision

    provider.update_state(
        "light.living_room",
        None,
    )

    assert provider.revision == initial_revision + 1


def test_home_assistant_provider_revision_unchanged_for_identical_state():
    state = {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {},
    }

    client = FakeClient(
        [state]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    initial_revision = provider.revision

    provider.update_state(
        "light.living_room",
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {},
        },
    )

    assert provider.revision == initial_revision


def test_home_assistant_provider_notifies_on_state_change():
    class FakeNotifier:
        def __init__(self):
            self.revisions = []

        def notify(self, revision):
            self.revisions.append(revision)

    notifier = FakeNotifier()

    state = {
        "entity_id": "light.living_room",
        "state": "off",
        "attributes": {},
    }

    client = FakeClient([state])

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[],
        change_notifier=notifier,
    )

    provider.refresh()

    provider.update_state(
        "light.living_room",
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {},
        },
    )

    assert notifier.revisions == [
        provider.revision,
    ]


def test_home_assistant_provider_does_not_notify_identical_state():
    class FakeNotifier:
        def __init__(self):
            self.revisions = []

        def notify(self, revision):
            self.revisions.append(revision)

    notifier = FakeNotifier()

    state = {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {},
    }

    client = FakeClient([state])

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[],
        change_notifier=notifier,
    )

    provider.refresh()

    provider.update_state(
        "light.living_room",
        dict(state),
    )

    assert notifier.revisions == []


def test_home_assistant_provider_notifies_when_entity_removed():
    class FakeNotifier:
        def __init__(self):
            self.revisions = []

        def notify(self, revision):
            self.revisions.append(revision)

    notifier = FakeNotifier()

    client = FakeClient(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[],
        change_notifier=notifier,
    )

    provider.refresh()

    provider.update_state(
        "light.living_room",
        None,
    )

    assert notifier.revisions == [
        provider.revision,
    ]


class SequencedHomeAssistantClient:
    def __init__(self, results):
        self._results = list(results)
        self.requests = []

    def get_json(self, path):
        self.requests.append(path)

        if not self._results:
            raise AssertionError(
                "unexpected Home Assistant request"
            )

        result = self._results.pop(0)

        if isinstance(result, BaseException):
            raise result

        return result


def test_home_assistant_provider_reports_available_after_successful_refresh():
    client = SequencedHomeAssistantClient(
        [
            [
                {
                    "entity_id": "light.living_room",
                    "state": "off",
                    "attributes": {
                        "friendly_name": "客厅灯",
                    },
                }
            ]
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
            }
        ],
    )

    assert provider.available is False

    assert provider.get_items() == [
        {
            "name": "客厅灯",
            "state": "关闭",
        }
    ]

    assert provider.available is True


def test_home_assistant_provider_preserves_cached_items_when_refresh_fails():
    client = SequencedHomeAssistantClient(
        [
            [
                {
                    "entity_id": "light.living_room",
                    "state": "on",
                    "attributes": {
                        "friendly_name": "客厅灯",
                    },
                }
            ],
            OSError(
                "Home Assistant unavailable"
            ),
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
            }
        ],
    )

    expected = [
        {
            "name": "客厅灯",
            "state": "开启",
        }
    ]

    assert provider.get_items() == expected
    assert provider.available is True

    assert provider.get_items() == expected
    assert provider.available is False


def test_home_assistant_provider_returns_empty_items_when_initial_refresh_fails():
    client = SequencedHomeAssistantClient(
        [
            OSError(
                "Home Assistant unavailable"
            ),
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
            }
        ],
    )

    assert provider.get_items() == []
    assert provider.available is False


def test_home_assistant_provider_recovers_after_refresh_failure():
    client = SequencedHomeAssistantClient(
        [
            OSError(
                "Home Assistant unavailable"
            ),
            [
                {
                    "entity_id": "light.living_room",
                    "state": "on",
                    "attributes": {
                        "friendly_name": "客厅灯",
                    },
                }
            ],
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
            }
        ],
    )

    assert provider.get_items() == []
    assert provider.available is False

    assert provider.get_items() == [
        {
            "name": "客厅灯",
            "state": "开启",
        }
    ]

    assert provider.available is True
