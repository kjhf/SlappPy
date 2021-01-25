from typing import List, Optional, Collection, Set, Dict
from uuid import UUID

from helpers.dict_helper import deserialize_uuids, serialize_uuids


class Placement:
    def __init__(self,
                 players_by_placement: Optional[Dict[int, Set[UUID]]] = None,
                 teams_by_placement: Optional[Dict[int, Set[UUID]]] = None):
        self.players_by_placement: Dict[int, Set[UUID]] = players_by_placement or dict()
        self.teams_by_placement: Dict[int, Set[UUID]] = teams_by_placement or dict()

    @staticmethod
    def deserialize_placement_dict(placement: dict, key: str) -> Dict[int, Set[UUID]]:
        assert isinstance(placement, dict)
        assert isinstance(placement[key], dict)
        result = {}
        for rank in placement[key]:
            result[int(rank)] = set(deserialize_uuids(placement[key], rank))
        return result

    @staticmethod
    def from_dict(obj: dict) -> 'Placement':
        assert isinstance(obj, dict)
        return Placement(
            players_by_placement=Placement.deserialize_placement_dict(obj, "PlayersByPlacement"),
            teams_by_placement=Placement.deserialize_placement_dict(obj, "TeamsByPlacement")
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.players_by_placement) > 0:
            result["PlayersByPlacement"] = Placement.serialize_placement_dict(self.players_by_placement)
        if len(self.teams_by_placement) > 0:
            result["TeamsByPlacement"] = Placement.serialize_placement_dict(self.teams_by_placement)
        return result

    @staticmethod
    def serialize_placement_dict(placement: Dict[int, Set[UUID]]) -> Dict[str, List[str]]:
        assert isinstance(placement, dict)
        result = {}
        for rank in placement:
            result[rank.__str__()] = serialize_uuids(placement[rank])
        return result
