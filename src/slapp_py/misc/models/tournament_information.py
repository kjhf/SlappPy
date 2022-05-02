from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class TournamentInformation:
    name: str
    stage_ids: Optional[List[str]]
    start_time: Optional[datetime]
    players_per_team: int
    stage_types: List[Tuple[str, str]]
    """Stages in order of rounds, tupled by its id and its type"""
    organization: str
    org_slug: str
    contact_link: Optional[str]
    """Contact link, probably discord"""
    stream_link: Optional[str]
    """Stream link, probably Twitch"""

    @staticmethod
    def from_dict(obj: dict) -> 'TournamentInformation':
        assert isinstance(obj, dict)
        stream_link = obj.get("streams", None)
        if stream_link:
            stream_link = stream_link[0].get("link", "")

        return TournamentInformation(
            name=obj.get("name", "<Unnamed Tournament>"),
            stage_ids=obj.get("stageIDs", None),
            start_time=obj.get("startTime", None),
            players_per_team=obj.get("playersPerTeam", 0),
            stage_types=list(map(lambda stage: (stage["_id"], stage["bracket"].get("style", "") + " " + stage["bracket"].get("type", "")), obj.get("stages", []))),
            organization=obj.get("organization", {}).get("name", ""),
            org_slug=obj.get("slug", ""),
            contact_link=obj.get("contact", {}).get("details", ""),
            stream_link=stream_link
        )

    @staticmethod
    def get_headers() -> List[str]:
        return list(TournamentInformation.from_dict({}).__dataclass_fields__.keys())

    def to_row(self) -> List[str]:
        return list(self.__dict__.values())


# if __name__ == '__main__':
#     print(TournamentInformation.get_headers())
#     print(TournamentInformation.from_dict({}).to_row())
