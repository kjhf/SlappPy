from typing import List, Optional, Set
from uuid import UUID

from slapp_py.core_classes.game import Game
from slapp_py.core_classes.placement import Placement
from slapp_py.helpers.dict_helper import from_list, to_list

UNKNOWN_BRACKET = "(Unnamed Bracket)"
"""Displayed string for an unknown bracket."""


class Bracket:
    def __init__(self,
                 name: Optional[str],
                 matches: Optional[List[Game]] = None,
                 placements: Optional[Placement] = None):
        self.name: str = name or UNKNOWN_BRACKET
        self.matches: List[Game] = matches or list()
        self.placements: Placement = placements or Placement()

    def __str__(self):
        return self.name

    @staticmethod
    def from_dict(obj: dict) -> 'Bracket':
        assert isinstance(obj, dict)
        return Bracket(
            name=obj.get("Name", UNKNOWN_BRACKET),
            matches=from_list(lambda x: Game.from_dict(x), obj.get("Matches")),
            placements=Placement.from_dict(obj.get("Placements")) if "Placements" in obj else None
        )

    def to_dict(self) -> dict:
        result = {"Name": self.name}
        if len(self.matches) > 0:
            result["Matches"] = to_list(lambda x: Game.to_dict(x), self.matches)
        placements_dict = self.placements.to_dict()
        if len(placements_dict) > 0:
            result["Placements"] = placements_dict
        return result

    @property
    def players(self) -> Set[UUID]:
        """Get a set of all the players that have played in this Bracket."""
        players = set()
        for match in self.matches:
            for player in match.players:
                players.add(player)
        return players

    @property
    def teams(self) -> Set[UUID]:
        """Get a set of all the teams that have played in this Bracket."""
        teams = set()
        for match in self.matches:
            for team in match.teams:
                teams.add(team)
        return teams

    @property
    def is_valid(self):
        return self.players and self.teams and \
               self.placements.players_by_placement and self.placements.teams_by_placement
