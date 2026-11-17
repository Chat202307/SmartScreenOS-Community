from copy import deepcopy
class StaticKnowledge:
    def __init__(self,global_values=None,location_values=None):
        self._global=dict(global_values or {})
        self._locations={k:dict(v) for k,v in dict(location_values or {}).items()}
    def get(self,key,location_id=None,default=None):
        if location_id is not None and key in self._locations.get(location_id,{}):
            return deepcopy(self._locations[location_id][key])
        return deepcopy(self._global.get(key,default))
    def snapshot(self):
        return {"global":deepcopy(self._global),"locations":deepcopy(self._locations)}
