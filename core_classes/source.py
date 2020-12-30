from typing import Union, List, Optional
from uuid import UUID, uuid4

from core_classes.bracket import Bracket
from core_classes.placement import Placement
from core_classes.player import Player
from core_classes.team import Team
from helpers.dict_helper import to_list, from_list

UNKNOWN_SOURCE = "(Unnamed Source)"
"""Displayed string for an unknown source."""


class Source:
    brackets: List[Bracket]
    guid: UUID
    name: str
    placements: Placement
    players: List[Player]
    teams: List[Team]
    uris: List[str]

    def __init__(self,
                 name: Optional[str] = None,
                 brackets: Optional[List[Bracket]] = None,
                 placements: Optional[Placement] = None,
                 players: Optional[List[Player]] = None,
                 teams: Optional[List[Team]] = None,
                 uris: Optional[List[str]] = None,
                 guid: Union[None, str, UUID] = None
                 ):
        self.brackets: List[Bracket] = brackets or []
        self.name: str = name or UNKNOWN_SOURCE
        self.placements: Placement = placements or Placement()
        self.players: List[Player] = players or []
        self.teams: List[Team] = teams or []
        self.uris: List[str] = uris or []

        if isinstance(guid, str):
            guid = UUID(guid)
        self.guid = guid or uuid4()

    def __str__(self):
        return self.name

    @staticmethod
    def deserialize_uuids(info: dict, key: str = "S") -> List[UUID]:
        sources: List[UUID] = []
        incoming_sources = info.get(key, [])
        if not isinstance(incoming_sources, list):
            incoming_sources = [incoming_sources]

        for s in incoming_sources:
            if isinstance(s, str):
                sources.append(UUID(s))
            elif isinstance(s, UUID):
                sources.append(s)
            elif isinstance(s, Source):
                sources.append(s.guid)
            else:
                print(f"Could not convert s into UUID ({s=})")
        return sources

    @staticmethod
    def from_dict(obj: dict) -> 'Source':
        assert isinstance(obj, dict)
        return Source(
            guid=UUID(obj.get("Id")),
            name=obj.get("Name", UNKNOWN_SOURCE),
            brackets=from_list(lambda x: Bracket.from_dict(x), obj.get("Brackets")),
            placements=Placement.from_dict(obj.get("Placements")),
            players=from_list(lambda x: Player.from_dict(x), obj.get("Players")),
            teams=from_list(lambda x: Team.from_dict(x), obj.get("Teams")),
            uris=from_list(lambda x: str(x), obj.get("Uris"))
        )

    def to_dict(self) -> dict:
        result = {"Id": self.guid, "Name": self.name}
        if len(self.brackets) > 0:
            result["Brackets"] = to_list(lambda x: Bracket.to_dict(x), self.brackets)
        if len(self.placements.players_by_placement) > 0 or len(self.placements.teams_by_placement) > 0:
            result["Placements"] = self.placements.to_dict()
        if len(self.players) > 0:
            result["Players"] = to_list(lambda x: Player.to_dict(x), self.players)
        if len(self.teams) > 0:
            result["Teams"] = to_list(lambda x: Team.to_dict(x), self.teams)
        if len(self.uris) > 0:
            result["Uris"] = map(str, self.uris)
        return result
