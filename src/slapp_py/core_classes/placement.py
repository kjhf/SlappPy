from typing import Optional, Dict, Iterable, Union
from uuid import UUID

from slapp_py.helpers.dict_helper import serialize_uuids_as_dict, deserialize_uuids_from_dict_as_set


class Placement:
    def __init__(self,
                 players_by_placement: Optional[Dict[Union[int, str], Iterable[UUID]]] = None,
                 teams_by_placement: Optional[Dict[Union[int, str], Iterable[UUID]]] = None):
        """
        Construct a placement with the players and teams who played in dictionaries by ranking.

        :param players_by_placement: A dictionary containing ranks (int or str) with player uuid values.
        :param teams_by_placement: A dictionary containing ranks (int or str) with team uuid values.
        """
        self.players_by_placement = dict()
        for rank in players_by_placement or []:
            to_add = set(players_by_placement[rank])
            if len(to_add) > 0:
                self.players_by_placement[int(rank)] = to_add

        self.teams_by_placement = dict()
        for rank in teams_by_placement or []:
            to_add = set(teams_by_placement[rank])
            if len(to_add) > 0:
                self.teams_by_placement[int(rank)] = to_add

    @staticmethod
    def from_dict(obj: dict) -> 'Placement':
        assert isinstance(obj, dict)
        return Placement(
            players_by_placement=deserialize_uuids_from_dict_as_set(obj.get("PlayersByPlacement", {})),
            teams_by_placement=deserialize_uuids_from_dict_as_set(obj.get("TeamsByPlacement", {}))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.players_by_placement) > 0:
            result["PlayersByPlacement"] = serialize_uuids_as_dict(self.players_by_placement)
        if len(self.teams_by_placement) > 0:
            result["TeamsByPlacement"] = serialize_uuids_as_dict(self.teams_by_placement)
        return result
