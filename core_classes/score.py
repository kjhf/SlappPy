from typing import List

from helpers.dict_helper import from_list


class Score:
    points: List[int]

    def __init__(self, points: List[int] = None):
        self.points: List[int] = points or []

    @property
    def description(self) -> str:
        return '-'.join(list(map(lambda point: point.__str__(), self.points)))

    @property
    def games_played(self) -> int:
        return sum(self.points)

    @staticmethod
    def from_dict(obj: dict) -> 'Score':
        assert isinstance(obj, dict)
        return Score(
            points=from_list(lambda x: int(x), obj.get("Points"))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.points) > 0:
            result["Points"] = self.points
        return result
