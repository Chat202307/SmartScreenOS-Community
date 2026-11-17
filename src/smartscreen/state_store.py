import copy, threading
from datetime import datetime, timezone
from .models import DeviceState

class StateStore:
    def __init__(self):
        self._lock=threading.RLock()
        self._states={}
    def initialize(self,device_id):
        with self._lock:
            self._states.setdefault(device_id,DeviceState(device_id=device_id))
    def update(self,device_id,available,state,attributes=None):
        with self._lock:
            self._states[device_id]=DeviceState(device_id=device_id,available=available,state=state,attributes=attributes or {},updated_at=datetime.now(timezone.utc).isoformat())
    def snapshot(self):
        with self._lock:
            return copy.deepcopy(self._states)
