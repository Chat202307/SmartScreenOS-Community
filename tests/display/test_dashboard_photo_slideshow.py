from pathlib import Path


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_js():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def test_slideshow_tracks_photo_list():
    script = dashboard_js()

    assert "photoList" in script


def test_slideshow_tracks_current_index():
    script = dashboard_js()

    assert "photoIndex" in script


def test_slideshow_advances_photo_index():
    script = dashboard_js()

    assert "photoIndex + 1" in script


def test_slideshow_wraps_at_end():
    script = dashboard_js()

    assert "% photoList.length" in script


def test_slideshow_updates_image_source():
    script = dashboard_js()

    assert "photoList[photoIndex].url" in script


def test_slideshow_has_rotation_function():
    script = dashboard_js()

    assert "function showNextPhoto()" in script


def test_slideshow_uses_timer():
    script = dashboard_js()

    assert "setInterval(showNextPhoto" in script


def test_slideshow_does_not_rotate_single_photo():
    script = dashboard_js()

    assert "photoList.length <= 1" in script
