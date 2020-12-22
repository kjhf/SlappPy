from typing import Union, List
from uuid import UUID

from core_classes.game import Game


class Bracket:
    def __init__(self, param: Union[None, str]):
        self.matches: List[Game] = []
        self.name: str = param if isinstance(param, str) else None
        self.players: List[UUID] = []
        self.teams: List[UUID] = []

    def __str__(self):
        return self.name
