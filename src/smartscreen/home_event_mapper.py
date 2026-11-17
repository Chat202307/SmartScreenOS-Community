from .home_event import HomeEvent

class HomeEventMapper:
    def __init__(self, devices):
        self._devices = devices

    def from_device_state(self, device_id, available, state, attributes, previous=None, current=None, source='adapter'):
        device = self._devices.get(device_id)
        return HomeEvent.create(
            event_type='home.device.state_changed',
            source=source,
            room_id=device.room if device is not None else None,
            device_id=device_id,
            payload={
                'available': bool(available),
                'state': str(state),
                'attributes': dict(attributes or {}),
                'previous': previous,
                'current': current,
            },
        )

    @staticmethod
    def from_adapter_event(event_type, adapter, payload=None):
        return HomeEvent.create(
            event_type='home.adapter.' + str(event_type),
            source=str(adapter),
            payload=dict(payload or {}),
        )
