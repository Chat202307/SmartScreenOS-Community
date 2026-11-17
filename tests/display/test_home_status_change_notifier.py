import threading

from src.smartscreen_display.home_status_change_notifier import (
    HomeStatusChangeNotifier,
)


def test_notifier_starts_at_revision_zero():
    notifier = HomeStatusChangeNotifier()

    assert notifier.revision == 0


def test_notifier_notify_sets_revision():
    notifier = HomeStatusChangeNotifier()

    notifier.notify(1)

    assert notifier.revision == 1

    notifier.notify(2)

    assert notifier.revision == 2


def test_notifier_wait_returns_after_change():
    notifier = HomeStatusChangeNotifier()

    result = []

    def wait_for_change():
        result.append(
            notifier.wait_for_change(
                0,
                timeout=1.0,
            )
        )

    thread = threading.Thread(
        target=wait_for_change
    )

    thread.start()

    notifier.notify(1)

    thread.join(timeout=1.0)

    assert thread.is_alive() is False
    assert result == [1]


def test_notifier_wait_times_out_without_change():
    notifier = HomeStatusChangeNotifier()

    revision = notifier.wait_for_change(
        0,
        timeout=0.01,
    )

    assert revision == 0


def test_home_status_change_notifier_accepts_revision():
    notifier = HomeStatusChangeNotifier()

    result = notifier.notify(7)

    assert result == 7
    assert notifier.revision == 7


def test_home_status_change_notifier_tracks_provider_revision_exactly():
    notifier = HomeStatusChangeNotifier()

    notifier.notify(7)
    notifier.notify(12)

    assert notifier.revision == 12


def test_home_status_change_notifier_ignores_duplicate_revision():
    notifier = HomeStatusChangeNotifier()

    notifier.notify(7)
    notifier.notify(7)

    assert notifier.revision == 7


def test_home_status_change_notifier_wait_returns_supplied_revision():
    notifier = HomeStatusChangeNotifier()

    notifier.notify(23)

    result = notifier.wait_for_change(
        0,
        timeout=0,
    )

    assert result == 23
