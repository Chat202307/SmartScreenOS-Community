from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_css():
    return (
        STATIC_DIR / "dashboard.css"
    ).read_text(encoding="utf-8")


def test_dashboard_has_card_container():
    html = dashboard_html()

    assert 'class="dashboard-cards"' in html


def test_dashboard_has_card():
    html = dashboard_html()

    assert 'class="dashboard-card"' in html


def test_dashboard_card_has_title():
    html = dashboard_html()

    assert 'class="dashboard-card-title"' in html


def test_dashboard_card_has_body():
    html = dashboard_html()

    assert 'class="dashboard-card-body"' in html


def test_dashboard_cards_have_layout():
    css = dashboard_css()

    assert ".dashboard-cards" in css
    assert ".dashboard-card" in css


def test_dashboard_card_title_has_style():
    css = dashboard_css()

    assert ".dashboard-card-title" in css


def test_dashboard_card_body_has_style():
    css = dashboard_css()

    assert ".dashboard-card-body" in css
