from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_js():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def test_dashboard_has_update_status():
    html = dashboard_html()

    assert 'id="update-status"' in html


def test_dashboard_shows_updated_time():
    script = dashboard_js()

    assert "updated_at" in script
    assert "formatObservedAt" in script


def test_dashboard_formats_chinese_weekday():
    script = dashboard_js()

    assert "星期一" in script
    assert "星期二" in script
    assert "星期三" in script
    assert "星期四" in script
    assert "星期五" in script
    assert "星期六" in script
    assert "星期日" in script


def test_dashboard_has_connection_error_state():
    script = dashboard_js()

    assert "数据连接失败" in script


def test_dashboard_has_compact_freshness_indicator():
    html = dashboard_html()
    script = dashboard_js()

    assert (
        'class="update-status update-status-pending"'
        in html
    )
    assert "function setUpdateStatus" in script
    assert '"fresh"' in script
    assert '"error"' in script


def test_dashboard_keeps_legacy_browser_compatibility():
    script = dashboard_js()

    assert "XMLHttpRequest" in script
    assert "=>" not in script
    assert "const " not in script
    assert "let " not in script
