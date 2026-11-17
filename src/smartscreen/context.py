class ContextEngine:
    def __init__(self, house_model):
        self._house = house_model

    def snapshot(self):
        house = self._house.snapshot()
        rooms = [self._room_context(room) for room in house["rooms"]]
        return {
            "generated_at": house["generated_at"],
            "home": {
                "name": house["home"]["name"],
                "status": house["home"]["status"],
                "summary": self._home_summary(house["home"], rooms),
            },
            "rooms": rooms,
        }

    def room(self, room_id):
        for room in self.snapshot()["rooms"]:
            if room["id"] == room_id:
                return room
        return None

    def _room_context(self, room):
        devices = room["devices"]
        presence = self._presence(devices)
        climate = self._climate(devices)
        lighting = self._lighting(devices)
        privacy = self._privacy(devices)
        connectivity = self._connectivity(room)
        activity = self._activity(room, presence)
        comfort = self._comfort(climate, connectivity)

        return {
            "id": room["id"],
            "name": room["name"],
            "presence": presence,
            "comfort": comfort,
            "lighting": lighting,
            "climate": climate,
            "privacy": privacy,
            "activity": activity,
            "connectivity": connectivity,
            "temperature": self._temperature(devices),
            "summary": self._summary(
                room["name"], presence, comfort, lighting,
                privacy, activity, connectivity
            ),
            "last_activity": room.get("last_activity"),
        }

    @staticmethod
    def _presence(devices):
        items = [d for d in devices if d["type"] == "occupancy"]
        if not items:
            return "unknown"
        if any(d["available"] and d["state"] == "on" for d in items):
            return "occupied"
        if all(d["available"] for d in items):
            return "vacant"
        return "unknown"

    @staticmethod
    def _climate(devices):
        items = [d for d in devices if d["type"] == "climate" and d["available"]]
        if not items:
            return "unknown"
        state = items[0]["state"]
        return {
            "cool": "cool",
            "heat": "warm",
            "off": "neutral",
        }.get(state, "unknown")

    @staticmethod
    def _temperature(devices):
        for device in devices:
            if device["type"] == "climate" and device["available"]:
                value = (device.get("attributes") or {}).get("current_temperature")
                if value is not None:
                    return value
        return None

    @staticmethod
    def _lighting(devices):
        items = [d for d in devices if d["type"] == "light" and d["available"]]
        if not items:
            return "unknown"
        return "bright" if any(d["state"] == "on" for d in items) else "dim"

    @staticmethod
    def _privacy(devices):
        items = [d for d in devices if d["type"] == "curtain" and d["available"]]
        if not items:
            return "unknown"
        if any(d["state"] in ("open","opening","stopped") for d in items):
            return "open"
        if all(d["state"] in ("closed","closing") for d in items):
            return "closed"
        return "unknown"

    @staticmethod
    def _connectivity(room):
        if room["device_count"] == 0:
            return "empty"
        if room["available_devices"] == 0:
            return "offline"
        if room["unavailable_devices"] > 0:
            return "partial"
        return "healthy"

    @staticmethod
    def _activity(room, presence):
        if room["device_count"] == 0:
            return "empty"
        if presence == "occupied" or room["active_devices"] > 0:
            return "active"
        if room["status"] == "offline":
            return "unknown"
        return "quiet"

    @staticmethod
    def _comfort(climate, connectivity):
        if connectivity in ("offline","partial"):
            return "unknown"
        return "good" if climate in ("cool","warm","neutral") else "unknown"

    @staticmethod
    def _summary(name, presence, comfort, lighting, privacy, activity, connectivity):
        if connectivity == "empty":
            return name + "尚未配置设备。"
        if connectivity == "offline":
            return name + "暂时无法获取最新状态。"
        if connectivity == "partial":
            return name + "有部分设备暂时无法连接。"

        parts = []
        if presence == "occupied":
            parts.append("有人活动")
        elif activity == "quiet":
            parts.append("很安静")
        if comfort == "good":
            parts.append("环境舒适")
        if lighting == "bright":
            parts.append("照明已开启")
        elif lighting == "dim":
            parts.append("照明关闭")
        if privacy == "open":
            parts.append("窗帘打开")
        elif privacy == "closed":
            parts.append("窗帘关闭")

        return name + "，" + "，".join(parts) + "。" if parts else name + "状态正常。"

    @staticmethod
    def _home_summary(home, rooms):
        if home["status"] == "healthy":
            active = sum(1 for room in rooms if room["activity"] == "active")
            return "家中有 %d 个房间正在活动。" % active if active else "家里很安静，一切正常。"
        unavailable = home["unavailable_devices"]
        return "有 %d 个设备暂时无法连接。" % unavailable if unavailable else "正在更新家庭状态。"
