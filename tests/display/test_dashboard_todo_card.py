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


def test_dashboard_has_todo_card():
    html = dashboard_html()

    assert 'id="todo-card"' in html
    assert "待办" in html


def test_dashboard_has_todo_list():
    html = dashboard_html()

    assert 'id="todo-list"' in html


def test_dashboard_requests_todo_api():
    script = dashboard_js()

    assert '"/api/todos"' in script
    assert "XMLHttpRequest" in script


def test_dashboard_reads_todos():
    script = dashboard_js()

    assert "payload.todos" in script


def test_dashboard_renders_todo_title():
    script = dashboard_js()

    assert "todo.title" in script


def test_dashboard_handles_empty_todos():
    script = dashboard_js()

    assert "暂无待办" in script


def test_todo_card_has_layout():
    css = dashboard_css()

    assert "#todo-card" in css
    assert "#todo-list" in css


def test_completed_todo_has_style():
    css = dashboard_css()

    assert ".todo-completed" in css


def test_todo_conflict_refreshes_when_no_edit_is_active():
    script = dashboard_js()

    conflict_start = script.index(
        "} else if (request.status === 409) {"
    )
    conflict_end = script.index(
        "} else {",
        conflict_start + 1,
    )
    conflict = script[
        conflict_start:conflict_end
    ]

    assert "todoRevision = null;" in conflict
    assert "if (!todoEditId)" in conflict
    assert "updateTodoCard();" in conflict


def test_todo_home_summary_shows_at_most_two_items():
    script = dashboard_js()

    assert "Math.min(pending.length, 2)" in script


def test_todo_overlay_has_bounded_scroll_container():
    css = dashboard_css()

    panel_start = css.index(".todo-overlay-panel {")
    panel_end = css.index("}", panel_start)
    panel = css[panel_start:panel_end]

    content_start = css.index(".todo-overlay-content {")
    content_end = css.index("}", content_start)
    content = css[content_start:content_end]

    assert "display: flex;" in panel
    assert "flex-direction: column;" in panel
    assert "min-height: 0;" in content
    assert "overflow-y: auto;" in content


def test_todo_overlay_close_clears_card_focus():
    script = dashboard_js()

    close_start = script.index("function closeTodoOverlay()")
    bind_start = script.index("function bindTodos()", close_start)
    close_function = script[close_start:bind_start]

    assert "card.blur();" in close_function


def test_todo_overlay_uses_native_button_backdrop():
    from src.smartscreen_display.dashboard import (
        DASHBOARD_HTML,
    )

    html = DASHBOARD_HTML.decode("utf-8")

    assert (
        '<button\n'
        '      type="button"\n'
        '      class="todo-overlay-backdrop"\n'
        '      data-todo-close\n'
        '      aria-label="关闭待办事项"\n'
        '    ></button>'
        in html
    )


def test_todo_backdrop_does_not_need_touch_workaround():
    script = dashboard_js()

    bind_start = script.index("function bindTodos()")
    bind_end = script.index(
        "document.getElementById('todo-add-form')",
        bind_start,
    )
    binding = script[bind_start:bind_end]

    assert (
        "document.querySelector('.todo-overlay-backdrop')"
        not in binding
    )
    assert "backdrop.ontouchstart" not in binding
