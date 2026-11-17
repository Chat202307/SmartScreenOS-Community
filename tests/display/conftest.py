"""Display tests use an isolated MQTT transport, never the household broker."""
from unittest.mock import Mock

import paho.mqtt.client as mqtt
import pytest


@pytest.fixture(autouse=True)
def isolate_default_mqtt_transport(monkeypatch):
    # Wiring tests may override this constructor with their own recording fake.
    # Keep the real source lifecycle and adapters; isolate only network I/O.
    client = Mock(spec=mqtt.Client)
    client.publish.side_effect = AssertionError(
        "Control tests must provide an explicit recording MQTT client"
    )
    monkeypatch.setattr(
        "src.smartscreen_display.application.DnakeMqttClient",
        lambda *args, **kwargs: client,
    )
    return client
