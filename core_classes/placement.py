from typing import List, Optional
from uuid import UUID

from helpers.dict_helper import deserialize_uuids


class Placement:
    players_by_placement: Optional[List[UUID]]
    teams_by_placement: Optional[List[UUID]]

    def __init__(self,
                 players_by_placement: Optional[List[UUID]] = None,
                 teams_by_placement: Optional[List[UUID]] = None):
        self.players_by_placement: List[UUID] = players_by_placement or []
        self.teams_by_placement: List[UUID] = teams_by_placement or []

    @staticmethod
    def from_dict(obj: dict) -> 'Placement':
        assert isinstance(obj, dict)
        return Placement(
            players_by_placement=deserialize_uuids(obj, "PlayersByPlacement"),
            teams_by_placement=deserialize_uuids(obj, "TeamsByPlacement")
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.players_by_placement) > 0:
            result["PlayersByPlacement"] = map(str, self.players_by_placement)
        if len(self.teams_by_placement) > 0:
            result["TeamsByPlacement"] = map(str, self.teams_by_placement)
        return result
