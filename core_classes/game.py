from uuid import UUID
from typing import List

from core_classes.score import Score
from helpers.dict_helper import deserialize_uuids


class Game:
    score: Score
    players: List[UUID]
    teams: List[UUID]

    def __init__(self, score: Score = None, players: List[UUID] = None, teams: List[UUID] = None):
        self.score: Score = score or Score()
        self.players: List[UUID] = players or []
        self.teams: List[UUID] = teams or []

    @staticmethod
    def from_dict(obj: dict) -> 'Game':
        assert isinstance(obj, dict)
        return Game(
            score=Score.from_dict(obj.get("Score")) if "Score" in obj else None,
            players=deserialize_uuids(obj, "Players"),
            teams=deserialize_uuids(obj, "Teams")
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.score.points) > 0:
            result["Score"] = self.score.to_dict()
        if len(self.players) > 0:
            result["Players"] = map(str, self.players)
        if len(self.teams) > 0:
            result["Teams"] = map(str, self.teams)
        return result
