from copy import deepcopy

class HomeProfile:
    def __init__(self, data=None):
        data = dict(data or {})
        self._data = {
            "rhythm": data.get("rhythm", "balanced"),
            "quietness": data.get("quietness", "balanced"),
            "care_focus": list(data.get("care_focus", [])),
            "traditions": list(data.get("traditions", [])),
            "boundaries": dict(data.get("boundaries", {
                "notification": "minimal",
                "automation": "suggestion_only",
                "privacy": "maximum",
            })),
        }

    def snapshot(self):
        return deepcopy(self._data)

    def update_confirmed(self, changes):
        changes = dict(changes or {})
        for key in ("rhythm", "quietness", "care_focus", "traditions", "boundaries"):
            if key in changes:
                self._data[key] = deepcopy(changes[key])
        return self.snapshot()
