from pathlib import Path

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {}


def create_app(photo_dir):
    return SnapshotApplication(
        FakeHost(),
        photo_dir=photo_dir,
    )


def test_photo_is_served(tmp_path):
    photo = tmp_path / "family.jpg"
    photo.write_bytes(b"fake-jpeg")

    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/photos/family.jpg",
    )

    assert status == 200
    assert headers["Content-Type"] == "image/jpeg"
    assert body == b"fake-jpeg"


def test_png_photo_is_served(tmp_path):
    photo = tmp_path / "screen.png"
    photo.write_bytes(b"fake-png")

    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/photos/screen.png",
    )

    assert status == 200
    assert headers["Content-Type"] == "image/png"
    assert body == b"fake-png"


def test_missing_photo_returns_404(tmp_path):
    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/photos/missing.jpg",
    )

    assert status == 404


def test_photo_endpoint_is_read_only(tmp_path):
    photo = tmp_path / "family.jpg"
    photo.write_bytes(b"fake-jpeg")

    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="POST",
        path="/photos/family.jpg",
    )

    assert status == 405


def test_photo_path_cannot_escape_photo_directory(tmp_path):
    outside = tmp_path.parent / "secret.jpg"
    outside.write_bytes(b"secret")

    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/photos/../secret.jpg",
    )

    assert status == 404
