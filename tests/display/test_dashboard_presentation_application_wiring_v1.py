import json

from src.smartscreen_display.application import (
    run_display_server,
)


class FakeRuntime:
    def start_background(self):
        pass

    def stop(self):
        pass

    def join(self, timeout=None):
        pass


class FakeServer:
    def serve_forever(self):
        pass

    def shutdown(self):
        pass

    def server_close(self):
        pass


def test_application_wires_dashboard_presentation_config(
    monkeypatch,
    tmp_path,
):
    captured = {}

    presentation_config = (
        tmp_path / "dashboard_presentation.json"
    )

    presentation_config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "areas": [
                    {
                        "id": "home_kitchen",
                        "label": "厨房",
                        "member_location_ids": [
                            "kitchen",
                        ],
                        "summary_location_id":
                            "open_public_area",
                        "order": 10,
                    },
                    {
                        "id": "home_living_dining",
                        "label": "客餐厅",
                        "member_location_ids": [
                            "living",
                            "dining",
                        ],
                        "summary_location_id":
                            "open_public_area",
                        "order": 20,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class FakePresentationBuilder:
        def __init__(
            self,
            *,
            location_labels=None,
            location_orders=None,
            location_zones=None,
        ):
            captured["labels"] = dict(
                location_labels or {}
            )
            captured["orders"] = dict(
                location_orders or {}
            )
            captured["zones"] = dict(
                location_zones or {}
            )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DashboardPresentationBuilder",
        FakePresentationBuilder,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        dashboard_presentation_file=(
            presentation_config
        ),
    )

    assert captured["labels"][
        "home_kitchen"
    ] == "厨房"

    assert captured["labels"][
        "home_living_dining"
    ] == "客餐厅"

    assert captured["orders"][
        "home_kitchen"
    ] == 10

    assert captured["orders"][
        "home_living_dining"
    ] == 20

    assert captured["zones"][
        "home_kitchen"
    ] == {
        "room_ids": (
            "kitchen",
        ),
        "summary_location_id":
            "open_public_area",
        "show_on_home": True,
        "sheet_extra_device_ids": (),
        "sheet_device_order": (),
        "sheet_wide_device_ids": (),
    }

    assert captured["zones"][
        "home_living_dining"
    ] == {
        "room_ids": (
            "living",
            "dining",
        ),
        "summary_location_id":
            "open_public_area",
        "show_on_home": True,
        "sheet_extra_device_ids": (),
        "sheet_device_order": (),
        "sheet_wide_device_ids": (),
    }
