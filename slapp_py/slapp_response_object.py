from typing import Dict, Union, List
from uuid import UUID

from core_classes.bracket import Bracket
from core_classes.player import Player
from core_classes.skill import Skill
from core_classes.team import Team
from helpers.dict_helper import from_list
from slapp_py.strings import attempt_link_source


class SlappResponseObject:
    def __init__(self, response: dict):
        matched_players: List[Player] = from_list(lambda x: Player.from_dict(x), response.get("Players"))
        matched_teams: List[Team] = from_list(lambda x: Team.from_dict(x), response.get("Teams"))
        known_teams: Dict[str, Team] = {}
        placements_for_players: Dict[str, Dict[str, List[Bracket]]] = {}
        """Dictionary keyed by Player id, of value Dictionary keyed by Source id of value Placements list"""

        for team_id in response.get("AdditionalTeams"):
            known_teams[team_id.__str__()] = Team.from_dict(response.get("AdditionalTeams")[team_id])
        for team in matched_teams:
            known_teams[team.guid.__str__()] = team

        matched_players_for_teams: Dict[str, List[Dict[str, Union[Player, bool]]]] = {}
        for team_id in response.get("PlayersForTeams"):
            matched_players_for_teams[team_id] = []
            for tup in response.get("PlayersForTeams")[team_id]:
                player_tuple_for_team: Dict[str, Union[Player, bool]] = \
                    {"Item1": Player.from_dict(tup["Item1"]) if "Item1" in tup else None,
                     "Item2": "Item2" in tup}
                matched_players_for_teams[team_id].append(player_tuple_for_team)

        sources: Dict[str, str] = {}

        for source_id in response.get("Sources"):
            source_name = response.get("Sources")[source_id]
            sources[source_id] = source_name

        for player_id in response.get("PlacementsForPlayers"):
            placements_for_players[player_id.__str__()] = {}
            for source_id in response.get("PlacementsForPlayers")[player_id]:
                placements_for_players[player_id][source_id] = []
                for bracket in response.get("PlacementsForPlayers")[player_id][source_id]:
                    placements_for_players[player_id][source_id].append(Bracket.from_dict(bracket))

        self.matched_players = matched_players
        self.matched_teams = matched_teams
        self.known_teams = known_teams
        self.placements_for_players = placements_for_players
        self.matched_players_for_teams = matched_players_for_teams
        self.sources = sources
        """Sources keyed by id, values are its name"""
        self.query = response.get("Query", "<UNKNOWN_QUERY_PLEASE_DEBUG>")

    @property
    def matched_players_len(self):
        return len(self.matched_players)

    @property
    def matched_teams_len(self):
        return len(self.matched_teams)

    @property
    def has_matched_players(self):
        return len(self.matched_players) != 0

    @property
    def has_matched_teams(self):
        return len(self.matched_teams) != 0

    @property
    def show_limited(self):
        return self.matched_players_len > 9 or self.matched_teams_len > 9

    def get_players_in_team(self, team_guid: Union[UUID, str], include_ex_players: bool = True) -> List[Player]:
        """Return Player objects for the specified team id, optionally excluding players no longer in the team."""

        return [player_dict["Item1"] for player_dict in self.matched_players_for_teams.get(team_guid.__str__(), [])
                if player_dict and player_dict.get("Item1") and (player_dict["Item2"] or include_ex_players)]

    def get_team_skills(self, team_guid: Union[UUID, str], include_ex_players: bool = True) -> Dict[Player, Skill]:
        """
        Return Player objects with their skills for the specified team id,
        optionally excluding players no longer in the team.
        """
        players = self.get_players_in_team(team_guid, include_ex_players)
        return {player: player.skill for player in players}

    def get_first_placements(self, p: Player) -> List[str]:
        result = []
        if p.guid.__str__() in self.placements_for_players:
            sources = self.placements_for_players[p.guid.__str__()]
            for source_id in sources:
                brackets = self.placements_for_players[p.guid.__str__()][source_id]
                for bracket in brackets:
                    if 1 in bracket.placements.players_by_placement:
                        first_place_ids = [player_id.__str__() for player_id in bracket.placements.players_by_placement[1]]
                        if p.guid.__str__() in first_place_ids:
                            result.append(bracket.name + ' in ' + attempt_link_source(self.sources[source_id]))

        return result
