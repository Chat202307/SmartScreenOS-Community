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


def test_dashboard_has_photo_card():
    html = dashboard_html()

    assert 'id="photo-card"' in html
    assert "照片" in html


def test_dashboard_has_photo_image():
    html = dashboard_html()

    assert 'id="photo-image"' in html
    assert "<img" in html


def test_dashboard_requests_photo_library():
    script = dashboard_js()

    assert '"/api/photos"' in script
    assert "XMLHttpRequest" in script


def test_dashboard_reads_photo_url():
    script = dashboard_js()

    assert "photoList[photoIndex].url" in script


def test_dashboard_sets_photo_source():
    script = dashboard_js()

    assert 'getElementById("photo-image")' in script
    assert ".src" in script


def test_dashboard_handles_empty_photo_library():
    script = dashboard_js()

    assert "暂无照片" in script


def test_photo_card_has_layout():
    css = dashboard_css()

    assert "#photo-card" in css
    assert "#photo-image" in css


def test_photo_image_preserves_aspect_ratio():
    css = dashboard_css()

    assert "max-width:" in css
    assert "max-height:" in css
