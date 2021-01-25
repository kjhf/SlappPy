from uuid import UUID
from typing import List, Set, Collection

from core_classes.score import Score
from helpers.dict_helper import deserialize_uuids, serialize_uuids


class Game:
    def __init__(self, score: Score = None, players: Collection[UUID] = None, teams: Collection[UUID] = None):
        self.score: Score = score or Score()
        self.players: Set[UUID] = players or set()
        self.teams: Set[UUID] = teams or set()

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
            result["Players"] = serialize_uuids(self.players)
        if len(self.teams) > 0:
            result["Teams"] = serialize_uuids(self.teams)
        return result
