import unittest
from src.smartscreen.diagnostics import DiagnosticsEngine
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore

class A:
    def health(self):
        return {"mqtt":{"running":True,"connected":True}}
class C:
    def __init__(self): self.adapters=A()

class DiagnosticsTests(unittest.TestCase):
    def test_snapshot(self):
        rooms=RoomRegistry([Room("living","客厅","public_area",1)])
        devices=DeviceRegistry([Device("living.light","客厅灯","living","light","mqtt",["turn_on","turn_off"])],rooms)
        states=StateStore(); states.initialize("living.light")
        states.update("living.light",available=True,state="off",attributes={})
        p=DiagnosticsEngine(C(),devices,states).snapshot()
        self.assertEqual(p["overall"],"healthy")
        self.assertEqual(p["devices"]["available"],1)
