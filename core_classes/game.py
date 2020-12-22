from uuid import UUID
from typing import List

from core_classes.score import Score


class Game:
    def __init__(self):
        self.score: Score = Score()
        self.players: List[UUID] = []
        self.teams: List[UUID] = []

