from uuid import UUID
from typing import Set, Dict, Optional, Iterable

from slapp_py.core_classes.score import Score
from slapp_py.helpers.dict_helper import serialize_uuids_as_dict, first_key, deserialize_uuids_from_dict_as_set


class Game:
    def __init__(self, score: Score = None, ids: Dict[UUID, Iterable[UUID]] = None):
        self.score: Score = score or Score()
        self.ids = dict()
        for team_id in ids or []:
            self.ids[team_id] = set(ids[team_id])

    @staticmethod
    def from_dict(obj: dict) -> 'Game':
        assert isinstance(obj, dict)
        return Game(
            score=Score.from_dict(obj.get("Score")) if "Score" in obj else None,
            ids=deserialize_uuids_from_dict_as_set(obj.get("Ids", {}))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.score.points) > 0:
            result["Score"] = self.score.to_dict()
        if len(self.ids) > 0:
            result["Ids"] = serialize_uuids_as_dict(self.ids)
        return result

    @property
    def team1_uuid(self) -> Optional[UUID]:
        return first_key(self.ids)

    @property
    def team1_players(self) -> Set[UUID]:
        return self.ids.get(self.team1_uuid)

    @property
    def team2_uuid(self) -> Optional[UUID]:
        return list(self.ids.keys())[1]

    @property
    def team2_players(self) -> Set[UUID]:
        return self.ids.get(self.team2_uuid)

    @property
    def players(self) -> Set[UUID]:
        """Get a flat list of players"""
        return {player_id for players_in_team in self.ids.values() for player_id in players_in_team}

    @property
    def teams(self) -> Set[UUID]:
        """Get a flat list of teams"""
        return set(self.ids.keys())
