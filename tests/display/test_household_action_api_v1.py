import json

from src.smartscreen_display.server import (
    SnapshotApplication,
)


class FakeHost:
    def snapshot(self):
        return {
            "capabilities": {},
        }


class FakeHouseholdActionExecutor:
    def __init__(
        self,
        *,
        result=None,
        error=None,
    ):
        self.calls = []
        self.result = result
        self.error = error

    def execute(self, action_id):
        self.calls.append(action_id)

        if self.error is not None:
            raise ValueError(
                self.error
            )

        return (
            self.result
            if self.result is not None
            else {
                "action_id": action_id,
                "status": "success",
                "succeeded_device_ids": [],
                "failures": [],
            }
        )


def create_app(executor=None):
    return SnapshotApplication(
        FakeHost(),
        household_action_executor=executor,
    )


def test_household_action_api_executes_action():
    executor = (
        FakeHouseholdActionExecutor()
    )

    app = create_app(executor)

    status, _, body = app.handle(
        method="POST",
        path="/api/household/actions",
        body=json.dumps(
            {
                "action_id":
                    "all_lights_off",
            }
        ).encode("utf-8"),
    )

    assert status == 200

    assert executor.calls == [
        "all_lights_off"
    ]

    assert json.loads(
        body.decode("utf-8")
    ) == {
        "action_id":
            "all_lights_off",
        "status": "success",
        "succeeded_device_ids": [],
        "failures": [],
    }


def test_household_action_api_preserves_partial_failure():
    result = {
        "action_id":
            "all_lights_off",
        "status":
            "partial_failure",
        "succeeded_device_ids": [
            "corridor.light_1",
        ],
        "failures": [
            {
                "device_id":
                    "kitchen.light_1",
                "error":
                    "device unavailable",
            },
        ],
    }

    app = create_app(
        FakeHouseholdActionExecutor(
            result=result
        )
    )

    status, _, body = app.handle(
        method="POST",
        path="/api/household/actions",
        body=json.dumps(
            {
                "action_id":
                    "all_lights_off",
            }
        ).encode("utf-8"),
    )

    assert status == 200

    assert json.loads(
        body.decode("utf-8")
    ) == result


def test_household_action_api_requires_executor():
    app = create_app()

    status, _, body = app.handle(
        method="POST",
        path="/api/household/actions",
        body=json.dumps(
            {
                "action_id":
                    "all_lights_off",
            }
        ).encode("utf-8"),
    )

    assert status == 503

    assert (
        "household action executor"
        in json.loads(
            body.decode("utf-8")
        )["error"]
    )


def test_household_action_api_requires_action_id():
    app = create_app(
        FakeHouseholdActionExecutor()
    )

    status, _, body = app.handle(
        method="POST",
        path="/api/household/actions",
        body=b"{}",
    )

    assert status == 400

    assert json.loads(
        body.decode("utf-8")
    ) == {
        "error":
            "action_id required",
    }


def test_household_action_api_rejects_unknown_action():
    executor = (
        FakeHouseholdActionExecutor(
            error=(
                "unknown household action: "
                "unknown"
            )
        )
    )

    app = create_app(executor)

    status, _, body = app.handle(
        method="POST",
        path="/api/household/actions",
        body=json.dumps(
            {
                "action_id":
                    "unknown",
            }
        ).encode("utf-8"),
    )

    assert status == 400

    assert (
        "unknown household action"
        in json.loads(
            body.decode("utf-8")
        )["error"]
    )


def test_household_action_api_rejects_invalid_json():
    app = create_app(
        FakeHouseholdActionExecutor()
    )

    status, _, body = app.handle(
        method="POST",
        path="/api/household/actions",
        body=b"{not-json",
    )

    assert status == 400

    assert json.loads(
        body.decode("utf-8")
    ) == {
        "error": "invalid json",
    }


def test_household_action_api_rejects_non_post():
    app = create_app(
        FakeHouseholdActionExecutor()
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/household/actions",
        body=b"",
    )

    assert status == 405
    assert headers["Allow"] == "POST"

    assert json.loads(
        body.decode("utf-8")
    ) == {
        "error":
            "method not allowed",
    }
