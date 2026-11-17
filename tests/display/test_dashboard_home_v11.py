from pathlib import Path

from src.smartscreen_display.dashboard import (
    DASHBOARD_HTML,
)


STATIC_DIR = Path(
    "src/smartscreen_display/static"
)


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_css():
    return (
        STATIC_DIR / "dashboard.css"
    ).read_text(encoding="utf-8")


def test_home_has_overview_cards():
    html = dashboard_html()

    assert 'id="today-card"' in html
    assert 'id="today-summary"' in html

    assert 'id="todo-card"' in html
    assert 'id="todo-list"' in html

    assert 'id="reminder-card"' in html
    assert 'id="reminder-list"' in html

    assert 'id="family-summary"' not in html
    assert 'id="family-summary-primary"' not in html
    assert 'id="family-summary-attention"' not in html

def test_home_has_household_actions():
    html = dashboard_html()

    assert 'id="household-actions"' in html

    for action_id in (
        "away",
        "night",
        "all_lights_off",
        "more",
    ):
        assert (
            'data-household-action="'
            + action_id
            + '"'
        ) in html


def test_home_has_area_section():
    html = dashboard_html()

    assert 'id="area-overview"' in html


def test_home_exposes_dynamic_area_overview_container():
    html = dashboard_html()

    assert 'id="area-overview"' in html

    for location_id in (
        "open_public_area",
        "master_bedroom",
        "study",
        "princess_room",
        "master_bath",
        "guest_bath",
        "corridor",
    ):
        assert (
            'data-location-id="'
            + location_id
            + '"'
        ) not in html


def test_area_cards_are_not_device_specific():
    html = dashboard_html()

    start = html.index(
        'id="area-overview"'
    )

    section = html[start:]

    assert "adapter_id" not in section
    assert "source_id" not in section


def test_home_keeps_existing_dashboard_content_contract():
    html = dashboard_html()

    assert 'id="dashboard-content"' in html
    assert 'id="todo-card"' in html
    assert 'id="home-status-card"' in html


def test_home_keeps_photo_compatibility_contract():
    html = dashboard_html()

    assert 'id="photo-card"' in html
    assert 'id="photo-image"' in html


def test_home_has_v11_layout_styles():
    css = dashboard_css()

    for selector in (
        ".home-summary",
        ".family-summary",
        ".household-actions",
        ".area-overview",
        ".area-card",
    ):
        assert selector in css


def test_v11_area_layout_has_tablet_adaptation():
    css = dashboard_css()

    assert "@media" in css
    assert "max-width: 1024px" in css
    assert ".area-overview" in css


def test_v11_area_layout_has_compact_adaptation():
    css = dashboard_css()

    assert "max-width: 768px" in css
    assert ".area-overview" in css


def dashboard_script():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def test_v11_home_renders_area_summary_from_semantic_cards():
    script = dashboard_script()

    assert "renderAreaOverview" in script
    assert "cards" in script
    assert "locations" in script


def test_v11_area_summary_uses_platform_semantics():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    for target in (
        '"occupancy"',
        '"lighting"',
        '"comfort"',
    ):
        assert target in section

    assert "observations" not in section


def test_v11_area_summary_updates_existing_area_cards():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "data-location-id" in section
    assert "area-card-state" in section


def test_v11_dashboard_update_calls_area_renderer():
    script = dashboard_script()

    start = script.index(
        "function updateSemanticDashboard"
    )

    section = script[start:start + 1800]

    assert "renderAreaOverview(" in section


def test_v11_home_hides_legacy_photo_card():
    css = dashboard_css()

    assert "#photo-card" in css
    assert "display: none" in css


def test_v11_home_hides_legacy_home_status_card():
    css = dashboard_css()

    assert "#home-status-card" in css
    assert "display: none" in css


def test_v11_home_renders_family_summary_from_cards():
    script = dashboard_script()

    assert "renderFamilySummary" in script


def test_v11_family_summary_does_not_infer_household_occupancy():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function renderAreaOverview",
        start,
    )
    section = script[start:end]

    assert "当前无人" not in section
    assert "当前有人" not in section


def test_v11_dashboard_update_calls_family_summary():
    script = dashboard_script()

    start = script.index(
        "function updateSemanticDashboard"
    )
    section = script[start:start + 2200]

    assert "renderFamilySummary(" in section


def test_v11_home_contains_area_sheet():
    html = dashboard_html()

    assert 'id="area-sheet"' in html
    assert 'id="area-sheet-title"' in html
    assert 'id="area-sheet-content"' in html
    assert 'data-area-sheet-close' in html


def test_v11_area_sheet_has_styles():
    css = dashboard_css()

    assert ".area-sheet" in css
    assert ".area-sheet-backdrop" in css
    assert ".area-sheet-panel" in css
    assert ".area-sheet-device" in css


def test_v11_area_sheet_resolves_zone_members_from_payload():
    script = dashboard_script()

    assert "resolveAreaLocationIds" in script

    start = script.index(
        "function resolveAreaLocationIds"
    )
    end = script.index(
        "function renderAreaSheet",
        start,
    )
    section = script[start:end]

    assert "zone_id" in section
    assert "room_ids" in section

    # The UI must consume the formal zone relation,
    # not hard-code the current home's room members.
    assert '"living"' not in section
    assert '"dining"' not in section
    assert '"kitchen"' not in section


def test_v11_area_sheet_scope_includes_zone_itself():
    script = dashboard_script()

    start = script.index(
        "function resolveAreaLocationIds"
    )
    end = script.index(
        "function renderAreaSheet",
        start,
    )
    section = script[start:end]

    assert "locationId" in section
    assert "room_ids" in section


def test_v11_area_sheet_filters_devices_by_location():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "devices" in section
    assert "device.location_id" in section
    assert "resolveAreaLocationIds" in section


def test_v11_area_cards_open_area_sheet():
    script = dashboard_script()

    assert "function bindAreaOverview" in script

    start = script.index(
        "function bindAreaOverview"
    )
    section = script[start:start + 1800]

    assert "data-location-id" in section
    assert "renderAreaSheet(" in section


def test_v11_dashboard_update_preserves_area_payload():
    script = dashboard_script()

    start = script.index(
        "function updateSemanticDashboard"
    )
    section = script[start:start + 2500]

    assert "payload.zones" in section
    assert "payload.devices" in section


def test_v11_area_sheet_uses_device_names_not_adapter_details():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "device.name" in section
    assert "adapter_id" not in section
    assert "source_id" not in section


def test_v11_area_sheet_renders_boolean_controls():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "device.controls" in section
    assert 'control.kind === "boolean"' in section
    assert "data-device-control" in section
    assert "data-control-value" in section


def test_v11_area_sheet_uses_device_states_for_boolean_state():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "deviceStates" in section
    assert "state.parameter" in section
    assert "device-control-active" in section


def test_v11_area_sheet_skips_complex_air_purifier_controls():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert '"air_purifier"' in section
    assert "device.device_type" in section


def test_v11_area_sheet_sends_controls_through_existing_dispatch():
    script = dashboard_script()

    start = script.index(
        "function bindAreaOverview"
    )
    end = script.index(
        "function renderAreaOverview",
        start,
    )
    section = script[start:end]

    assert "data-device-control" in section
    assert "sendDeviceControl(" in section


def test_v11_area_sheet_update_passes_device_states():
    script = dashboard_script()

    start = script.index(
        "function updateSemanticDashboard"
    )
    section = script[start:start + 2800]

    assert "deviceStates" in section
    assert "renderAreaSheet(" in section


def test_v11_area_sheet_renders_number_controls():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert 'control.kind === "number"' in section
    assert "numberStateAvailable" in section
    assert 'data-control-delta="' in section
    assert '"状态未知"' in section


def test_v11_area_sheet_uses_number_control_metadata():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "control.min" in section
    assert "control.max" in section
    assert "control.step" in section
    assert '"brightness"' in section
    assert '"color_temperature"' in section
    assert "numberIncrement = 5" in section
    assert "numberIncrement = 100" in section


def test_v11_area_sheet_number_click_uses_existing_dispatch():
    script = dashboard_script()

    start = script.index(
        "function bindAreaOverview"
    )
    end = script.index(
        "function renderAreaOverview",
        start,
    )
    section = script[start:end]

    assert "data-control-delta" in section
    assert "parseFloat(" in section
    assert "Math.max(" in section
    assert "Math.min(" in section
    assert "sendDeviceControl(" in section


def test_v11_area_sheet_renders_select_controls():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert 'control.kind === "select"' in section
    assert "control.options || []" in section
    assert "data-control-value" in section


def test_v11_area_sheet_select_uses_confirmed_state():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "String(" in section
    assert "device-control-active" in section


def test_v11_area_sheet_uses_ten_percent_curtain_position_increment():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert (
        'control.control_id'
        '\n            === "position"'
        in section
    )
    assert "numberIncrement = 10" in section


def test_v11_area_sheet_uses_user_friendly_control_labels():
    script = dashboard_script()

    assert "function deviceControlLabel" in script

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )

    section = script[start:end]

    assert "deviceControlLabel(" in section


def test_v11_area_sheet_uses_user_friendly_option_labels():
    script = dashboard_script()

    assert (
        "function deviceControlOptionLabel"
        in script
    )

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )

    section = script[start:end]

    assert (
        "deviceControlOptionLabel("
        in section
    )


def test_v11_area_sheet_number_controls_show_semantic_units():
    script = dashboard_script()

    assert (
        "function deviceControlNumberUnit"
        in script
    )

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )

    section = script[start:end]

    assert (
        "deviceControlNumberUnit("
        in section
    )


def test_v11_area_sheet_keeps_canonical_control_id_in_data_attribute():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert (
        "deviceControlLabel("
        in section
    )

    assert (
        '''' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            )'''
        in section
    )


def test_v11_area_sheet_keeps_canonical_control_id_in_data_attribute():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert (
        "deviceControlLabel("
        in section
    )

    assert (
        '''' data-device-control="' +
            escapeHtml(
              control.control_id || ""
            )'''
        in section
    )


def test_v11_area_sheet_renders_selected_read_only_device_states():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "electric_power" in section
    assert "energy" in section
    assert "voltage" in section

    assert "当前功率" in section
    assert "累计用电" in section
    assert "电压" in section


def test_v11_area_sheet_read_only_states_show_units():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert '" W"' in section
    assert '" kWh"' in section
    assert '" V"' in section


def test_area_sheet_hides_devices_when_upstream_power_is_off():
    content = dashboard_script()

    helper_start = content.index(
        "function collapseAreaSheetPowerGroups"
    )
    helper_end = content.index(
        "function renderAreaSheet",
        helper_start,
    )

    helper = content[
        helper_start:helper_end
    ]

    assert (
        "power_source_device_id"
        in helper
    )

    assert (
        '"powered_off_by_upstream"'
        in helper
    )

    assert (
        "removeChild"
        in helper
    )

    assert (
        "createElement("
        not in helper
    )

    assert (
        '"details"'
        not in helper
    )

    assert (
        '"summary"'
        not in helper
    )

    assert (
        "个设备已关闭"
        not in helper
    )

    render_start = content.index(
        "function renderAreaSheet"
    )
    render_end = content.index(
        "function bindAreaOverview",
        render_start,
    )

    render = content[
        render_start:render_end
    ]

    assert (
        "collapseAreaSheetPowerGroups("
        in render
    )


def test_area_sheet_does_not_require_dining_device_ids_for_upstream_grouping():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    for device_id in (
        "dining.table_light_east",
        "dining.table_light_center",
        "dining.table_light_west",
        "dining.light_power_1",
    ):
        assert device_id not in section


def test_area_sheet_air_purifier_uses_dedicated_device_page():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert (
        "area-sheet-purifier-expanded"
        not in section
    )

    assert (
        "完整控制 ›"
        not in section
    )

    assert (
        "data-open-special-device"
        in section
    )

    assert (
        "area-sheet-device-name-opener"
        in section
    )


def test_area_sheet_supports_power_control_device_delegation():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    assert (
        "power_control_device_id"
        in section
    )

    assert (
        "delegatedPowerTargets"
        in section
    )

    assert (
        "delegatedPowerControlId"
        in section
    )

    assert (
        "delegatedPowerState"
        in section
    )

def test_area_sheet_uses_delegated_power_target_only_for_power_control():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    assert (
        "data-control-device-id"
        in section
    )

    assert (
        "delegatedPowerControlId"
        in section
    )

    assert (
        'control.control_id === "power"'
        in section
    )

    assert (
        "device.device_id || \"\""
        in section
    )


def test_area_sheet_keeps_delegated_light_visible_when_upstream_is_off():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    upstream_start = section.index(
        'device.availability_reason ==='
    )

    upstream_section = section[
        max(
            0,
            upstream_start - 180,
        ):
        upstream_start + 180
    ]

    assert (
        "!device.power_control_device_id"
        in upstream_section
    )

    assert (
        '"powered_off_by_upstream"'
        in upstream_section
    )



def test_area_sheet_delegated_light_keeps_smart_light_advanced_controls():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    assert (
        "delegatedPowerControlId"
        in section
    )

    assert (
        'control.kind === "number"'
        in section
    )

    assert (
        '"brightness"'
        in section
    )

    assert (
        '"color_temperature"'
        in section
    )


def test_area_sheet_power_delegation_is_metadata_driven_not_device_id_driven():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    for device_id in (
        "living.main_light_1",
        "living.main_light_power_1",
        "master_bedroom.main_light_1",
        "master_bedroom.main_light_power_1",
        "princess_room.ceiling_light_1",
        "princess_room.ceiling_light_power_1",
    ):
        assert device_id not in section


def test_area_sheet_does_not_use_power_source_as_basic_control_delegate():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    delegation_start = section.index(
        "var delegatedPowerTargets"
    )

    delegation_end = section.index(
        "for (\n      var deviceIndex",
        delegation_start,
    )

    delegation = section[
        delegation_start:
        delegation_end
    ]

    assert (
        "power_control_device_id"
        in delegation
    )

    assert (
        "power_source_device_id"
        not in delegation
    )



def test_area_sheet_click_prefers_control_level_device_target():
    content = dashboard_script()

    start = content.index(
        "function bindAreaOverview"
    )
    end = content.index(
        "function renderAreaOverview",
        start,
    )

    section = content[start:end]

    assert (
        "data-control-device-id"
        in section
    )

    assert "controlDeviceId" in section
    assert "panelDeviceId" in section

    assert (
        "var deviceId = ("
        in section
    )

    assert (
        "sendDeviceControl("
        in section
    )

def test_area_sheet_power_state_uses_delegated_device_but_smart_state_does_not():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    assert (
        "delegatedPowerState"
        in section
    )

    assert (
        "state.device_id ==="
        in section
    )

    assert (
        "device.device_id"
        in section
    )

    assert (
        "device.power_control_device_id"
        in section
    )


def test_area_sheet_hides_advanced_smart_light_controls_when_delegated_power_is_confirmed_off():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    assert (
        "delegatedPowerIsOff"
        in section
    )

    assert (
        "delegatedPowerState.power === false"
        in section
    )

    assert (
        "controls = controls.filter("
        in section
    )

    assert (
        'control.control_id === "power"'
        in section
    )


def test_area_sheet_does_not_treat_unknown_delegated_power_as_off():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )

    section = content[start:end]

    # Collapse is allowed only for a confirmed
    # boolean false state. Missing/unavailable
    # upstream state must not be guessed as OFF.
    assert (
        "delegatedPowerState.power === false"
        in section
    )

    assert (
        "!delegatedPowerState.power"
        not in section
    )



def test_v11_area_sheet_renders_door_and_doorbell_read_only_states():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )

    section = script[start:end]

    assert '"open"' in section
    assert '"门状态"' in section
    assert '"battery_level"' in section
    assert '"电量"' in section
    assert '"operating_state"' in section
    assert '"工作状态"' in section


def test_v11_area_sheet_formats_boolean_open_state_semantically():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )

    section = script[start:end]

    assert (
        'readOnlyState.parameter === "open"'
        in section
    )

    assert (
        'typeof readOnlyValue === "boolean"'
        in section
    )

    assert '"已打开"' in section
    assert '"已关闭"' in section


def test_v11_area_sheet_does_not_show_doorbell_motion_as_persistent_readonly_state():
    script = dashboard_script()

    start = script.index(
        "var readOnlyStates"
    )
    end = script.index(
        "for (",
        start,
    )

    readonly_definition = script[
        start:end
    ]

    assert '"motion"' not in readonly_definition


def test_area_sheet_supports_p10_pro_readonly_status_semantics():
    content = dashboard_script()

    start = content.index(
        "var readOnlyStates"
    )
    end = content.index(
        'html +=\n'
        '        "</div>" +\n'
        '        "</div>";',
        start,
    )

    section = content[start:end]

    for parameter in (
        "battery_level",
        "operating_state",
        "cleaning",
        "water_shortage",
        "clean_water_box_problem",
        "dirty_water_box_problem",
        "vacuum_error",
        "dock_error",
    ):
        assert (
            'parameter: "'
            + parameter
            + '"'
        ) in section

    # Charging remains Device Data,
    # but is represented by operating_state
    # rather than a duplicate UI row.
    assert (
        'parameter: "charging"'
        not in section
    )

    for label in (
        "工作状态",
        "清扫",
        "供水",
        "清水箱",
        "脏水箱",
        "机器人",
        "基站",
        "充电中",
        "已停靠",
        "正在清扫",
        "未运行",
        "回充中",
        "已暂停",
        "空闲",
        "正常",
        "异常",
    ):
        assert label in section


def test_v11_area_temperature_display_uses_selected_device_sources():
    script = dashboard_script()

    assert "areaTemperatureDisplay" in script

    assert (
        'open_public_area: {\n'
        '        device_id: '
        '"living.temperature_humidity_sensor_1",\n'
        '        parameter: "temperature"'
    ) in script

    assert (
        'master_bedroom: {\n'
        '        device_id: '
        '"master_bedroom.temperature_humidity_sensor_1",\n'
        '        parameter: "temperature"'
    ) in script

    assert (
        'study: {\n'
        '        device_id: "study.air_conditioner_1",\n'
        '        parameter: "current_temperature"'
    ) in script

    assert (
        'princess_room: {\n'
        '        device_id: '
        '"princess_room.air_conditioner_1",\n'
        '        parameter: "current_temperature"'
    ) in script



def test_v11_area_sheet_supports_action_controls():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )

    section = script[start:end]

    assert (
        'control.kind === "action"'
        in section
    )

    assert (
        'data-control-action="true"'
        in section
    )

    assert (
        "deviceControlLabel("
        in section
    )


def test_v11_area_sheet_supports_multi_select_controls():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )

    section = script[start:end]

    assert (
        'control.kind === "multi_select"'
        in section
    )

    assert (
        'data-multi-select-option="'
        in section
    )

    assert (
        'data-multi-select-submit="true"'
        in section
    )

    assert "开始区域清扫" in section


def test_v11_area_sheet_action_sends_null_value():
    script = dashboard_script()

    start = script.index(
        "sheet.onclick = function"
    )
    end = script.index(
        "function areaTemperatureDisplay",
        start,
    )

    section = script[start:end]

    assert (
        '"data-control-action"'
        in section
    )

    assert "value = null" in section

    assert (
        "sendDeviceControl("
        in section
    )


def test_v11_area_sheet_multi_select_builds_one_value_array():
    script = dashboard_script()

    start = script.index(
        "sheet.onclick = function"
    )
    end = script.index(
        "function areaTemperatureDisplay",
        start,
    )

    section = script[start:end]

    assert (
        '"data-multi-select-option"'
        in section
    )

    assert (
        '"data-multi-select-submit"'
        in section
    )

    assert "selectedValues" in section
    assert "selectedValues.push(" in section

    assert (
        "value = selectedValues"
        in section
    )


def test_v11_vacuum_control_labels_use_smartscreen_semantics():
    script = dashboard_script()

    start = script.index(
        "function deviceControlLabel"
    )
    end = script.index(
        "function deviceControlNumberUnit",
        start,
    )

    section = script[start:end]

    assert 'clean_all: "全屋清扫"' in section
    assert 'clean_areas: "区域清扫"' in section

    for option, label in (
        ("living", "客厅"),
        ("dining", "餐厅"),
        ("master_bedroom", "主卧"),
        ("princess_room", "公主房"),
        ("study", "书房"),
        ("master_bath", "主卫"),
        ("guest_bath", "客卫"),
    ):
        assert (
            option + ': "' + label + '"'
            in section
        )



def test_v11_area_temperature_display_formats_floating_point_noise():
    script = dashboard_script()

    start = script.index(
        "function formatTemperatureDisplay"
    )
    end = script.index(
        "function areaTemperatureDisplay",
        start,
    )

    section = script[start:end]

    assert "Math.round" in section
    assert "/ 10" in section


def test_v11_area_temperature_display_uses_temperature_formatter():
    script = dashboard_script()

    start = script.index(
        "function areaTemperatureDisplay"
    )
    end = script.index(
        "function renderAreaOverview",
        start,
    )

    section = script[start:end]

    assert (
        "formatTemperatureDisplay("
        in section
    )

    assert (
        'String(state.value) + " °C"'
        not in section
    )



def test_v11_vacuum_operating_state_labels_cover_runtime_states():
    script = dashboard_script()

    start = script.index(
        "var operatingStateLabels"
    )
    end = script.index(
        "var normalizedOperatingState",
        start,
    )

    section = script[start:end]

    expected = {
        "segment_cleaning": "分区清扫中",
        "washing_the_mop": "清洗拖布",
        "washing_the_mop_2": "清洗拖布",
        "going_to_wash_the_mop": "前往清洗拖布",
        "returning_home": "回充中",
        "docking": "回充中",
        "charging_complete": "充电完成",
        "emptying_the_bin": "集尘中",
    }

    for state, label in expected.items():
        assert (
            state + ': "' + label + '"'
            in section
        )


def test_v11_area_overview_uses_structured_state_lines():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )

    section = script[start:end]

    assert "area-card-state-primary" in section
    assert "area-card-state-secondary" in section


def test_v11_dashboard_bumps_static_asset_versions_for_ui_polish():
    from src.smartscreen_display.dashboard import DASHBOARD_HTML

    assert b"/static/dashboard.css?v=79" in DASHBOARD_HTML
    assert b"/static/dashboard.js?v=60" in DASHBOARD_HTML



def test_v11_home_area_cards_are_driven_by_presentation_zones():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )

    section = script[start:end]

    assert "show_on_home" in section
    assert "summary_location_id" in section
    assert "zone_id" in section
    assert "room_ids" in section


def test_v11_home_no_longer_hardcodes_open_public_area_card():
    from src.smartscreen_display.dashboard import DASHBOARD_HTML

    html = DASHBOARD_HTML.decode(
        "utf-8"
    )

    start = html.index(
        'id="area-overview"'
    )

    end = html.index(
        "</div>",
        start,
    )

    area_section = html[start:end]

    assert (
        'data-location-id="open_public_area"'
        not in area_section
    )



def test_v11_household_actions_follow_area_overview():
    html = dashboard_html()

    assert html.index(
        'id="area-overview"'
    ) < html.index(
        'id="household-actions"'
    )


def test_v11_warm_minimal_css_asset_version():
    from src.smartscreen_display.dashboard import (
        DASHBOARD_HTML,
    )

    assert (
        b"/static/dashboard.css?v=79"
        in DASHBOARD_HTML
    )


def test_v11_family_summary_attention_requires_occupied_area():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )

    section = script[start:end]

    assert "occupancyByLocation" in section
    assert "summary_location_id" in section
    assert "room_ids" in section
    assert '=== "occupied"' in section


def test_v11_family_summary_receives_presentation_zones():
    script = dashboard_script()

    assert "renderFamilySummary(" in script

    start = script.index(
        "function updateSemanticDashboard"
    )

    section = script[start:]

    assert (
        "renderFamilySummary(\n"
        "        cards,\n"
        "        zones,\n"
        "        deviceStates,\n"
        "        devices\n"
        "      );"
        in section
    )


def test_v11_all_lights_off_uses_household_action_api():
    html = dashboard_html()
    script = dashboard_script()

    assert (
        'data-household-action="all_lights_off"'
        in html
    )

    assert (
        '"/api/household/actions"'
        in script
    )

    assert (
        "action_id: actionId"
        in script
    )

    assert (
        "supportedActions"
        in script
    )

    assert (
        "all_lights_off: true"
        in script
    )


def test_v11_household_action_handles_partial_failure():
    script = dashboard_script()

    assert (
        '"partial_failure"'
        in script
    )

    assert (
        "部分设备未响应"
        in script
    )


def test_v11_home_has_today_todo_and_reminder_cards():
    html = dashboard_html()

    assert 'id="today-card"' in html
    assert 'id="today-summary"' in html

    assert 'id="todo-card"' in html
    assert "待办事项" in html

    assert 'id="reminder-card"' in html
    assert 'id="reminder-list"' in html


def test_v11_home_no_longer_exposes_family_summary_card():
    html = dashboard_html()

    assert 'id="family-summary"' not in html
    assert "家庭概览" not in html


def test_v11_today_card_uses_existing_clock_data():
    script = dashboard_script()

    assert "function renderTodaySummary" in script
    assert '"today-summary"' in script

    assert "clock.date" in script
    assert "clock.weekday" in script

    assert (
        "renderTodaySummary("
        in script
    )

def test_v11_reminder_card_is_exception_first():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )

    section = script[start:end]

    assert '"reminder-list"' in section
    assert "暂无需要处理的事项" in section

    assert (
        "家中状态舒适"
        not in section
    )
    assert (
        "家庭状态已更新"
        not in section
    )




def test_v11_home_v2_uses_three_equal_overview_cards():
    css = dashboard_css()

    assert ".home-overview-card" in css
    assert "width: calc(33.333%" in css


def test_v11_home_v2_keeps_four_column_room_grid():
    css = dashboard_css()

    assert ".area-card" in css
    assert "width: calc(25%" in css


def test_v11_home_v2_uses_system_font_stack():
    css = dashboard_css()

    assert "-apple-system" in css
    assert "BlinkMacSystemFont" in css


def test_v11_home_v2_keeps_compact_freshness_indicator():
    css = dashboard_css()

    assert ".update-status" in css
    assert "border-radius: 50%" in css


def test_v11_dashboard_supports_ios_standalone_mode():
    html = dashboard_html()

    assert (
        'name="apple-mobile-web-app-capable"'
        in html
    )
    assert (
        'content="yes"'
        in html
    )

    assert (
        'name="apple-mobile-web-app-status-bar-style"'
        in html
    )
    assert (
        'content="black-translucent"'
        in html
    )

    assert (
        'name="apple-mobile-web-app-title"'
        in html
    )
    assert (
        'content="SmartScreenOS"'
        in html
    )


def test_v11_dashboard_disables_ios_page_zoom():
    html = dashboard_html()

    assert (
        "maximum-scale=1.0"
        in html
    )
    assert (
        "user-scalable=no"
        in html
    )


def test_v11_has_dedicated_ipad_landscape_layout():
    css = dashboard_css()

    assert "iPad Final Base V1" in css
    assert "orientation: landscape" in css
    assert "max-width: 1024px" in css


def test_v11_ipad_layout_rebalances_home_hierarchy():
    css = dashboard_css()

    start = css.index(
        "iPad Final Base V1"
    )
    section = css[start:]

    assert ".primary-panel" in section
    assert ".home-overview-card" in section
    assert ".area-card" in section
    assert ".household-actions" in section


def test_v11_ipad_layout_reduces_clock_dominance():
    css = dashboard_css()

    start = css.index(
        "iPad Final Base V1"
    )
    section = css[start:]

    assert "#time" in section
    assert "font-size: 62px" in section


def test_v11_ipad_layout_keeps_four_room_columns():
    css = dashboard_css()

    start = css.index(
        "iPad Final Base V1"
    )
    section = css[start:]

    assert (
        "width: calc(25% - 8px)"
        in section
    )
    assert (
        "flex: 0 0 calc(25% - 8px)"
        in section
    )


def test_v11_ipad_layout_uses_fixed_legacy_safari_room_height():
    css = dashboard_css()

    start = css.index(
        "iPad Final Base V1"
    )
    section = css[start:]

    assert "height: 360px" in section
    assert "height: 172px" in section
    assert "min-height: 172px" in section


def test_v11_ipad_layout_does_not_depend_on_viewport_height():
    css = dashboard_css()

    start = css.index(
        "iPad Final Base V1"
    )
    section = css[start:]

    assert "100vh" not in section
    assert "overflow: hidden" not in section


def test_v11_ipad_overview_cards_share_same_geometry():
    css = dashboard_css()

    start = css.index(
        "iPad Final Cards V1"
    )
    section = css[start:]

    assert "#today-card" in section
    assert "#todo-card" in section
    assert "#reminder-card" in section

    assert "height: 104px" in section
    assert "min-height: 104px" in section
    assert "padding: 14px 16px" in section


def test_v11_home_has_music_shortcut():
    html = dashboard_html()

    assert 'id="music-shortcut"' in html
    assert 'href="https://music.apple.com/"' in html
    assert 'aria-label="打开音乐"' in html


def test_v11_freshness_indicator_is_inside_household_dock():
    html = dashboard_html()

    start = html.index(
        'id="household-actions"'
    )
    end = html.index(
        "</div>",
        start,
    )

    section = html[start:end]

    assert 'id="update-status"' in section


def test_v11_ipad_overview_cards_share_equal_geometry():
    css = dashboard_css()

    start = css.index(
        "iPad Final Cards V1"
    )
    section = css[start:]

    assert "#today-card" in section
    assert "#todo-card" in section
    assert "#reminder-card" in section

    assert "height: 104px" in section
    assert "min-height: 104px" in section


def test_v11_ipad_today_card_does_not_get_special_large_type():
    css = dashboard_css()

    start = css.index(
        "iPad Final Cards V1"
    )
    section = css[start:]

    assert "#today-summary" in section
    assert "font-size: 14px" in section


def test_v11_ipad_final_adds_top_breathing_room():
    css = dashboard_css()

    start = css.index(
        "iPad Final Cards V1"
    )
    section = css[start:]

    assert ".dashboard" in section
    assert "padding-top: 18px" in section


def test_v11_ipad_final_separates_freshness_from_actions():
    css = dashboard_css()

    start = css.index(
        "iPad Final Cards V1"
    )
    section = css[start:]

    assert ".update-status:before" in section
    assert "height: 22px" in section
    assert "width: 8px" in section


def test_v11_ipad_final_has_composition_spacing():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert "top: -30px" in section
    assert "margin:" in section


def test_v11_ipad_final_refines_freshness_indicator():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert ".update-status" in section
    assert "width: 8px" in section
    assert "height: 8px" in section
    assert "margin:" in section
    assert "0 8px" in section
    assert "0 14px" in section


def test_v11_ipad_final_has_weather_glyph():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert ".weather-icon-cloudy:before" in css
    assert ".weather-icon-cloudy:after" in css
    assert ".weather-icon-sunny" in css
    assert ".weather-icon-sunny .sun-disc" in css
    assert ".weather-icon-sunny .sun-ray" in css


def test_v11_ipad_final_raises_and_spaces_dock():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert "top: -30px" in section
    assert "width: 665px" in section
    assert "max-width: calc(100% - 24px)" in section
    assert "gap: 8px" in section
    assert "border-radius: 27px" in section


def test_v11_ipad_final_refines_freshness_position():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert ".update-status" in section
    assert "top: -4px" in section
    assert "left: 3px" in section
    assert "width: 8px" in section
    assert "height: 8px" in section
    assert ".update-status:before" in section


def test_v11_ipad_final_weather_uses_css_cloud():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert ".weather-icon-cloudy:before" in css
    assert ".weather-icon-cloudy:after" in css
    assert ".weather-icon-sunny" in css
    assert ".weather-icon-sunny .sun-disc" in css
    assert ".weather-icon-sunny .sun-ray" in css


def test_v11_ipad_final_dock_is_raised_from_bottom():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert "top: -30px" in section
    assert "width: 665px" in section
    assert "max-width: calc(100% - 24px)" in section
    assert "gap: 8px" in section


def test_v11_ipad_final_composition_moves_down_six_pixels():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert "Final composition offset." in section
    assert ".dashboard {" in section
    assert "top: 6px" in section


def test_v11_ipad_final_dock_uses_available_width():
    css = dashboard_css()

    start = css.index(
        "iPad Final Polish V1"
    )
    section = css[start:]

    assert "width: 665px" in section
    assert "max-width: calc(100% - 24px)" in section
    assert "min-width: 108px" in section
    assert "min-width: 122px" in section
    assert "min-width: 110px" in section
    assert "align-self: center" in section


def test_v11_reminder_projection_receives_device_states_and_devices():
    script = dashboard_script()

    start = script.index(
        "function updateSemanticDashboard"
    )
    section = script[start:start + 3600]

    assert (
        "renderFamilySummary(\n"
        "        cards,\n"
        "        zones,\n"
        "        deviceStates,\n"
        "        devices\n"
        "      );"
        in section
    )


def test_v11_reminder_projection_supports_low_battery():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert '"battery_level"' in section
    assert "state.available !== true" in section
    assert "numericBattery < 5" in section
    assert '" 电量仅 "' in section


def test_v11_reminder_projection_supports_vacuum_water_alerts():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert '"water_shortage"' in section
    assert '"clean_water_box_problem"' in section
    assert '"dirty_water_box_problem"' in section

    assert "扫地机器人缺水" in section
    assert "请检查扫地机器人清水箱" in section
    assert "请检查扫地机器人污水箱" in section


def test_v11_reminder_projection_supports_vacuum_error_states():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert '"vacuum_error"' in section
    assert '"dock_error"' in section

    assert 'state.value !== "none"' in section
    assert 'state.value !== "ok"' in section

    assert "扫地机器人异常：" in section
    assert "扫地机器人基站异常：" in section


def test_v11_reminder_projection_uses_device_names_not_location_labels_for_battery():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert "deviceNameById" in section
    assert "device.device_id" in section
    assert "device.name" in section


def test_v11_reminder_projection_low_battery_threshold_is_strictly_below_five():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert "numericBattery < 5" in section
    assert "numericBattery <= 5" not in section


def test_v11_reminder_projection_ignores_unavailable_device_state():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert "state.available !== true" in section
    assert "continue;" in section


def test_v11_reminder_projection_does_not_flag_normal_vacuum_values():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert 'state.value !== "none"' in section
    assert 'state.value !== "ok"' in section

    assert (
        'state.parameter ===\n'
        '          "water_shortage" &&\n'
        '        state.value === true'
        in section
    )

    assert (
        'state.parameter ===\n'
        '          "clean_water_box_problem" &&\n'
        '        state.value === true'
        in section
    )

    assert (
        'state.parameter ===\n'
        '          "dirty_water_box_problem" &&\n'
        '        state.value === true'
        in section
    )


def test_v11_reminder_projection_accumulates_multiple_attention_items():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert section.count(
        "attentionParts.push("
    ) >= 6

    assert (
        'attentionParts.join(" · ")'
        in section
    )


def test_v11_reminder_projection_keeps_occupied_dim_attention():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert "occupancyByLocation" in section
    assert '=== "occupied"' in section
    assert 'card.value.state !== "dim"' in section
    assert 'location + "光线偏暗"' in section


def test_v11_reminder_projection_consumes_dashboard_device_contract_only():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert "deviceStates" in section
    assert "devices" in section

    # Reminder presentation must consume canonical
    # dashboard Device Data, not Home Assistant identity.
    assert "entity_id" not in section
    assert "source_id" not in section
    assert "home_assistant" not in section


def test_v11_reminder_projection_supports_entry_door_open_alert():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert (
        '"living.entry_door_sensor_1"'
        in section
    )
    assert (
        '"入户门未关闭"'
        in section
    )


def test_v11_reminder_projection_supports_princess_fire_door_open_alert():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert (
        '"princess_room.fire_door_sensor_1"'
        in section
    )
    assert (
        '"公主房消防门未关闭"'
        in section
    )


def test_v11_door_reminders_require_available_open_true_state():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert "state.available !== true" in section
    assert 'state.parameter === "open"' in section
    assert "state.value === true" in section


def test_v11_door_reminders_have_highest_display_priority():
    script = dashboard_script()

    start = script.index(
        "function renderFamilySummary"
    )
    end = script.index(
        "function resolveAreaLocationIds",
        start,
    )
    section = script[start:end]

    assert "doorAttentionParts" in section

    assert (
        'doorAttentionParts.push(\n'
        '            "入户门未关闭"'
        in section
    )

    assert (
        'doorAttentionParts.push(\n'
        '            "公主房消防门未关闭"'
        in section
    )

    assert (
        "doorAttentionParts.concat("
        in section
    )


def test_v11_room_card_content_keeps_temperature_as_primary_state():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "temperatureDisplay" in section
    assert "primaryParts.push(" in section
    assert "area-card-state-primary" in section


def test_v11_room_card_content_orders_secondary_semantics():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    occupied = section.index(
        'parts.push("有人")'
    )
    comfort = section.index(
        '"舒适度需留意"'
    )
    dim = section.index(
        '"光线偏暗"'
    )

    assert occupied < comfort < dim


def test_v11_room_card_content_does_not_project_device_alerts():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert '"battery_level"' not in section
    assert '"vacuum_error"' not in section
    assert '"dock_error"' not in section
    assert '"入户门未关闭"' not in section
    assert '"公主房消防门未关闭"' not in section


def test_v11_room_card_content_has_no_placeholder_for_missing_state():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert '">--</span>"' not in section
    assert 'stateHtml || "--"' not in section
    assert 'stateNode.innerHTML = "--"' not in section


def test_v11_room_card_initial_markup_has_no_missing_state_placeholder():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "container.innerHTML = areaHtml",
        start,
    )

    section = script[start:end]

    assert '"--"' not in section


def test_v11_room_card_empty_state_does_not_depend_on_location_presence():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "knownLocations" not in section
    assert 'stateNode.innerHTML = ""' in section


def test_v11_night_uses_household_action_api():
    script = dashboard_script()

    start = script.index(
        "function bindHouseholdActions"
    )
    end = script.index(
        "function sendDeviceControl",
        start,
    )
    section = script[start:end]

    assert "supportedActions" in section
    assert "all_lights_off: true" in section
    assert "night: true" in section

    assert (
        'actionId !== "all_lights_off"'
        not in section
    )

    assert "sendHouseholdAction(" in section

def test_v11_away_uses_household_action_api():
    script = dashboard_script()

    start = script.index(
        "function bindHouseholdActions"
    )
    end = script.index(
        "function sendDeviceControl",
        start,
    )
    section = script[start:end]

    assert "supportedActions" in section
    assert "away: true" in section
    assert "sendHouseholdAction(" in section


def test_v2_room_card_adds_visual_state_classes():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "area-card-occupied" in section
    assert "area-card-dim" in section


def test_v2_room_card_secondary_states_are_individual_items():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "area-card-state-item" in section
    assert "secondaryParts.join" not in section


def test_v2_room_card_keeps_temperature_as_primary_hero():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "area-card-state-primary" in section
    assert "temperatureDisplay" in section


def test_v2_room_card_does_not_add_device_level_status():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert '"operating_state"' not in section
    assert '"battery_level"' not in section
    assert '"vacuum_error"' not in section
    assert "entity_id" not in section
    assert "source_id" not in section


def test_v2_room_card_css_has_visual_state_treatment():
    css = dashboard_css()

    assert ".area-card-occupied" in css
    assert ".area-card-dim" in css
    assert ".area-card-state-item" in css


def test_v2_room_card_dim_is_only_presented_when_occupied():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "if (isOccupied && isDim)" in section

    assert (
        'if (isDim) {\n'
        '        parts.push('
        not in section
    )


def test_v2_room_card_dim_visual_state_requires_occupancy():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert (
        'if (isOccupied && isDim) {\n'
        '        areaCard.className +='
        in section
    )


def test_v2_home_clock_hides_seconds_in_presentation():
    script = dashboard_script()

    start = script.index(
        "function updateDashboard"
    )
    end = script.index(
        "function semanticStatusNodeId",
        start,
    )
    section = script[start:end]

    assert "formatClockTime(" in section
    assert 'clock.time || "--:--"' not in section


def test_v2_clock_formatter_returns_hour_and_minute_only():
    script = dashboard_script()

    start = script.index(
        "function formatClockTime"
    )
    end = script.index(
        "function formatDate",
        start,
    )
    section = script[start:end]

    assert "function formatClockTime" in section
    assert 'parts.slice(0, 2).join(":")' in section


def test_v23_home_date_uses_compact_separator():
    script = dashboard_script()

    start = script.index(
        "function formatDate"
    )
    end = script.index(
        "function formatWeatherCondition",
        start,
    )
    section = script[start:end]

    assert '" · "' in section


def test_v23_ipad_clock_has_compact_time_group():
    css = dashboard_css()

    start = css.index(
        "iPad Final Base V1"
    )
    section = css[start:]

    assert "font-size: 62px" in section
    assert "margin-top: 6px" in section
    assert "font-size: 16px" in section


def test_v231_ipad_clock_uses_final_compact_date_hierarchy():
    css = dashboard_css()

    start = css.index(
        "iPad Final Base V1"
    )
    section = css[start:]

    assert "font-size: 62px" in section
    assert "line-height: 0.96" in section
    assert "letter-spacing: -2px" in section

    assert "margin-top: 6px" in section
    assert "font-size: 16px" in section
    assert (
        "rgba(235, 231, 223, 0.62)"
        in section
    )


def test_v11_area_sheet_formats_numeric_readonly_values():
    script = dashboard_script()

    assert "function formatNumericDisplay" in script

    start = script.index(
        "var readOnlyDisplayValue"
    )
    end = script.index(
        'readOnlyState.parameter === "open"',
        start,
    )
    section = script[start:end]

    assert "formatNumericDisplay(" in section
    assert (
        'typeof readOnlyValue === "number"'
        in section
    )

    # Numeric values must no longer be rendered
    # by the old unconditional String(value) path.
    assert (
        "String(readOnlyValue)\n"
        "          + readOnlyState.unit"
        not in section
    )


def test_v11_numeric_display_formatter_removes_float_noise():
    script = dashboard_script()

    start = script.index(
        "function formatNumericDisplay"
    )
    end = script.index(
        "function formatTemperatureDisplay",
        start,
    )
    section = script[start:end]

    assert "Math.round" in section
    assert "* 100" in section
    assert "/ 100" in section


def test_v2_room_card_lights_on_uses_explicit_device_whitelist():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    expected_devices = (
        "corridor.light_1",
        "living.main_light_power_1",
        "living.light_strip_1",
        "living.downlight_1",
        "dining.light_power_1",
        "dining.atmosphere_light_1",
        "kitchen.light_1",
        "master_bedroom.main_light_power_1",
        "master_bedroom.light_strip_1",
        "master_bedroom.downlight_1",
        "study.ceiling_light_1",
        "princess_room.ceiling_light_power_1",
        "princess_room.spotlight_1",
        "princess_room.light_strip_1",
        "master_bath.makeup_light_1",
        "master_bath.bathing_light_1",
        "guest_bath.makeup_light_1",
        "guest_bath.bathing_light_1",
    )

    for device_id in expected_devices:
        assert (
            '"' + device_id + '"'
            in section
        )

    assert "area-card-lights-on" in section


def test_v2_room_card_lights_on_excludes_downstream_smart_lights():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    excluded_devices = (
        "living.main_light_1",
        "master_bedroom.main_light_1",
        "princess_room.ceiling_light_1",
        "dining.table_light_east",
        "dining.table_light_center",
        "dining.table_light_west",
    )

    for device_id in excluded_devices:
        assert (
            '"' + device_id + '"'
            not in section
        )


def test_v2_room_card_lights_on_requires_available_confirmed_power_true():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "state.available === true" in section
    assert 'state.parameter === "power"' in section
    assert "state.value === true" in section


def test_v2_room_card_lights_on_uses_presentation_zone_room_scope():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "presentationZone.room_ids" in section
    assert "lightsOn" in section


def test_v2_room_card_lights_on_keeps_study_smart_light_as_temporary_proxy():
    script = dashboard_script()

    start = script.index(
        "function renderAreaOverview"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    # Temporary exception:
    # study has no confirmed physical master-power
    # device in Device Data yet, so the smart
    # ceiling light currently represents its
    # room-card lighting state.
    assert '"study.ceiling_light_1"' in section



def test_v2_area_sheet_powered_off_branch_closes_body_and_tile():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    branch_start = section.index(
        'device.availability_reason ==='
    )
    branch_end = section.index(
        "continue;",
        branch_start,
    )

    branch = section[
        branch_start:branch_end
    ]

    assert (
        '"上游电源已关闭" +\n'
        '          "</div>" +\n'
        '          "</div>" +\n'
        '          "</div>";'
        in branch
    )


def test_v2_area_sheet_uses_compact_device_tiles():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "area-sheet-device-tile" in section
    assert "area-sheet-device-header" in section
    assert "area-sheet-device-body" in section


def test_v2_area_sheet_does_not_repeat_device_location():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "area-sheet-device-location" not in section
    assert (
        "areaLocationLabel("
        not in section
    )


def test_v2_area_sheet_light_boolean_controls_use_single_toggle():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    # Normal light boolean controls use the unified
    # draggable single-toggle presentation.
    assert 'data-control-toggle="true"' in section
    assert "area-sheet-toggle" in section
    assert "area-sheet-toggle-knob" in section

    # The purifier intentionally uses explicit
    # Run / Stop or On / Off buttons instead of
    # pretending to be a light switch.
    assert (
        "area-sheet-control-purifier-boolean"
        in section
    )
    assert (
        'data-control-value="true"'
        in section
    )
    assert (
        'data-control-value="false"'
        in section
    )


def test_v2_area_sheet_toggle_keeps_control_device_delegation():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "delegatedPowerControlId" in section
    assert "data-control-device-id" in section
    assert 'data-control-toggle="true"' in section


def test_v2_area_sheet_click_supports_single_boolean_toggle():
    script = dashboard_script()

    start = script.index(
        "function bindAreaOverview"
    )
    end = script.index(
        "function renderAreaOverview",
        start,
    )
    section = script[start:end]

    assert '"data-control-toggle"' in section
    assert '"data-current-value"' in section
    assert "sendDeviceControl(" in section


def test_v2_area_sheet_readonly_devices_get_state_tile_class():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "device.area_readonly" in section
    assert "area-sheet-device-readonly" in section


def test_v2_area_sheet_air_purifier_uses_dedicated_device_page():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert (
        'device.device_type ===\n'
        '        "air_purifier"'
        in section
    )

    assert (
        "area-sheet-purifier-expanded"
        not in section
    )

    assert (
        "data-open-special-device"
        in section
    )

    assert (
        "area-sheet-device-name-opener"
        in section
    )

    assert (
        "完整控制"
        not in section
    )


def test_v2_area_sheet_complex_controls_remain_available():
    script = dashboard_script()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert 'control.kind === "number"' in section
    assert 'control.kind === "select"' in section
    assert 'control.kind === "action"' in section
    assert 'control.kind === "multi_select"' in section


def test_v2_area_sheet_css_uses_wide_compact_layout():
    css = dashboard_css()

    assert "Area Sheet Presentation V2" in css
    assert ".area-sheet-device-tile" in css
    assert ".area-sheet-toggle" in css

    start = css.index(
        "Area Sheet Presentation V2"
    )
    section = css[start:]

    assert "display: flex" in section
    assert "flex-wrap: wrap" in section
    assert "width: 74%" in section


def test_v2_area_sheet_ipad_keeps_wide_panel():
    css = dashboard_css()

    start = css.index(
        "Area Sheet Presentation V2"
    )
    section = css[start:]

    assert (
        "@media screen and "
        "(min-width: 769px)"
        in section
    )
    assert "width: 74%" in section


def test_area_sheet_extra_devices_do_not_expand_presentation_room_membership():
    script = dashboard_script()

    sheet_start = script.index(
        "function renderAreaSheet"
    )
    sheet_end = script.index(
        "function bindAreaOverview",
        sheet_start,
    )

    sheet_section = script[
        sheet_start:sheet_end
    ]

    # Explicit stable-device projection belongs only
    # to the Sheet rendering path.
    assert "sheet_extra_device_ids" in sheet_section
    assert "extraDeviceIds" in sheet_section
    assert "device.device_id" in sheet_section

    # Physical presentation membership remains
    # location-based.
    assert "locationScope" in sheet_section
    assert "device.location_id" in sheet_section

    home_start = script.index(
        "var presentationRoomIds"
    )
    home_end = script.index(
        "var lightsOn",
        home_start,
    )

    home_section = script[
        home_start:home_end
    ]

    # Home-card lighting membership must continue
    # to come only from room_ids. Sheet extras must
    # never leak into this semantic/presentation scope.
    assert "presentationZone.room_ids" in home_section
    assert "sheet_extra_device_ids" not in home_section



def test_v11_simple_boolean_uses_ha_tile_power_button():
    script = dashboard_script()
    css = dashboard_css()

    start = script.index(
        "function renderAreaSheet"
    )
    end = script.index(
        "function bindAreaOverview",
        start,
    )
    section = script[start:end]

    assert "booleanOnlyDeviceTile" in section
    assert "area-sheet-ha-toggle" in section
    assert "area-sheet-control-ha-tile" in section

    # Control semantics remain on the existing dispatcher.
    assert "data-device-control" in section
    assert "controlDeviceAttribute" in section
    assert "data-control-device-id" in section

    assert "Area Sheet HA Tile Visual V1" in css
    assert ".area-sheet-ha-toggle" in css



def test_area_sheet_resolves_visible_controls_before_boolean_tile_classification():
    content = dashboard_script()

    start = content.index(
        "function renderAreaSheet"
    )
    end = content.index(
        "function bindAreaOverview",
        start,
    )
    section = content[start:end]

    delegated_off = section.index(
        "var delegatedPowerIsOff"
    )
    controls_filter = section.index(
        "if (delegatedPowerIsOff)",
        delegated_off,
    )
    tile_controls = section.index(
        "var tileControls = controls",
        controls_filter,
    )
    boolean_classification = section.index(
        "var booleanOnlyDeviceTile",
        tile_controls,
    )

    assert (
        delegated_off
        < controls_filter
        < tile_controls
        < boolean_classification
    )

    # Only a confirmed false upstream state may collapse
    # the visible smart-light controls. Unknown state must
    # retain the normal smart-light presentation.
    preparation = section[
        delegated_off:controls_filter
    ]

    assert (
        "delegatedPowerState.power === false"
        in preparation
    )



def test_area_sheet_delegated_power_drives_boolean_tile_visual_state():
    content = dashboard_script()

    start = content.index(
        "var booleanTileValue"
    )
    end = content.index(
        "if (booleanTileValue === true)",
        start,
    )
    section = content[start:end]

    assert (
        'tileControls[0].control_id === "power"'
        in section
    )
    assert (
        "device.power_control_device_id"
        in section
    )
    assert (
        "booleanTileValue ="
        in section
    )
    assert (
        "delegatedPowerState.power"
        in section
    )
