from typing import Optional, List, Union, Dict
from uuid import UUID, uuid4

from core_classes import division
from core_classes.clan_tag import ClanTag
from core_classes.division import Division
from core_classes.name import Name
from core_classes.socials.battlefy_team_social import BattlefyTeamSocial
from core_classes.socials.twitter import Twitter
from helpers.dict_helper import from_list, to_list, serialize_uuids
from slapp_py.strings import escape_characters


class Team:
    battlefy_persistent_team_ids: List[BattlefyTeamSocial] = []
    """Back-store for the persistent ids of this team."""

    clan_tags: List[ClanTag] = []
    """The tag(s) of the team, first is the current tag."""

    divisions: List[Division] = []
    """The division(s) of the team, first is the current."""

    names: List[Name] = []
    """Back-store for the names of this team. The first element is the current name."""

    sources: List[UUID] = []
    """Back-store for the sources of this team."""

    twitter_profiles: List[Twitter] = []
    """Back-store for the Twitter Profiles of this team."""

    guid: UUID = uuid4()
    """The GUID of the team."""

    def __init__(self,
                 battlefy_persistent_team_ids: Optional[List[BattlefyTeamSocial]] = None,
                 clan_tags: Optional[List[ClanTag]] = None,
                 divisions: Optional[List[Division]] = None,
                 names: Union[None, Name, List[Name], str, List[str]] = None,
                 sources: Union[None, UUID, List[UUID]] = None,
                 twitter_profiles: Optional[List[Twitter]] = None,
                 guid: Union[None, str, UUID] = None):
        self.battlefy_persistent_team_ids = battlefy_persistent_team_ids or []
        self.clan_tags = clan_tags or []
        self.divisions = divisions or []

        if not sources:
            from core_classes.builtins import BuiltinSource
            self.sources = [BuiltinSource.guid]
        else:
            if not isinstance(sources, list):
                sources = [sources]

            self.sources = []
            for i in range(0, len(sources)):
                assert isinstance(sources[i], UUID)
                self.sources.append(sources[i])

        if not names:
            self.names = []
        else:
            if not isinstance(names, list):
                names = [names]

            self.names = []
            for i in range(0, len(names)):
                if isinstance(names[i], str):
                    self.names.append(Name(names[i], sources[0]))
                elif isinstance(names[i], Name):
                    self.names.append(names[i])

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
        from core_classes.builtins import UnknownTeamName
        return self.names[0] if len(self.names) > 0 else UnknownTeamName

    @property
    def tag(self) -> Optional[ClanTag]:
        """The most recent tag of the team. Can be None."""
        return self.clan_tags[0] if len(self.clan_tags) > 0 else None

    @property
    def current_div(self) -> Division:
        """The most recent division of the team or Division.Unknown."""
        return self.divisions[0] if len(self.divisions) > 0 else division.Unknown

    def __str__(self):
        return f'{(self.tag.value + " ") if self.tag else ""}' \
               f'{self.name}' \
               f'{(f" ({self.current_div})" if not self.current_div.is_unknown else "")}'

    @staticmethod
    def from_dict(obj: dict) -> 'Team':
        assert isinstance(obj, dict)
        from core_classes.source import Source
        return Team(
            battlefy_persistent_team_ids=from_list(lambda x: BattlefyTeamSocial.from_dict(x),
                                                   obj.get("BattlefyPersistentTeamIds")),
            clan_tags=from_list(lambda x: ClanTag.from_dict(x), obj.get("ClanTags")),
            divisions=from_list(lambda x: Division.from_dict(x), obj.get("Divisions")),
            names=from_list(lambda x: Name.from_dict(x), obj.get("Names")),
            sources=Source.deserialize_uuids(obj),
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
        if len(self.divisions) > 0:
            result["Divisions"] = to_list(lambda x: Division.to_dict(x), self.divisions)
        result["Id"] = self.guid.__str__()
        if len(self.names) > 0:
            result["Names"] = to_list(lambda x: Name.to_dict(x), self.names)
        if len(self.sources) > 0:
            result["S"] = serialize_uuids(self.sources)
        if len(self.twitter_profiles) > 0:
            result["Twitter"] = to_list(lambda x: Twitter.to_dict(x), self.twitter_profiles)
        return result

    @staticmethod
    def best_team_player_div_string(
            team: 'Team',
            players_for_team: List[Dict[str, Union[dict, object, bool]]],
            known_teams: Dict[str, 'Team']):
        if not players_for_team or not known_teams:
            return ''

        from core_classes.player import Player
        highest_div: Division = team.current_div
        best_player: Optional[Player] = None
        for player_tuple in players_for_team:
            if player_tuple:
                in_team = player_tuple["Item2"] if "Item2" in player_tuple else False
                p: Union[dict, Player] = player_tuple["Item1"] if "Item1" in player_tuple else None
                if p is None:
                    continue
                elif isinstance(p, dict):
                    p: Player = Player.from_dict(p)
                elif isinstance(p, Player):
                    pass
                else:
                    assert False, f"Unknown Player object {p}"

                if in_team and len(p.teams) > 0:
                    for team_id in p.teams:
                        player_team = known_teams[team_id.__str__()] if known_teams and team_id in known_teams else None
                        if (player_team is not None) \
                                and (not player_team.current_div.is_unknown) \
                                and (highest_div.is_unknown or (player_team.current_div < highest_div)):
                            highest_div = player_team.current_div
                            best_player = p

        if highest_div.is_unknown or team.current_div.is_unknown or best_player is None:
            return ''
        elif highest_div == team.current_div:
            return 'No higher div players.'
        else:
            name: str = best_player.name.value
            return f"Highest div player is {escape_characters(name)} at {highest_div.__str__()}."
