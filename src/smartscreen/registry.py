"""Room and device registries."""

from .device_types import validate_device_type


class RegistryError(ValueError):
    pass


class RoomRegistry:
    def __init__(self, rooms):
        self._rooms = {}

        for room in rooms:
            if room.id in self._rooms:
                raise RegistryError(f"Duplicate room id: {room.id}")
            self._rooms[room.id] = room

    def all(self):
        return sorted(self._rooms.values(), key=lambda item: item.order)

    def contains(self, room_id):
        return room_id in self._rooms


class DeviceRegistry:
    def __init__(self, devices, rooms):
        self._devices = {}

        for device in devices:
            if device.id in self._devices:
                raise RegistryError(f"Duplicate device id: {device.id}")

            if not rooms.contains(device.room):
                raise RegistryError(
                    f"Device {device.id} references unknown room: {device.room}"
                )

            validate_device_type(device.type, device.capabilities)
            self._devices[device.id] = device

    def all(self):
        return list(self._devices.values())

    def get(self, device_id):
        return self._devices.get(device_id)

    def by_room(self, room_id):
        return [
            device
            for device in self._devices.values()
            if device.room == room_id
        ]
