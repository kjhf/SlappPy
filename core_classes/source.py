import uuid
from typing import Union, List

from core_classes.bracket import Bracket
from core_classes.placement import Placement


class Source:
    def __init__(self, param: Union[None, uuid.UUID, str]):
        self.brackets: List[Bracket] = []
        self.guid: uuid.UUID = param if isinstance(param, uuid.UUID) else uuid.uuid4()
        self.name: str = param if isinstance(param, str) else None
        self.placement: Placement = Placement()
        self.players: List[Player] = []
        self.teams: List[Team] = []
        self.uris: List[str] = []

    def __str__(self):
        return self.name

    def serialize(self, info: dict):
        if len(self.brackets) > 0:
            info["Brackets"] = self.brackets
        info["Id"] = self.guid

        if self.name is not None:
            info["Name"] = self.name

        if len(self.placement.players_by_placement) > 0 or len(self.placement.teams_by_placement) > 0:
            info["Placements"] = self.placement

        if len(self.players) > 0:
            info["Players"] = self.players

        if len(self.teams) > 0:
            info["Teams"] = self.teams

        if len(self.uris) > 0:
            info["Uris"] = self.uris
