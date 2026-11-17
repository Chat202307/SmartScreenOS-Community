"""Actual production JS functions run with fake XHR/clock/DOM; no real services."""
import json
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[2]
SCENARIOS=[
 'cold_syncing','cold_failure_then_empty_recovery','cached_syncing',
 'fault_and_automatic_recovery','transport_error','timeout_late_response',
 'single_inflight','malformed_json','invalid_events','stale_200','server_cache_age',
 'eventkit_legacy_and_old_safari','rollover_retains_only_overlapping_events',
 'late_previous_day_response','fresh_empty','unknown_server_state',
 'independent_from_snapshot','send_failure','stale_header',
 'escaped_title_and_private_error','bounded_retry_hint','server_clock_overrides_device_drift','no_events_field_is_failure',
]

@pytest.mark.parametrize('scenario',SCENARIOS)
def test_calendar_js_state_transitions(scenario):
    node=shutil.which('node')
    assert node,'Node is required for calendar UI behavior tests'
    result=subprocess.run([node,str(Path(__file__).with_name('calendar_ui_runner.cjs')),
        str(ROOT/'src/smartscreen_display/static/dashboard.js'),scenario],
        capture_output=True,text=True,timeout=15,env={'PATH':str(Path(node).parent),'TZ':'Asia/Shanghai'})
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==dict(scenario=scenario,passed=True)
