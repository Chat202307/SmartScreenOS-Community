from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]

DASHBOARD_JS = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "static"
    / "dashboard.js"
)


def dashboard_script():
    return DASHBOARD_JS.read_text(
        encoding="utf-8"
    )


def test_occupancy_renderer_reads_location_id():
    script = dashboard_script()

    start = script.index(
        "function renderOccupancyCard"
    )
    section = script[start:start + 900]

    assert "card.location_id" in section


def test_comfort_renderer_reads_location_id():
    script = dashboard_script()

    start = script.index(
        "function renderComfortCard"
    )
    section = script[start:start + 1100]

    assert "card.location_id" in section


def test_occupancy_renderer_appends_location_context():
    script = dashboard_script()

    start = script.index(
        "function renderOccupancyCard"
    )
    section = script[start:start + 1300]

    assert '" · " + displayLocation' in section


def test_comfort_renderer_appends_location_context():
    script = dashboard_script()

    start = script.index(
        "function renderComfortCard"
    )
    section = script[start:start + 1600]

    assert '" · " + displayLocation' in section


def test_location_context_is_optional():
    script = dashboard_script()

    assert "displayLocation" in script
    assert '? " · " + displayLocation' in (
        " ".join(script.split())
    )
    assert ': ""' in (
        " ".join(script.split())
    )


def test_location_context_does_not_add_separator_when_missing():
    script = dashboard_script()

    normalized = " ".join(script.split())

    assert (
        'displayLocation ? " · " + displayLocation : ""'
        in normalized
    )


def test_semantic_primary_labels_are_preserved():
    script = dashboard_script()

    assert '"当前有人"' in script
    assert '"当前无人"' in script
    assert '"舒适"' in script
    assert '"稍有不适"' in script
    assert '"不舒适"' in script


def test_occupancy_renderer_prefers_location_label():
    script = dashboard_script()

    start = script.index(
        "function renderOccupancyCard"
    )
    section = script[start:start + 1100]

    assert "card.location_label" in section
    assert "locationLabel || locationId" in section


def test_comfort_renderer_prefers_location_label():
    script = dashboard_script()

    start = script.index(
        "function renderComfortCard"
    )
    section = script[start:start + 1400]

    assert "card.location_label" in section
    assert "locationLabel || locationId" in section


def test_location_id_remains_fallback():
    script = dashboard_script()

    assert "locationLabel || locationId" in script


def test_location_context_remains_optional_without_label_or_id():
    script = dashboard_script()

    normalized = " ".join(script.split())

    assert (
        'displayLocation ? " · " + displayLocation : ""'
        in normalized
    )
