from typing import List


class Score:
    def __init__(self):
        self.points: List[int] = []

    @property
    def description(self) -> str:
        return '-'.join(list(map(lambda point: point.__str__(), self.points)))

    @property
    def games_played(self) -> int:
        return sum(self.points)
