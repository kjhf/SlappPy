from typing import List

from slapp_py.helpers.dict_helper import from_list


class Score:
    def __init__(self, points: List[int] = None):
        self.points: List[int] = points or []

    @property
    def description(self) -> str:
        """Get a readable description of the points in a-b-c-... format, e.g. 3-2"""
        return '-'.join(list(map(lambda point: point.__str__(), self.points)))

    @property
    def games_played(self) -> int:
        """Get a sum of the points, i.e. the number of games played. Will always return 0 or more."""
        return max(0, sum(self.points))

    @property
    def winning_team_index(self) -> int:
        """Get the winning team index, e.g. team1 = 0. No winner/draw is -1."""
        if not len(self.points):
            return -1

        best_point = -1
        best_index = -1
        for index, point in enumerate(self.points):
            if point > best_point:
                best_index = index
                best_point = point
            elif point == best_point:
                best_index = -1
                break

        return best_index

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
