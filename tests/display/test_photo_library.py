import json

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {}


def create_app(photo_dir):
    return SnapshotApplication(
        FakeHost(),
        photo_dir=photo_dir,
    )


def test_photo_library_lists_jpeg(tmp_path):
    (tmp_path / "family.jpg").write_bytes(b"jpg")

    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/api/photos",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert payload == {
        "photos": [
            {
                "name": "family.jpg",
                "url": "/photos/family.jpg",
            }
        ]
    }


def test_photo_library_lists_supported_formats(tmp_path):
    (tmp_path / "one.JPG").write_bytes(b"jpg")
    (tmp_path / "two.jpeg").write_bytes(b"jpeg")
    (tmp_path / "three.png").write_bytes(b"png")
    (tmp_path / "notes.txt").write_text("ignore")

    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/api/photos",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200

    names = [
        photo["name"]
        for photo in payload["photos"]
    ]

    assert names == [
        "one.JPG",
        "three.png",
        "two.jpeg",
    ]


def test_photo_library_ignores_directories(tmp_path):
    (tmp_path / "album.jpg").mkdir()
    (tmp_path / "photo.jpg").write_bytes(b"jpg")

    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/api/photos",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert len(payload["photos"]) == 1
    assert payload["photos"][0]["name"] == "photo.jpg"


def test_photo_library_returns_empty_list(tmp_path):
    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="GET",
        path="/api/photos",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload == {"photos": []}


def test_photo_library_is_read_only(tmp_path):
    app = create_app(tmp_path)

    status, headers, body = app.handle(
        method="POST",
        path="/api/photos",
    )

    assert status == 405
    assert headers["Allow"] == "GET"
