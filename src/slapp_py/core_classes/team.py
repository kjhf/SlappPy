import logging
from typing import Optional, List, Union
from uuid import UUID, uuid4

from slapp_py.core_classes import division
from slapp_py.core_classes.clan_tag import ClanTag
from slapp_py.core_classes.division import Division
from slapp_py.core_classes.divisions_handler import DivisionsHandler
from slapp_py.core_classes.name import Name
from slapp_py.core_classes.simple_source import SimpleSource
from slapp_py.core_classes.socials.battlefy_team_social import BattlefyTeamSocial
from slapp_py.core_classes.socials.twitter import Twitter
from slapp_py.helpers.dict_helper import from_list, to_list


class Team:
    battlefy_persistent_team_ids: List[BattlefyTeamSocial] = []
    """Back-store for the persistent ids of this team."""

    clan_tags: List[ClanTag] = []
    """The tag(s) of the team, first is the current tag."""

    division_information: DivisionsHandler
    """The division(s) of the team."""

    names: List[Name] = []
    """Back-store for the names of this team. The first element is the current name."""

    twitter_profiles: List[Twitter] = []
    """Back-store for the Twitter Profiles of this team."""

    guid: UUID = uuid4()
    """The GUID of the team."""

    def __init__(self,
                 battlefy_persistent_team_ids: Optional[List[BattlefyTeamSocial]] = None,
                 clan_tags: Optional[List[ClanTag]] = None,
                 division_information: Optional[DivisionsHandler] = None,
                 names: Union[None, Name, List[Name], str, List[str]] = None,
                 twitter_profiles: Optional[List[Twitter]] = None,
                 guid: Union[None, str, UUID] = None):
        self.battlefy_persistent_team_ids = battlefy_persistent_team_ids or []
        self.clan_tags = list(set(clan_tags or []))
        self.division_information = division_information or DivisionsHandler()

        if not names:
            self.names = []
        else:
            if not isinstance(names, list):
                names = [names]

            self.names = []
            for i in range(0, len(names)):
                if isinstance(names[i], str):
                    if not any(n == names[i] for n in self.names):
                        self.names.append(Name(names[i], None))
                elif isinstance(names[i], Name):
                    if not any(n == names[i].value for n in self.names):
                        self.names.append(names[i])
                else:
                    logging.error(f"team: Can't handle {names[i]} -- expected Name or str. Ignoring.")

        self.twitter_profiles = twitter_profiles or []
        if isinstance(guid, str):
            guid = UUID(guid)
        self.guid = guid or uuid4()

    @property
    def battlefy_persistent_id_strings(self) -> List[str]:
        """The known Battlefy Persistent Ids of the team. Can be Empty."""
        return [social.value for social in self.battlefy_persistent_team_ids] \
            if len(self.battlefy_persistent_team_ids) > 0 else []

    @property
    def battlefy_persistent_team_id(self) -> Optional[Name]:
        """The last known Battlefy Persistent Id of the team. Can be None."""
        return self.battlefy_persistent_team_ids[0] if len(self.battlefy_persistent_team_ids) > 0 else None

    @property
    def name(self) -> Name:
        """The last known used name for the Team or UnknownTeamName."""
        from slapp_py.core_classes.builtins import UnknownTeamName
        return self.names[0] if len(self.names) > 0 else UnknownTeamName

    @property
    def tag(self) -> Optional[ClanTag]:
        """The most recent tag of the team. Can be None."""
        return self.clan_tags[0] if len(self.clan_tags) > 0 else None

    @property
    def current_div(self) -> Division:
        """The most recent division of the team or Division.Unknown."""
        return self.division_information.current_div

    @property
    def div_history(self) -> str:
        """The team's division history as a display str."""
        if self.current_div.is_unknown:
            return ""
        else:
            return ' ⬅ '.join([d.__str__() for d in self.division_information.get_divs_ordered()[:3]])

    def filter_to_source(self, source_id: SimpleSource) -> 'Team':
        """Filter this Team instance down to the components made by a sources id."""
        return Team(
            battlefy_persistent_team_ids=[name for name in self.battlefy_persistent_team_ids if source_id in name.sources],
            clan_tags=[name for name in self.clan_tags if source_id in name.sources],
            division_information=self.division_information.filter_to_source(source_id),
            names=[name for name in self.names if source_id in name.sources],
            twitter_profiles=[name for name in self.twitter_profiles if source_id in name.sources],
            guid=uuid4())

    @property
    def sources(self):
        return \
            list(
                sorted(
                    set(
                        sum([x.sources for x in self.names]
                            + [x.sources for x in self.battlefy_persistent_team_ids]
                            + [x.sources for x in self.clan_tags]
                            + [x.sources for x in self.twitter_profiles], [])
                    ),
                    reverse=True
                )
            )

    def __str__(self):
        return f'{(self.tag.value + " ") if self.tag else ""}' \
               f'{self.name}' \
               f'{(f" ({self.div_history})" if not self.current_div.is_unknown else "")}'

    @staticmethod
    def from_dict(obj: dict) -> 'Team':
        assert isinstance(obj, dict)
        return Team(
            battlefy_persistent_team_ids=from_list(lambda x: BattlefyTeamSocial.from_dict(x),
                                                   obj.get("BattlefyPersistentTeamIds")),
            clan_tags=from_list(lambda x: ClanTag.from_dict(x), obj.get("ClanTags")),
            division_information=DivisionsHandler.from_dict(obj.get("Divisions")) if "Divisions" in obj else None,
            names=from_list(lambda x: Name.from_dict(x), obj.get("N")),
            twitter_profiles=from_list(lambda x: Twitter.from_dict(x), obj.get("Twitter")),
            guid=UUID(obj.get("Id"))
        )

    def to_dict(self) -> dict:
        result = {}
        if len(self.battlefy_persistent_team_ids) > 0:
            result["BattlefyPersistentTeamIds"] = to_list(lambda x: BattlefyTeamSocial.to_dict(x),
                                                          self.battlefy_persistent_team_ids)
        if len(self.clan_tags) > 0:
            result["ClanTags"] = to_list(lambda x: ClanTag.to_dict(x), self.clan_tags)
        if self.division_information.count > 0:
            result["Divisions"] = self.division_information.to_dict()
        result["Id"] = self.guid.__str__()
        if len(self.names) > 0:
            result["N"] = to_list(lambda x: Name.to_dict(x), self.names)
        if len(self.twitter_profiles) > 0:
            result["Twitter"] = to_list(lambda x: Twitter.to_dict(x), self.twitter_profiles)
        return result

    def get_best_div(self, last_n_divisions: int = 3) -> Division:
        """The team's best division in the last n divisions"""
        if self.current_div.is_unknown:
            return self.current_div
        else:
            best_div = division.Unknown
            last_n_divisions = min(last_n_divisions, self.division_information.count)  # Can only be up to the size.
            for div in self.division_information.get_divs_ordered()[:last_n_divisions]:
                if div < best_div:
                    best_div = div
            return best_div
