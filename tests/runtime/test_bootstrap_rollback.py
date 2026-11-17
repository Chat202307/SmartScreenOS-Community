import pytest

from src.smartscreen_runtime.runtime.bootstrap import (
    RuntimeBootstrapError,
    create_runtime_host,
)


def test_missing_path_is_rejected():
    with pytest.raises(RuntimeBootstrapError, match="path"):
        create_runtime_host(
            capabilities=[
                {
                    "session_id": "session-clock-main",
                }
            ]
        )


def test_missing_session_id_is_rejected():
    with pytest.raises(RuntimeBootstrapError, match="session_id"):
        create_runtime_host(
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                }
            ]
        )


def test_invalid_configuration_type_is_rejected():
    with pytest.raises(RuntimeBootstrapError, match="configuration"):
        create_runtime_host(
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                    "session_id": "session-clock-main",
                    "configuration": "invalid",
                }
            ]
        )


def test_duplicate_session_id_is_rejected():
    with pytest.raises(RuntimeBootstrapError, match="duplicate"):
        create_runtime_host(
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                    "session_id": "session-main",
                },
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-main",
                    "configuration": {
                        "location": "Dalian",
                    },
                },
            ]
        )


def test_bootstrap_rolls_back_when_later_capability_fails():
    with pytest.raises(RuntimeBootstrapError):
        create_runtime_host(
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                    "session_id": "session-clock-main",
                },
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                },
            ]
        )


def test_bootstrap_error_preserves_original_cause():
    with pytest.raises(RuntimeBootstrapError) as exc_info:
        create_runtime_host(
            capabilities=[
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                }
            ]
        )

    assert exc_info.value.__cause__ is not None
