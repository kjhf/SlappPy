from dataclasses import dataclass
from typing import List

from slapp_py.helpers.dict_helper import from_list, to_list
from slapp_py.misc.models.battlefy_player import BattlefyPlayer


@dataclass
class BattlefyTeam:
    _id: str
    name: str
    persistent_team_id: str
    players: List[BattlefyPlayer]

    @staticmethod
    def from_dict(obj: dict) -> 'BattlefyTeam':
        assert isinstance(obj, dict)
        return BattlefyTeam(
            _id=obj.get("_id", None),
            name=obj.get("name", None),
            persistent_team_id=obj.get("persistentTeamID", None),
            players=from_list(lambda x: BattlefyPlayer.from_dict(x), obj.get("players"))
        )

    def to_dict(self) -> dict:
        result = {"_id": self._id, "name": self.name, "persistentTeamID": self.persistent_team_id, "players": to_list(lambda x: BattlefyPlayer.to_dict(x), self.players)}
        return result
