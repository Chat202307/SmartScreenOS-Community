import json

from src.smartscreen_display.application import (
    run_display_server,
)


class FakeRuntime:
    def snapshot(self):
        return {}

    def start_background(self):
        pass

    def stop(self):
        pass

    def join(self, timeout=None):
        pass


class FakeHouseholdState:
    def snapshot(self):
        return [
            {
                "target": "occupancy",
                "value": {
                    "state": "occupied",
                    "count": None,
                },
                "confidence": 0.9,
                "location_id": "living",
                "evidence_refs": [],
                "metadata": {},
            }
        ]


class FakeServer:
    def serve_forever(self):
        return None

    def server_close(self):
        pass


def test_configured_rooms_survive_into_dashboard_presentation(
    tmp_path,
):
    home_config = tmp_path / "home.json"

    home_config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rooms": [
                    {
                        "id": "living",
                        "name": "家庭活动室",
                        "order": 20,
                    },
                    {
                        "id": "study",
                        "name": "阅读室",
                        "order": 10,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    device_config = (
        tmp_path / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": []
}
""".strip(),
        encoding="utf-8",
    )

    captured = {}

    def server_factory(
        app,
        *,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app
        return FakeServer()

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=server_factory,
        household_state_source=FakeHouseholdState(),
        home_file="home-status.json",
        location_config_file=home_config,
        device_data_file=device_config,
    )

    app = captured["app"]

    status, headers, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200

    assert payload["locations"] == [
        {
            "location_id": "study",
            "has_semantic_data": False,
            "semantic_targets": [],
            "location_label": "阅读室",
            "location_order": 10,
        },
        {
            "location_id": "living",
            "has_semantic_data": True,
            "semantic_targets": [
                "occupancy",
            ],
            "location_label": "家庭活动室",
            "location_order": 20,
        },
    ]

    assert payload["cards"][0][
        "location_id"
    ] == "living"

    assert payload["cards"][0][
        "location_label"
    ] == "家庭活动室"
