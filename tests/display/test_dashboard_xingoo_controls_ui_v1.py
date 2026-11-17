from pathlib import Path


PROJECT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DASHBOARD_HTML = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "dashboard.py"
)

DASHBOARD_JS = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "static"
    / "dashboard.js"
)

DASHBOARD_CSS = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "static"
    / "dashboard.css"
)


def html():
    return DASHBOARD_HTML.read_text(
        encoding="utf-8"
    )


def script():
    return DASHBOARD_JS.read_text(
        encoding="utf-8"
    )


def stylesheet():
    return DASHBOARD_CSS.read_text(
        encoding="utf-8"
    )


def test_dashboard_has_xingoo_air_purifier_control_panel():
    content = html()

    assert (
        'id="xingoo-air-purifier-controls"'
        in content
    )

    assert (
        'data-device-type="air_purifier"'
        in content
    )

    panel_start = content.index(
        'id="xingoo-air-purifier-controls"'
    )
    panel_end = content.index(
        ">",
        panel_start,
    )

    panel_opening_tag = content[
        panel_start:panel_end
    ]

    assert (
        "data-device-id="
        not in panel_opening_tag
    )

    assert "IAM消毒空气净化器" in content


def test_dashboard_exposes_supported_device_controls():
    content = html()

    for control_id in (
        "power",
        "mode",
        "wind_speed",
        "ions",
        "disinfection",
        "screen_on",
        "child_lock",
    ):
        assert (
            'data-device-control="'
            + control_id
            + '"'
        ) in content


def test_dashboard_exposes_control_values():
    content = html()

    for value in (
        "true",
        "false",
        "smart",
        "sleep",
        "1",
        "2",
        "3",
        "4",
        "5",
    ):
        assert (
            'data-control-value="'
            + value
            + '"'
        ) in content


def test_dashboard_uses_device_action_api():
    content = script()

    assert (
        '"/api/device/actions"'
        in content
    )
    assert "sendDeviceControl" in content
    assert "bindDeviceControls" in content


def test_dashboard_sends_generic_control_payload_fields():
    content = script()

    start = content.index(
        "function sendDeviceControl"
    )

    end = content.index(
        "function bindDeviceControls",
        start,
    )

    section = content[start:end]

    assert "device_id: deviceId" in section
    assert "control_id: controlId" in section
    assert "value: value" in section

    assert "action: action" not in section
    assert "extraPayload.speed" not in section
    assert "extraPayload.enabled" not in section



def test_dashboard_does_not_expose_vendor_protocol_fields():
    content = html()

    for vendor_field in (
        "PowerSwitch",
        "WorkMode",
        "WindSpeed",
        "IonsSwitch",
        "DisinfectSwitch",
        "ScreenSwitch",
        "ChildLockSwitch",
    ):
        assert vendor_field not in content


def test_dashboard_has_device_control_styles():
    content = stylesheet()

    assert ".device-control-section" in content
    assert ".device-control-buttons" in content
    assert ".device-control-status" in content


def test_dashboard_bumps_static_asset_revision():
    content = html()

    assert (
        "/static/dashboard.css?v=79"
        in content
    )
    assert (
        "/static/dashboard.js?v=60"
        in content
    )



def test_dashboard_renders_xingoo_control_state_from_observations():
    content = script()

    assert (
        "renderXingooDeviceControlState"
        in content
    )

    assert "provenance.device_id" in content

    for parameter in (
        "power",
        "mode",
        "wind_speed",
        "ions",
        "disinfection",
        "screen_on",
        "child_lock",
    ):
        assert parameter in content


def test_dashboard_has_real_device_state_active_style():
    content = stylesheet()

    assert (
        ".device-control-active"
        in content
    )


def test_generic_observation_renderer_keeps_control_state_hidden():
    content = script()

    start = content.index(
        "function renderGenericObservations"
    )

    end = content.index(
        "function renderFamilySummary",
        start,
    )

    section = content[start:end]

    for parameter in (
        '"power"',
        '"mode"',
        '"wind_speed"',
        '"ions"',
        '"disinfection"',
        '"screen_on"',
        '"child_lock"',
    ):
        assert parameter not in section



def test_device_action_success_immediately_requests_confirmed_state():
    content = script()

    start = content.index(
        "function sendDeviceControl"
    )

    end = content.index(
        "function bindDeviceControls",
        start,
    )

    section = content[start:end]

    assert (
        '"命令已发送"'
        in section
    )

    assert (
        "updateSemanticDashboard();"
        in section
    )



def test_device_control_only_disables_clicked_button_while_pending():
    content = script()

    start = content.index(
        "function sendDeviceControl"
    )

    end = content.index(
        "function bindDeviceControls",
        start,
    )

    section = content[start:end]

    assert (
        "deviceControlRequestPending = true"
        in section
    )

    assert (
        "sourceButton.disabled = true"
        in section
    )

    assert (
        "sourceButton.disabled = false"
        in section
    )

    assert (
        "setDeviceControlButtonsDisabled("
        not in section
    )


def test_device_control_blocks_overlapping_commands_without_dimming_panel():
    content = script()

    assert (
        "if (deviceControlRequestPending)"
        in content
    )

    assert (
        "正在发送并确认状态..."
        in content
    )


def test_sleep_mode_visually_implies_screen_off():
    content = script()

    start = content.index(
        "function renderXingooDeviceControlState"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "state.mode === 2"
        in section
    )

    assert (
        "effectiveScreenOn"
        in section
    )

    assert (
        "state.mode === 2"
        in section
        and "false" in section
    )


def test_work_mode_one_is_not_exposed_as_user_visible_mode():
    html_content = html()
    js_content = script()

    start = js_content.index(
        "function renderXingooDeviceControlState"
    )

    end = js_content.index(
        "function renderGenericObservations",
        start,
    )

    section = js_content[
        start:end
    ]

    # M8 reports WorkMode=1 after a
    # direct wind-speed selection, but
    # the vendor app does not expose
    # this as a named "manual" mode.
    assert (
        "state.mode === 0"
        in section
    )

    assert (
        "state.mode === 2"
        in section
    )

    assert (
        "state.mode === 1"
        not in section
    )

    assert (
        'data-control-value="manual"'
        not in html_content
    )

    assert (
        ">手动</button>"
        not in html_content
    )

    # Wind speed remains independently
    # represented and may still be active
    # while neither visible mode is active.
    assert (
        '[data-device-control="wind_speed"]'
        in section
    )


def test_work_mode_one_is_not_exposed_as_user_visible_mode():
    html_content = html()
    js_content = script()

    start = js_content.index(
        "function renderXingooDeviceControlState"
    )

    end = js_content.index(
        "function renderGenericObservations",
        start,
    )

    section = js_content[
        start:end
    ]

    # M8 reports WorkMode=1 after a
    # direct wind-speed selection, but
    # the vendor app does not expose
    # this as a named "manual" mode.
    assert (
        "state.mode === 0"
        in section
    )

    assert (
        "state.mode === 2"
        in section
    )

    assert (
        "state.mode === 1"
        not in section
    )

    assert (
        'data-control-value="manual"'
        not in html_content
    )

    assert (
        ">手动</button>"
        not in html_content
    )

    # Wind speed remains independently
    # represented and may still be active
    # while neither visible mode is active.
    assert (
        '[data-device-control="wind_speed"]'
        in section
    )


def test_smart_mode_is_the_only_visible_mode_for_work_mode_zero():
    content = script()

    start = content.index(
        "function renderXingooDeviceControlState"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "state.mode === 0"
        in section
    )

    assert (
        '[data-device-control="mode"]'
        in section
    )

    assert (
        '[data-control-value="smart"]'
        in section
    )


def test_sleep_mode_is_visible_for_work_mode_two_and_implies_dark_screen():
    content = script()

    start = content.index(
        "function renderXingooDeviceControlState"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "state.mode === 2"
        in section
    )

    assert (
        '[data-control-value="sleep"]'
        in section
    )

    assert (
        "effectiveScreenOn = false"
        in section
    )



def test_dashboard_binds_special_panel_from_declared_device_type():
    content = script()

    start = content.index(
        "function bindSpecialDevicePanels"
    )
    end = content.index(
        "function renderGenericDeviceControls",
        start,
    )

    section = content[start:end]

    assert (
        'getAttribute('
        in section
    )
    assert (
        '"data-device-type"'
        in section
    )
    assert (
        "device.device_type"
        in section
    )
    assert (
        "!== deviceType"
        in section
    )
    assert (
        '"data-device-id"'
        in section
    )
    assert (
        "device.device_id"
        in section
    )



def test_dashboard_renders_generic_device_controls_from_dashboard_metadata():
    content = script()

    assert "payload.devices || []" in content
    assert "renderGenericDeviceControls" in content

    start = content.index(
        "function renderGenericDeviceControls"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        'device.device_type === '
        '"air_purifier"'
        in section
    )

    assert (
        "open_public_area."
        "xingoo_air_purifier_1"
        not in section
    )

    assert "device.controls || []" in section
    assert 'control.kind === "boolean"' in section

    assert (
        'data-device-id="'
        in section
    )

    assert (
        'data-device-control="'
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


def test_generic_device_controls_use_existing_device_action_sender():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert "sendDeviceControl(" in section


def test_generic_device_controls_only_highlight_available_device_states():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "deviceStates = deviceStates || []"
        in section
    )

    assert (
        "state.device_id !== device.device_id"
        in section
    )

    assert (
        "state.available !== true"
        in section
    )

    assert (
        "observation.quality"
        not in section
    )


def test_generic_device_controls_explain_missing_confirmed_state():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert "状态未知" in section


def test_generic_device_active_state_is_visually_distinct_from_hover():
    content = stylesheet()

    assert (
        ".device-control-buttons "
        "button.device-control-active"
        in content
    )

    assert (
        "box-shadow:"
        in content
    )


def test_generic_device_controls_use_device_scoped_parameter_states():
    content = script()

    assert (
        "payload.device_states || []"
        in content
    )

    start = content.index(
        "function renderGenericDeviceControls"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert "deviceStates" in section

    assert (
        "state.device_id"
        in section
    )

    assert (
        "state.parameter"
        in section
    )

    assert (
        "state.available !== true"
        in section
    )


def test_generic_device_control_state_does_not_use_location_parameter_observations():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "provenance.device_id"
        not in section
    )

    assert (
        "observation.quality"
        not in section
    )


def test_generic_device_controls_keep_same_parameter_devices_independent():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )

    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "state.device_id !== device.device_id"
        in section
    )

    assert (
        "deviceState[state.parameter] = state.value"
        in section
    )


def test_generic_device_controls_hide_device_when_upstream_power_is_off():
    script = DASHBOARD_JS.read_text(
        encoding="utf-8"
    )

    start = script.index(
        "function renderGenericDeviceControls"
    )
    end = script.index(
        "container.innerHTML = html",
        start,
    )

    section = script[start:end]

    assert (
        'device.availability_reason'
        in section
    )
    assert (
        '"powered_off_by_upstream"'
        in section
    )

    # A child device whose physical upstream supply
    # is confirmed OFF remains part of the backend
    # device model, but is not rendered as an
    # actionable dashboard device.
    assert (
        "continue;"
        in section
    )

    upstream_check = section.index(
        '"powered_off_by_upstream"'
    )
    continue_after_check = section.index(
        "continue;",
        upstream_check,
    )
    device_markup = section.index(
        "'<div class=\"device-control-section\"'"
    )

    assert (
        continue_after_check
        < device_markup
    )


def test_generic_device_controls_render_number_controls():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert 'control.kind === "number"' in section
    assert 'data-control-delta="' in section
    assert "状态未知" in section


def test_generic_number_controls_use_parameter_specific_ui_increment():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert "control.control_id" in section
    assert '"brightness"' in section
    assert '"color_temperature"' in section
    assert "numberIncrement = 5" in section
    assert "numberIncrement = 100" in section


def test_generic_number_controls_send_numeric_values():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert "parseFloat(" in section
    assert "Number.isNaN" in section
    assert "sendDeviceControl(" in section


def test_generic_number_controls_clamp_to_metadata_range():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert "controlMinimum" in section
    assert "controlMaximum" in section
    assert "Math.max(" in section
    assert "Math.min(" in section


def test_generic_number_controls_do_not_guess_unknown_state():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "numberStateAvailable"
        in section
    )
    assert (
        'numberStateAvailable ? "" : " disabled"'
        in section
    )
    assert "numberStateAvailable" in section
    assert "numberDisplayValue" in section
    assert '"状态未知"' in section


def test_generic_device_controls_render_select_controls():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )
    section = content[start:end]

    assert 'control.kind === "select"' in section
    assert "control.options || []" in section
    assert "data-control-value" in section


def test_generic_select_control_highlights_confirmed_state():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )
    section = content[start:end]

    assert "String(" in section
    assert "device-control-active" in section


def test_generic_device_controls_use_user_friendly_control_labels():
    content = script()

    assert "function deviceControlLabel" in content

    for control_id, label in (
        ("power", "开关"),
        ("brightness", "亮度"),
        ("color_temperature", "色温"),
        ("operating_state", "模式"),
        ("target_temperature", "设定温度"),
        ("fan_mode", "风速"),
        ("state", "状态"),
        ("position", "位置"),
    ):
        assert (
            control_id + ":"
            in content
            or (
                '"' + control_id + '"'
                in content
            )
        )
        assert label in content

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert "deviceControlLabel(" in section


def test_generic_device_controls_use_user_friendly_option_labels():
    content = script()

    assert (
        "function deviceControlOptionLabel"
        in content
    )

    for value, label in (
        ("off", "关闭"),
        ("cool", "制冷"),
        ("heat", "制热"),
        ("low", "低速"),
        ("medium", "中速"),
        ("open", "打开"),
        ("close", "关闭"),
        ("stop", "停止"),
    ):
        assert (
            '"' + value + '"'
            in content
        )
        assert label in content

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "deviceControlOptionLabel("
        in section
    )


def test_generic_number_controls_show_semantic_units():
    content = script()

    assert (
        "function deviceControlNumberUnit"
        in content
    )

    assert '"target_temperature"' in content
    assert '" °C"' in content
    assert '"position"' in content
    assert '" %"' in content

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )

    section = content[start:end]

    assert (
        "deviceControlNumberUnit("
        in section
    )


def test_generic_device_control_handler_only_dispatches_rendered_control_shapes():
    content = script()

    start = content.index(
        "function renderGenericDeviceControls"
    )
    end = content.index(
        "function renderGenericObservations",
        start,
    )
    section = content[start:end]

    # The generic renderer currently emits only:
    # boolean/select -> data-control-value
    # number         -> data-control-delta
    #
    # Action/toggle/multi-select dispatch belongs to
    # other UI surfaces and must not leak into this
    # handler as undeclared variables.
    assert "rawValue" in section
    assert "rawDelta" in section

    for orphan_name in (
        "rawAction",
        "rawToggle",
        "rawCurrent",
        "multiSelectSubmit",
        "multiSelectOption",
    ):
        assert orphan_name not in section
