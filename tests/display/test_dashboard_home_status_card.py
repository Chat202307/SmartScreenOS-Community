from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_css():
    return (
        STATIC_DIR / "dashboard.css"
    ).read_text(encoding="utf-8")


def dashboard_js():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def test_dashboard_has_home_status_card():
    html = dashboard_html()

    assert 'id="home-status-card"' in html
    assert "家庭状态" in html


def test_dashboard_has_home_status_list():
    html = dashboard_html()

    assert 'id="home-status-list"' in html


def test_dashboard_requests_home_api():
    script = dashboard_js()

    assert '"/api/home?ts="' in script
    assert "XMLHttpRequest" in script


def test_dashboard_reads_home_items():
    script = dashboard_js()

    assert "payload.items" in script


def test_dashboard_renders_home_item_name():
    script = dashboard_js()

    assert "item.name" in script


def test_dashboard_renders_home_item_state():
    script = dashboard_js()

    assert "item.state" in script


def test_dashboard_handles_empty_home_status():
    script = dashboard_js()

    assert "暂无家庭状态" in script


def test_home_status_card_has_layout():
    css = dashboard_css()

    assert "#home-status-card" in css
    assert "#home-status-list" in css


def test_home_status_rows_have_layout():
    css = dashboard_css()

    assert ".home-status-row" in css
    assert ".home-status-name" in css
    assert ".home-status-value" in css


def test_home_status_refreshes_frequently():
    script = dashboard_js()

    assert "setInterval(updateHomeStatusCard, 5000)" in script


def test_home_status_request_bypasses_browser_cache():
    script = dashboard_js()

    assert "new Date().getTime()" in script
    assert '"/api/home?ts="' in script


def test_home_status_card_has_state_class_mapper():
    script = dashboard_js()

    assert "function homeStatusClass(state)" in script


def test_home_status_card_maps_active_states():
    script = dashboard_js()

    assert '"开启"' in script
    assert '"有人"' in script
    assert '"已打开"' in script
    assert '"制冷"' in script
    assert '"state-active"' in script


def test_home_status_card_maps_inactive_states():
    script = dashboard_js()

    assert '"关闭"' in script
    assert '"无人"' in script
    assert '"已关闭"' in script
    assert '"state-inactive"' in script


def test_home_status_card_maps_problem_states():
    script = dashboard_js()

    assert '"离线"' in script
    assert '"state-warning"' in script
    assert '"未知"' in script
    assert '"state-unknown"' in script


def test_home_status_active_state_has_visual_style():
    style = dashboard_css()

    assert ".home-status-row.state-active" in style


def test_home_status_inactive_state_has_visual_style():
    style = dashboard_css()

    assert ".home-status-row.state-inactive" in style


def test_home_status_warning_state_has_visual_style():
    style = dashboard_css()

    assert ".home-status-row.state-warning" in style


def test_home_status_unknown_state_has_visual_style():
    style = dashboard_css()

    assert ".home-status-row.state-unknown" in style


def test_home_status_card_renders_icon_class():
    script = dashboard_js()

    assert "home-status-icon" in script
    assert "item.icon" in script


def test_home_status_card_builds_icon_class_name():
    script = dashboard_js()

    assert '"icon-" + item.icon' in script


def test_home_status_icon_has_base_style():
    style = dashboard_css()

    assert ".home-status-icon" in style


def test_home_status_door_icon_has_style():
    style = dashboard_css()

    assert ".icon-door" in style


def test_home_status_presence_icon_has_style():
    style = dashboard_css()

    assert ".icon-presence" in style


def test_home_status_light_icon_has_style():
    style = dashboard_css()

    assert ".icon-light" in style


def test_home_status_climate_icon_has_style():
    style = dashboard_css()

    assert ".icon-climate" in style


def test_home_status_cover_icon_has_style():
    style = dashboard_css()

    assert ".icon-cover" in style


def test_home_status_card_marks_actionable_rows():
    script = dashboard_js()

    assert "home-status-actionable" in script
    assert "item.action" in script


def test_home_status_card_stores_entity_action():
    script = dashboard_js()

    assert "data-action" in script
    assert "data-entity-id" in script


def test_home_status_card_has_action_function():
    script = dashboard_js()

    assert "function performHomeAction" in script


def test_home_status_card_posts_action_api():
    script = dashboard_js()

    assert '"/api/home/actions"' in script
    assert '"POST"' in script


def test_home_status_card_sends_action_payload():
    script = dashboard_js()

    assert "entity_id" in script
    assert "action" in script
    assert "JSON.stringify" in script


def test_home_status_actionable_row_has_style():
    style = dashboard_css()

    assert ".home-status-actionable" in style


def test_home_action_function_is_available_to_inline_handler():
    script = dashboard_js()

    assert "window.performHomeAction = performHomeAction" in script


def test_home_action_has_busy_guard():
    script = dashboard_js()

    assert "homeActionBusy" in script


def test_home_action_ignores_repeated_clicks():
    script = dashboard_js()

    assert "if (homeActionBusy)" in script


def test_home_action_sets_busy_before_request():
    script = dashboard_js()

    assert "homeActionBusy = true" in script


def test_home_action_clears_busy_after_request():
    script = dashboard_js()

    assert "homeActionBusy = false" in script


def test_home_status_has_busy_style():
    style = dashboard_css()

    assert ".home-status-busy" in style


def test_home_action_has_cooldown():
    script = dashboard_js()

    assert "homeActionCooldown" in script


def test_home_action_uses_cooldown_timer():
    script = dashboard_js()

    assert "setTimeout" in script
    assert "800" in script


def test_home_action_keeps_busy_until_cooldown_finishes():
    script = dashboard_js()

    assert "homeActionBusy = false" in script
    assert "homeActionCooldown" in script


def test_home_action_has_error_feedback():
    script = dashboard_js()

    assert "home-action-error" in script


def test_home_action_checks_response_status():
    script = dashboard_js()

    assert "request.status" in script
    assert "request.status !== 200" in script


def test_home_action_shows_error_on_failed_request():
    script = dashboard_js()

    assert "showHomeActionError" in script


def test_home_action_error_is_temporary():
    script = dashboard_js()

    assert "homeActionErrorTimeout" in script


def test_home_action_error_has_style():
    style = dashboard_css()

    assert ".home-action-error" in style


def test_home_status_card_supports_multiple_actions():
    script = dashboard_js()

    assert "item.actions" in script


def test_home_status_card_selects_turn_on_when_off():
    script = dashboard_js()

    assert '"关闭"' in script
    assert '"turn_on"' in script


def test_home_status_card_selects_turn_off_when_active():
    script = dashboard_js()

    assert '"turn_off"' in script


def test_home_status_card_builds_action_from_multiple_actions():
    script = dashboard_js()

    assert "resolvedAction" in script


def test_home_status_card_uses_raw_state_for_multi_action_control():
    script = dashboard_js()

    assert "item.raw_state" in script
    assert 'item.raw_state === "off"' in script


def test_home_status_card_renders_climate_details():
    script = dashboard_js()

    assert "current_temperature" in script
    assert "temperature" in script
    assert "fan_mode" in script


def test_home_status_card_has_climate_detail_class():
    script = dashboard_js()

    assert "home-status-detail" in script


def test_home_status_climate_detail_has_style():
    style = dashboard_css()

    assert ".home-status-detail" in style


def test_home_status_card_renders_temperature_controls():
    script = dashboard_js()

    assert "home-temperature-controls" in script


def test_home_status_card_has_temperature_decrease_control():
    script = dashboard_js()

    assert "decreaseHomeTemperature" in script


def test_home_status_card_has_temperature_increase_control():
    script = dashboard_js()

    assert "increaseHomeTemperature" in script


def test_home_temperature_control_posts_set_temperature():
    script = dashboard_js()

    assert '"set_temperature"' in script


def test_home_temperature_controls_use_step():
    script = dashboard_js()

    assert "target_temp_step" in script


def test_home_temperature_controls_have_style():
    style = dashboard_css()

    assert ".home-temperature-controls" in style


def test_home_status_card_renders_fan_controls():
    script = dashboard_js()

    assert "home-fan-controls" in script


def test_home_status_card_has_set_fan_mode_function():
    script = dashboard_js()

    assert "setHomeFanMode" in script


def test_home_status_card_posts_set_fan_mode():
    script = dashboard_js()

    assert '"set_fan_mode"' in script
    assert "fan_mode" in script


def test_home_status_card_maps_low_to_second_speed():
    script = dashboard_js()

    assert '"low"' in script
    assert "2档" in script


def test_home_status_card_maps_medium_to_third_speed():
    script = dashboard_js()

    assert '"medium"' in script
    assert "3档" in script


def test_home_fan_controls_have_style():
    style = dashboard_css()

    assert ".home-fan-controls" in style


def test_home_status_card_renders_hvac_mode_controls():
    script = dashboard_js()

    assert "home-hvac-controls" in script


def test_home_status_card_has_set_hvac_mode_function():
    script = dashboard_js()

    assert "setHomeHvacMode" in script


def test_home_status_card_posts_set_hvac_mode():
    script = dashboard_js()

    assert '"set_hvac_mode"' in script
    assert "hvac_mode" in script


def test_home_status_card_maps_off_mode():
    script = dashboard_js()

    assert '"off"' in script
    assert "关闭" in script


def test_home_status_card_maps_cool_mode():
    script = dashboard_js()

    assert "cool" in script
    assert "制冷" in script


def test_home_status_card_maps_heat_mode():
    script = dashboard_js()

    assert "heat" in script
    assert "制热" in script


def test_home_hvac_controls_have_style():
    style = dashboard_css()

    assert ".home-hvac-controls" in style


def test_home_status_card_marks_active_hvac_mode():
    script = dashboard_js()

    assert "home-control-active" in script
    assert "item.raw_state" in script


def test_home_status_card_marks_active_fan_mode():
    script = dashboard_js()

    assert "item.fan_mode" in script
    assert "home-control-active" in script


def test_home_control_active_has_style():
    style = dashboard_css()

    assert ".home-control-active" in style


def test_home_control_clears_active_state_while_pending():
    script = dashboard_js()

    assert "clearHomeControlActive" in script


def test_home_fan_control_keeps_real_active_state_until_refresh():
    script = dashboard_js()

    start = script.index(
        "function setHomeFanMode("
    )
    end = script.index(
        "window.setHomeFanMode",
        start,
    )

    section = script[start:end]

    assert (
        "clearHomeControlActive(homeList)"
        not in section
    )

    assert "updateHomeStatusCard()" in section


def test_home_hvac_control_keeps_real_active_state_until_refresh():
    script = dashboard_js()

    start = script.index(
        "function setHomeHvacMode("
    )
    end = script.index(
        "window.setHomeHvacMode",
        start,
    )

    section = script[start:end]

    assert (
        "clearHomeControlActive(homeList)"
        not in section
    )

    assert "updateHomeStatusCard()" in section


def test_home_control_pending_has_style():
    style = dashboard_css()

    assert ".home-control-pending" in style


def test_home_status_card_renders_cover_controls():
    script = dashboard_js()

    assert "home-cover-controls" in script


def test_home_status_card_has_cover_action_function():
    script = dashboard_js()

    assert "performHomeCoverAction" in script


def test_home_status_card_posts_cover_action():
    script = dashboard_js()

    assert '"cover_action"' in script
    assert "cover_action" in script


def test_home_status_card_has_open_cover_control():
    script = dashboard_js()

    assert "打开" in script
    assert "open" in script


def test_home_status_card_has_stop_cover_control():
    script = dashboard_js()

    assert "停止" in script
    assert "stop" in script


def test_home_status_card_has_close_cover_control():
    script = dashboard_js()

    assert "关闭" in script
    assert "close" in script


def test_home_cover_controls_have_style():
    style = dashboard_css()

    assert ".home-cover-controls" in style


def test_home_status_card_renders_cover_controls():
    script = dashboard_js()

    assert "home-cover-controls" in script


def test_home_status_card_has_cover_action_function():
    script = dashboard_js()

    assert "performHomeCoverAction" in script


def test_home_status_card_posts_cover_action():
    script = dashboard_js()

    assert '"cover_action"' in script


def test_home_status_card_has_cover_open_control():
    script = dashboard_js()

    assert '"open"' in script
    assert "打开" in script


def test_home_status_card_has_cover_stop_control():
    script = dashboard_js()

    assert '"stop"' in script
    assert "停止" in script


def test_home_status_card_has_cover_close_control():
    script = dashboard_js()

    assert '"close"' in script
    assert "关闭" in script



def test_home_cover_controls_have_style():
    style = dashboard_css()

    assert ".home-cover-controls" in style


def test_home_status_card_tracks_cover_last_action():
    script = dashboard_js()

    assert "homeCoverLastAction" in script


def test_home_status_card_records_cover_action_after_success():
    script = dashboard_js()

    assert (
        "homeCoverLastAction[entityId] = coverAction"
        in script
    )


def test_home_status_card_shows_cover_opening_state():
    script = dashboard_js()

    assert '"打开中"' in script


def test_home_status_card_shows_cover_closing_state():
    script = dashboard_js()

    assert '"关闭中"' in script


def test_home_status_card_shows_cover_stopped_state():
    script = dashboard_js()

    assert '"已停止"' in script


def test_home_status_card_shows_cover_unavailable_state():
    script = dashboard_js()

    assert '"状态不可用"' in script


def test_home_status_card_stop_has_no_active_direction():
    script = dashboard_js()

    assert (
        'coverLastAction === "open"'
        in script
    )
    assert (
        'coverLastAction === "close"'
        in script
    )


def test_home_status_card_supports_cover_position():
    script = dashboard_js()

    assert "item.position" in script


def test_home_status_card_displays_cover_position_percent():
    script = dashboard_js()

    assert '"%打开"' in script


def test_home_status_card_prefers_real_cover_position():
    script = dashboard_js()

    assert (
        "item.position !== undefined"
        in script
    )


def test_home_status_card_displays_fully_closed_cover_position():
    script = dashboard_js()

    assert 'item.position === 0' in script
    assert '"已关闭"' in script


def test_home_status_card_displays_fully_open_cover_position():
    script = dashboard_js()

    assert 'item.position === 100' in script
    assert '"已打开"' in script


def test_home_status_card_cover_open_action_precedes_stale_position():
    script = dashboard_js()

    assert (
        'coverLastAction === "open"'
        in script
    )
    assert (
        'coverDisplayState = "打开中"'
        in script
    )


def test_home_status_card_cover_close_action_precedes_stale_position():
    script = dashboard_js()

    assert (
        'coverLastAction === "close"'
        in script
    )
    assert (
        'coverDisplayState = "关闭中"'
        in script
    )


def test_home_status_card_cover_open_completes_at_100():
    script = dashboard_js()

    assert "item.position === 100" in script
    assert 'coverLastAction === "open"' in script
    assert (
        "homeCoverLastAction["
        in script
    )


def test_home_status_card_cover_close_completes_at_0():
    script = dashboard_js()

    assert "item.position === 0" in script
    assert 'coverLastAction === "close"' in script
    assert (
        "homeCoverLastAction["
        in script
    )


def test_home_cover_action_sets_pending_before_request():
    script = dashboard_js()

    pending = (
        "homeCoverLastAction[entityId] = coverAction"
    )
    send = "request.send("

    assert pending in script
    assert send in script
    assert script.index(pending) < script.index(
        send,
        script.index(
            "function performHomeCoverAction("
        ),
    )


def test_home_cover_action_refreshes_immediately():
    script = dashboard_js()

    function_start = script.index(
        "function performHomeCoverAction("
    )
    send = script.index(
        "request.send(",
        function_start,
    )

    immediate_refresh = script.index(
        "updateHomeStatusCard();",
        function_start,
    )

    assert immediate_refresh < send


def test_home_cover_action_restores_pending_on_failure():
    script = dashboard_js()

    assert "previousCoverLastAction" in script
    assert (
        "homeCoverLastAction[entityId]"
        in script
    )
    assert (
        "previousCoverLastAction"
        in script
    )


def test_home_status_card_highlights_cover_stop_button():
    script = dashboard_js()

    assert (
        'coverLastAction === "stop"'
        in script
    )
    assert (
        'data-cover-action="stop"'
        in script
    )
    assert (
        '"home-control-active"'
        in script
    )


def test_home_status_card_open_pending_only_at_closed_endpoint():
    script = dashboard_js()

    assert (
        'coverLastAction === "open" &&'
        in script
    )
    assert (
        "item.position === 0"
        in script
    )


def test_home_status_card_close_pending_only_at_open_endpoint():
    script = dashboard_js()

    assert (
        'coverLastAction === "close" &&'
        in script
    )
    assert (
        "item.position === 100"
        in script
    )


def test_home_status_card_real_intermediate_position_has_priority():
    script = dashboard_js()

    assert (
        'item.position > 0 &&'
        in script
    )
    assert (
        "item.position < 100"
        in script
    )
    assert (
        'item.position + "%打开"'
        in script
    )


def test_home_cover_action_updates_button_highlight_immediately():
    script = dashboard_js()

    assert "setHomeCoverPendingUi" in script
    assert (
        "setHomeCoverPendingUi("
        in script
    )


def test_home_cover_pending_ui_finds_cover_buttons():
    script = dashboard_js()

    assert "home-cover-controls" in script
    assert "getElementsByTagName" in script


def test_home_cover_pending_ui_marks_selected_button_active():
    script = dashboard_js()

    assert (
        'buttonCoverAction === coverAction'
        in script
    )
    assert (
        '"home-control-active"'
        in script
    )


def test_home_cover_action_restores_button_highlight_on_failure():
    script = dashboard_js()

    assert (
        "setHomeCoverPendingUi("
        in script
    )
    assert (
        "previousCoverLastAction"
        in script
    )
    assert (
        "setHomeCoverPendingUi(\n"
        "          entityId,\n"
        "          previousCoverLastAction\n"
        "        );"
        in script
    )


def test_home_cover_action_does_not_dim_all_home_controls():
    script = dashboard_js()

    start = script.index(
        "function performHomeCoverAction("
    )
    end = script.index(
        "window.performHomeCoverAction",
        start,
    )

    cover_action_script = script[start:end]

    assert (
        'homeList.className += " home-status-busy"'
        not in cover_action_script
    )


def test_home_cover_action_does_not_clear_global_busy_class():
    script = dashboard_js()

    start = script.index(
        "function performHomeCoverAction("
    )
    end = script.index(
        "window.performHomeCoverAction",
        start,
    )

    cover_action_script = script[start:end]

    assert (
        "home-status-busy"
        not in cover_action_script
    )







def test_home_cover_stop_is_not_stored_as_pending_action():
    script = dashboard_js()

    start = script.index(
        "function performHomeCoverAction("
    )
    end = script.index(
        "window.performHomeCoverAction",
        start,
    )

    cover_action_script = script[start:end]

    assert (
        'coverAction === "stop"'
        in cover_action_script
    )
    assert (
        'homeCoverLastAction[entityId] = "";'
        in cover_action_script
    )


def test_home_cover_stop_has_extended_press_feedback():
    script = dashboard_js()

    assert "setHomeCoverStopFeedback" in script
    assert "home-control-active" in script
    assert "500" in script


def test_home_cover_stop_feedback_does_not_use_pending_state():
    script = dashboard_js()

    start = script.index(
        "function setHomeCoverStopFeedback("
    )
    end = script.index(
        "function performHomeCoverAction(",
        start,
    )

    feedback_script = script[start:end]

    assert (
        "homeCoverLastAction"
        not in feedback_script
    )


def test_home_cover_remembers_last_known_state():
    script = dashboard_js()

    assert "homeCoverLastKnownState" in script
    assert "localStorage" in script


def test_home_cover_uses_last_known_state_when_unavailable():
    script = dashboard_js()

    assert (
        'item.raw_state === "unknown" ||'
        in script
    )
    assert (
        "homeCoverLastKnownState[item.entity_id]"
        in script
    )


def test_home_cover_updates_last_known_state_from_valid_state():
    script = dashboard_js()

    assert (
        "homeCoverLastKnownState[item.entity_id] ="
        in script
    )


def test_home_status_tracks_provider_revision():
    script = dashboard_js()

    assert "var homeStatusRevision = null;" in script
    assert "payload.revision" in script


def test_home_status_skips_render_for_unchanged_revision():
    script = dashboard_js()

    assert (
        "payload.revision === homeStatusRevision"
        in script
    )


def test_home_status_tracks_successful_render():
    script = dashboard_js()

    assert "var homeStatusHasData = false;" in script
    assert "homeStatusHasData = true;" in script


def test_home_status_preserves_existing_data_on_request_failure():
    script = dashboard_js()

    assert (
        "if (!homeStatusHasData)"
        in script
    )


def test_climate_row_with_inline_controls_is_not_whole_row_actionable():
    script = dashboard_js()

    assert (
        "hasDedicatedClimateControls"
        in script
    )

    assert (
        "resolvedAction &&"
        in script
    )

    assert (
        "!hasDedicatedClimateControls"
        in script
    )


def test_home_fan_and_hvac_pending_state_is_not_global():
    script = dashboard_js()

    fan_start = script.index(
        "function setHomeFanMode("
    )
    fan_end = script.index(
        "window.setHomeFanMode",
        fan_start,
    )
    fan_section = script[
        fan_start:fan_end
    ]

    hvac_start = script.index(
        "function setHomeHvacMode("
    )
    hvac_end = script.index(
        "window.setHomeHvacMode",
        hvac_start,
    )
    hvac_section = script[
        hvac_start:hvac_end
    ]

    assert (
        "clearHomeControlActive(homeList)"
        not in fan_section
    )

    assert (
        "clearHomeControlActive(homeList)"
        not in hvac_section
    )

    assert (
        "home-control-pending"
        not in fan_section
    )

    assert (
        "home-control-pending"
        not in hvac_section
    )


def test_home_light_uses_explicit_control_button_instead_of_whole_row():
    script = dashboard_js()

    assert (
        "hasDedicatedLightControl"
        in script
    )

    assert (
        "item.entity_id.indexOf("
        in script
    )

    assert (
        '"light."'
        in script
    )

    assert (
        "!hasDedicatedLightControl"
        in script
    )

    assert (
        "home-light-controls"
        in script
    )

    assert (
        "performHomeAction("
        in script
    )

    assert (
        "event.stopPropagation();"
        in script
    )


def test_home_light_buttons_use_explicit_on_and_off_actions():
    script = dashboard_js()

    start = script.index(
        "hasDedicatedLightControl &&"
    )

    end = script.index(
        "if (",
        start + 1,
    )

    section = script[start:end]

    assert "'turn_on'" in section
    assert "'turn_off'" in section

    assert ">开</button>" in section
    assert ">关</button>" in section


def test_home_light_controls_have_style():
    style = dashboard_css()

    assert ".home-light-controls" in style
    assert ".home-light-controls button" in style


def test_home_light_renders_both_on_and_off_controls():
    script = dashboard_js()

    start = script.index(
        "hasDedicatedLightControl &&"
    )

    end = script.index(
        "if (",
        start + 1,
    )

    section = script[start:end]

    assert "'turn_on'" in section
    assert "'turn_off'" in section

    assert ">开</button>" in section
    assert ">关</button>" in section


def test_home_light_marks_real_state_active():
    script = dashboard_js()

    start = script.index(
        "hasDedicatedLightControl &&"
    )

    end = script.index(
        "if (",
        start + 1,
    )

    section = script[start:end]

    assert 'item.raw_state === "on"' in section
    assert 'item.raw_state === "off"' in section
    assert "home-control-active" in section


def test_home_status_card_reads_provider_availability():
    script = dashboard_js()

    assert (
        "payload.available"
        in script
    )


def test_home_status_card_has_offline_notice_text():
    script = dashboard_js()

    assert (
        "Home Assistant 暂时离线"
        in script
    )

    assert (
        "最后一次已知状态"
        in script
    )


def test_home_status_card_keeps_cached_items_when_provider_is_offline():
    script = dashboard_js()

    assert (
        "payload.items || []"
        in script
    )

    assert (
        "payload.available === false"
        in script
    )


def test_home_status_refresh_considers_availability_change_with_same_revision():
    script = dashboard_js()

    assert (
        "homeStatusAvailable"
        in script
    )

    assert (
        "available === homeStatusAvailable"
        in script
    )


def test_initial_home_assistant_offline_can_render_notice_without_cached_items():
    script = dashboard_js()

    offline = script.index(
        "payload.available === false"
    )

    empty = script.index(
        "items.length === 0",
        offline,
    )

    assert offline < empty


def test_home_status_offline_notice_has_style():
    style = dashboard_css()

    assert ".home-status-offline" in style
