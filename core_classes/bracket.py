from typing import List, Optional, Set
from uuid import UUID

from core_classes.game import Game
from core_classes.placement import Placement
from helpers.dict_helper import from_list, deserialize_uuids, to_list, serialize_uuids

UNKNOWN_BRACKET = "(Unnamed Bracket)"
"""Displayed string for an unknown bracket."""


class Bracket:
    def __init__(self,
                 name: Optional[str],
                 matches: Optional[List[Game]] = None,
                 players: Optional[List[UUID]] = None,
                 teams: Optional[List[UUID]] = None,
                 placements: Optional[Placement] = None):
        self.name: str = name or UNKNOWN_BRACKET
        self.matches: Set[Game] = matches or set()
        self.players: Set[UUID] = players or set()
        self.teams: Set[UUID] = teams or set()
        self.placements: Placement = placements or Placement()

    def __str__(self):
        return self.name

    @staticmethod
    def from_dict(obj: dict) -> 'Bracket':
        assert isinstance(obj, dict)
        return Bracket(
            name=obj.get("Name", UNKNOWN_BRACKET),
            matches=from_list(lambda x: Game.from_dict(x), obj.get("Matches")),
            players=deserialize_uuids(obj, "Players"),
            teams=deserialize_uuids(obj, "Teams"),
            placements=Placement.from_dict(obj.get("Placements")) if "Placements" in obj else None
        )

    def to_dict(self) -> dict:
        result = {"Name": self.name}
        if len(self.matches) > 0:
            result["Matches"] = to_list(lambda x: Game.to_dict(x), self.matches)
        if len(self.players) > 0:
            result["Players"] = serialize_uuids(self.players)
        if len(self.teams) > 0:
            result["Teams"] = serialize_uuids(self.teams)
        if len(self.placements.players_by_placement) > 0 or len(self.placements.teams_by_placement) > 0:
            result["Placements"] = self.placements.to_dict()
        return result
