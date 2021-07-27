from typing import Dict, Union, List, Tuple, Optional
from uuid import UUID

from slapp_py.core_classes.bracket import Bracket
from slapp_py.core_classes.player import Player
from slapp_py.core_classes.skill import Skill
from slapp_py.core_classes.team import Team
from slapp_py.helpers.sources_helper import attempt_link_source


class SlappResponseObject:
    def __init__(self, response: dict):
        matched_players: List[Player] = [Player.from_dict(x) for x in response.get("Players", [])]
        matched_teams: List[Team] = [Team.from_dict(x) for x in response.get("Teams", [])]
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
    def is_single_player(self):
        return self.matched_players_len == 1 and self.matched_teams_len == 0

    @property
    def is_single_team(self):
        return self.matched_players_len == 0 and self.matched_teams_len == 1

    @property
    def single_player(self):
        return self.matched_players[0] if self.is_single_player else None

    @property
    def single_team(self):
        return self.matched_teams[0] if self.is_single_team else None

    @property
    def show_limited(self):
        return self.matched_players_len > 9 or self.matched_teams_len > 9

    def get_best_division_for_player(self, p: Player):
        from slapp_py.core_classes import division

        teams = self.get_teams_for_player(p)
        best_div = division.Unknown
        for div in list(map(lambda team: team.get_best_div(), teams)):
            if div < best_div:
                best_div = div
        return best_div

    def get_players_in_team(self, team_guid: Union[UUID, str], include_ex_players: bool = True) -> List[Player]:
        """Return Player objects for the specified team id, optionally excluding players no longer in the team."""

        return [player_dict["Item1"] for player_dict in self.matched_players_for_teams.get(team_guid.__str__(), [])
                if player_dict and player_dict.get("Item1") and (player_dict["Item2"] or include_ex_players)]

    def get_team(self, team_id: Union[str, UUID]) -> Team:
        from slapp_py.core_classes.builtins import NoTeam, UnknownTeam
        if isinstance(team_id, UUID):
            t_str = team_id.__str__()
        elif isinstance(team_id, str):
            t_str = team_id
        elif team_id is None:
            return NoTeam
        else:
            assert False, f"Don't know what {team_id} is"

        return NoTeam if t_str == NoTeam.guid.__str__() else self.known_teams.get(t_str, UnknownTeam)

    def get_teams_for_player(self, p: Player) -> List[Team]:
        return [self.get_team(t_uuid) for t_uuid in p.teams]

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
                        first_place_ids = [player_id.__str__() for player_id in
                                           bracket.placements.players_by_placement[1]]
                        if p.guid.__str__() in first_place_ids:
                            result.append(bracket.name + ' in ' + attempt_link_source(self.sources[source_id]))

        return result

    def get_low_ink_placements(self, p: Player) -> List[Tuple[int, str, str]]:
        """
        Returns the low ink placements this player has achieved, in form
        Ranking (number), bracket name, tournament name
        """
        result = []
        low_ink_sources = [s for s in self.placements_for_players.get(p.guid.__str__(), []) if
                           "low-ink-" in self.sources.get(s, s)]

        for source_id in low_ink_sources:
            source_name = self.sources[source_id]

            # Take only the brackets useful to us
            # i.e. Alpha, Beta, Gamma, and previous Top Cuts.
            # Plus the bracket must have had placements in it (a winning team)
            brackets = [b for b in self.placements_for_players[p.guid.__str__()][source_id] if
                        (
                                "Alpha" in b.name or
                                "Beta" in b.name or
                                "Gamma" in b.name or
                                "Top Cut" in b.name
                        ) and 1 in b.placements.players_by_placement]
            for bracket in brackets:
                for placement in bracket.placements.players_by_placement:
                    if p.guid in bracket.placements.players_by_placement[placement]:
                        result.append((placement, bracket.name, source_name))
        return result

    def best_low_ink_placement(self, p: Player) -> Optional[Tuple[int, str, str]]:
        """
        Iterate through the get_low_ink_placements and pick out the best
        Returns a Tuple in form:
        Ranking (number), bracket name, tournament name
        """
        current_best = None
        for placement in self.get_low_ink_placements(p):
            if not placement:
                continue

            if current_best is None:
                current_best = placement
            else:
                is_same_comparison = ("Alpha" in placement[1] and "Alpha" in current_best[1]) or \
                                     ("Beta" in placement[1] and "Beta" in current_best[1]) or \
                                     ("Gamma" in placement[1] and "Gamma" in current_best[1]) or \
                                     ("Alpha" in placement[1] and "Top Cut" in current_best[1]) or \
                                     ("Top Cut" in placement[1] and "Alpha" in current_best[1])
                if is_same_comparison:
                    # If lower place (i.e. did better)
                    if placement[0] < current_best[0]:
                        current_best = placement
                else:
                    if "Alpha" in placement[1] or "Top Cut" in placement[1]:
                        # Better than the current best's bracket
                        current_best = placement
                    elif "Beta" in placement[1]:
                        if "Alpha" not in current_best[1]:
                            # Better than the current best's bracket (gamma)
                            current_best = placement
                    # else gamma but this isn't better than the valid bracket names already tested
        return current_best

    @staticmethod
    def placement_is_winning_low_ink(placement: Tuple[int, str, str]):
        return placement and placement[0] == 1 and ("Top Cut" in placement[1] or "Alpha" in placement[1])
