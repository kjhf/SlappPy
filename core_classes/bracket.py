from typing import List, Optional
from uuid import UUID

from core_classes.game import Game
from helpers.dict_helper import from_list, deserialize_uuids, to_list

UNKNOWN_BRACKET = "(Unnamed Bracket)"
"""Displayed string for an unknown bracket."""


class Bracket:
    name: str
    matches: List[Game]
    players: List[UUID]
    teams: List[UUID]

    def __init__(self,
                 name: Optional[str],
                 matches: Optional[List[Game]] = None,
                 players: Optional[List[UUID]] = None,
                 teams: Optional[List[UUID]] = None):
        self.name: str = name or UNKNOWN_BRACKET
        self.matches: List[Game] = matches or []
        self.players: List[UUID] = players or []
        self.teams: List[UUID] = teams or []

    def __str__(self):
        return self.name

    @staticmethod
    def from_dict(obj: dict) -> 'Bracket':
        assert isinstance(obj, dict)
        return Bracket(
            name=obj.get("Name", UNKNOWN_BRACKET),
            matches=from_list(lambda x: Game.from_dict(x), obj.get("Matches")),
            players=deserialize_uuids(obj, "Players"),
            teams=deserialize_uuids(obj, "Teams")
        )

    def to_dict(self) -> dict:
        result = {"Name": self.name}
        if len(self.matches) > 0:
            result["Matches"] = to_list(lambda x: Game.to_dict(x), self.matches)
        if len(self.players) > 0:
            result["Players"] = map(str, self.players)
        if len(self.teams) > 0:
            result["Teams"] = map(str, self.teams)
        return result
