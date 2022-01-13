import logging
from typing import List, Union, Dict, Optional
from uuid import UUID

from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.helpers.dict_helper import first_key, order_dict_by_value


class TeamsHandler:
    _teams: Dict[UUID, List[SimpleSource]]
    _ordered: bool = False

    def __init__(self, teams: Optional[Dict[UUID, List[SimpleSource]]] = None):
        self._teams = teams or {}

    @property
    def count(self):
        return len(self._teams)

    @property
    def current_team(self) -> UUID:
        """Get the current team in the Teams in this information."""
        if not self._ordered:
            self._order_teams()
        from slapp_py.core_classes.builtins import UnknownTeam
        return first_key(self._teams, UnknownTeam.guid)

    def add(self, incoming: Union[UUID, List[UUID]], sources: Union[SimpleSource, List[SimpleSource]]):
        if not incoming or not sources:
            return
        if not isinstance(incoming, list):
            incoming = [incoming]

        self._ordered = False
        for to_add in incoming:
            self._teams.setdefault(to_add, []).extend(SimpleSource.from_serialized(sources))

    def merge(self, handler: 'TeamsHandler'):
        for key, value in handler._teams.items():
            self.add(key, value)

    def filter_to_source(self, source_id: SimpleSource) -> 'TeamsHandler':
        return TeamsHandler(
            teams={k: v for k, v in self._teams.items() if source_id in v}
        )

    def get_sources_for_team(self, team: UUID) -> List[SimpleSource]:
        """Gets sources for the team, or empty if not found."""
        return self._teams.get(team, [])

    def get_sources_flat(self) -> List[SimpleSource]:
        """Gets sources contained in this information."""
        return list(set([result for sublist in self._teams.values() for result in sublist]))

    def get_teams_unordered(self):
        """Get the teams without the sources."""
        return list(self._teams.keys())

    def get_teams_ordered(self):
        """Get the teams without the sources in chronological order from most recent."""
        if not self._ordered:
            self._order_teams()
        return self.get_teams_unordered()

    def get_teams_sourced(self) -> Dict[UUID, List[SimpleSource]]:
        """Get the teams with sources."""
        return {k: v for k, v in self._teams.items()}

    def _order_teams(self):
        self._teams = order_dict_by_value(self._teams, reverse=True)
        self._ordered = True

    @staticmethod
    def from_dict(obj: dict) -> 'TeamsHandler':
        assert isinstance(obj, dict)
        try:
            val_dict = obj.get("T")
            result = TeamsHandler()
            for key, value in val_dict.items():
                result.add(UUID(key), SimpleSource.from_serialized(value))
            return result
        except Exception as e:
            logging.exception(exc_info=e, msg=f"Exception occurred loading Divisions Handler: {e}, {e.args}")
            raise e

    def to_dict(self) -> dict:
        result = {}
        if len(self._teams) > 0:
            result["T"] = {k.__str__(): SimpleSource.to_serialized(v) for k, v in self._teams.items()}
        return result

    def __str__(self):
        return f"{self.count} Teams{(f', current={first_key(self._teams)}' if self.count > 0 else '')}"
