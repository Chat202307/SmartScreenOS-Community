import json
from typing import Any

from .base import AdapterError, BaseAdapter


class MqttAdapter(BaseAdapter):
    adapter_id = "mqtt"

    def __init__(
        self,
        state_callback,
        devices,
        settings,
        connection_manager=None,
        event_bus=None,
    ):
        super().__init__(state_callback)
        self._devices = list(devices)
        self._settings = settings
        self._connection_manager = connection_manager
        self._event_bus = event_bus
        self._running = False
        self._connected = False
        self._client = None
        self._topic_to_device = {}

        for device in self._devices:
            topic = device.adapter_config.get("state_topic")
            if topic:
                self._topic_to_device[topic] = device

        if self._connection_manager is not None:
            self._connection_manager.register("mqtt")

    def _emit(self, name, payload=None):
        if self._event_bus is not None:
            self._event_bus.publish(
                name,
                source="mqtt",
                payload=payload or {},
            )

    def start(self):
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise AdapterError(
                "paho-mqtt is not installed. "
                "Install it with: python3 -m pip install paho-mqtt"
            ) from exc

        if self._connection_manager is not None:
            self._connection_manager.set_state(
                "mqtt",
                "connecting",
            )

        self._emit("adapter.connecting", {"adapter": "mqtt"})

        callback_api = getattr(mqtt, "CallbackAPIVersion", None)
        if callback_api is not None:
            self._client = mqtt.Client(callback_api.VERSION2)
        else:
            self._client = mqtt.Client()

        username = str(self._settings.get("username", "")).strip()
        password = str(self._settings.get("password", ""))

        if username:
            self._client.username_pw_set(username, password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        host = str(self._settings.get("host", "127.0.0.1"))
        port = int(self._settings.get("port", 1883))
        keepalive = int(self._settings.get("keepalive", 60))

        self._running = True
        self._client.reconnect_delay_set(
            min_delay=2,
            max_delay=60,
        )
        self._client.connect(host, port, keepalive)
        self._client.loop_start()

    def stop(self):
        self._running = False

        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            finally:
                self._client = None

        self._connected = False

        if self._connection_manager is not None:
            self._connection_manager.set_state(
                "mqtt",
                "disconnected",
                "stopped",
            )

        self._emit(
            "adapter.disconnected",
            {
                "adapter": "mqtt",
                "reason": "stopped",
            },
        )

    def health(self):
        result = {
            "adapter_id": self.adapter_id,
            "running": self._running,
            "connected": self._connected,
            "read_only": bool(
                self._settings.get("read_only", True)
            ),
            "subscription_count": len(self._topic_to_device),
        }

        if self._connection_manager is not None:
            snapshot = self._connection_manager.snapshot()
            result["connection"] = snapshot[
                "connections"
            ].get("mqtt", {})

        return result

    def send_command(
        self,
        device_id: str,
        command: str,
        value: Any = None,
    ):
        if bool(self._settings.get("read_only", True)):
            raise AdapterError(
                "MQTT Adapter is in read-only mode. "
                "Commands are disabled."
            )

        raise AdapterError(
            "MQTT command publishing is not implemented."
        )

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties=None,
    ):
        self._connected = True

        if self._connection_manager is not None:
            self._connection_manager.set_state(
                "mqtt",
                "connected",
                str(reason_code),
            )

        self._emit(
            "adapter.connected",
            {
                "adapter": "mqtt",
                "reason": str(reason_code),
            },
        )

        print("[MQTT] Connected:", reason_code)

        for topic in sorted(self._topic_to_device):
            client.subscribe(topic)
            print("[MQTT] Subscribed:", topic)

    def _on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags=None,
        reason_code=None,
        properties=None,
    ):
        self._connected = False

        if self._connection_manager is not None:
            self._connection_manager.set_state(
                "mqtt",
                "reconnecting",
                str(reason_code),
            )

        self._emit(
            "adapter.reconnecting",
            {
                "adapter": "mqtt",
                "reason": str(reason_code),
            },
        )

        print("[MQTT] Disconnected:", reason_code)

    def _on_message(self, client, userdata, message):
        device = self._topic_to_device.get(message.topic)
        if device is None:
            return

        if self._connection_manager is not None:
            self._connection_manager.mark_message("mqtt")

        raw = message.payload.decode(
            "utf-8",
            errors="replace",
        ).strip()

        self._emit(
            "adapter.message_received",
            {
                "adapter": "mqtt",
                "topic": message.topic,
                "device_id": device.id,
            },
        )

        try:
            normalized = self._normalize(
                device.type,
                raw,
            )
        except Exception as exc:
            self._emit(
                "adapter.normalize_failed",
                {
                    "adapter": "mqtt",
                    "topic": message.topic,
                    "device_id": device.id,
                    "error": str(exc),
                },
            )
            print(
                "[MQTT] Normalize failed:",
                device.id,
                repr(raw),
                exc,
            )
            return

        self.publish_state(
            device.id,
            available=True,
            state=normalized["state"],
            attributes=normalized["attributes"],
        )

        print(
            "[MQTT STATE]",
            device.id,
            normalized["state"],
            normalized["attributes"],
        )

    @staticmethod
    def _normalize(device_type, raw):
        if device_type == "light":
            value = raw.upper()

            if value == "ON":
                return {
                    "state": "on",
                    "attributes": {},
                }

            if value == "OFF":
                return {
                    "state": "off",
                    "attributes": {},
                }

            return {
                "state": "unknown",
                "attributes": {"raw": raw},
            }

        if device_type == "curtain":
            value = raw.upper()
            states = {
                "OPEN": "open",
                "OPENING": "opening",
                "CLOSE": "closed",
                "CLOSED": "closed",
                "CLOSING": "closing",
                "STOP": "stopped",
                "STOPPED": "stopped",
            }

            return {
                "state": states.get(value, "unknown"),
                "attributes": {"raw": raw},
            }

        if device_type == "climate":
            data = json.loads(raw)
            power = str(
                data.get("power", "UNKNOWN")
            ).upper()
            mode = str(
                data.get("mode", "UNKNOWN")
            ).upper()

            if power == "OFF":
                state = "off"
            elif mode == "COOL":
                state = "cool"
            elif mode == "HEAT":
                state = "heat"
            else:
                state = "unknown"

            return {
                "state": state,
                "attributes": {
                    "power": power.lower(),
                    "mode": mode.lower(),
                    "target_temperature": data.get(
                        "temp_set"
                    ),
                    "current_temperature": data.get(
                        "temp_room"
                    ),
                    "fan_mode": str(
                        data.get("fan", "UNKNOWN")
                    ).lower(),
                    "fan_raw": data.get("fan_raw"),
                    "swing_mode": str(
                        data.get("swing", "UNKNOWN")
                    ).lower(),
                    "swing_raw": data.get("swing_raw"),
                },
            }

        return {
            "state": "unknown",
            "attributes": {"raw": raw},
        }
