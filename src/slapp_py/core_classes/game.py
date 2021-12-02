from uuid import UUID
from typing import Set, Dict, Optional, Iterable, Union

from slapp_py.core_classes.score import Score
from slapp_py.helpers.dict_helper import serialize_uuids_as_dict, first_key, deserialize_uuids_from_dict_as_set


class Game:
    def __init__(self, score: Score = None, ids: Optional[Dict[Union[UUID, str], Iterable[Union[UUID, str]]]] = None):
        self.score: Score = score or Score()
        self.ids: Dict[Union[UUID, str], Set[UUID]] = dict()
        for key, value in ids.items() or {}:
            if isinstance(value, str):
                value = {UUID(value)}
            elif isinstance(value, UUID):
                value = {value}
            else:
                # Normalise the type...
                ids_to_add: Set[UUID] = set()
                for i in value:
                    if i is not None:
                        if isinstance(i, str):
                            ids_to_add.add(UUID(i))
                        elif isinstance(i, UUID):
                            ids_to_add.add(i)
                        else:
                            raise TypeError(f"Unknown value type for game ids {key=} {value=} {i=}")
                value = ids_to_add

            if isinstance(key, str):
                self.ids[UUID(key)] = value
            elif isinstance(key, UUID):
                self.ids[key] = value
            else:
                raise TypeError(f"Unknown key type for game ids {key=} {value=}")

    @staticmethod
    def from_dict(obj: dict) -> 'Game':
        assert isinstance(obj, dict)
        return Game(
            score=Score.from_dict(obj.get("Score")) if "Score" in obj else None,
            ids=deserialize_uuids_from_dict_as_set(obj.get("Ids", {}))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.score.points) > 0:
            result["Score"] = self.score.to_dict()
        if len(self.ids) > 0:
            result["Ids"] = serialize_uuids_as_dict(self.ids)
        return result

    @property
    def team1_uuid(self) -> Optional[UUID]:
        return first_key(self.ids)

    @property
    def team1_players(self) -> Optional[Set[UUID]]:
        return self.ids.get(self.team1_uuid)

    @property
    def team2_uuid(self) -> Optional[UUID]:
        return list(self.ids.keys())[1]

    @property
    def team2_players(self) -> Optional[Set[UUID]]:
        return self.ids.get(self.team2_uuid)

    @property
    def players(self) -> Set[UUID]:
        """Get a flat list of players"""
        return {player_id for players_in_team in self.ids.values() for player_id in players_in_team}

    @property
    def teams(self) -> Set[UUID]:
        """Get a flat list of teams"""
        return set(self.ids.keys())
