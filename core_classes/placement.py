from typing import List
from uuid import UUID


class Placement:
    def __init__(self):
        self.players_by_placement: List[UUID] = []
        self.teams_by_placement: List[UUID] = []
