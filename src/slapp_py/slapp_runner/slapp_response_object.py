import logging
from typing import Dict, Union, List, Tuple, Optional, Iterable
from uuid import UUID

from slapp_py.core_classes.bracket import Bracket
from slapp_py.core_classes.division import Division
from slapp_py.core_classes.player import Player
from slapp_py.core_classes.skill import Skill
from slapp_py.core_classes.team import Team
from slapp_py.slapp_runner.simple_source import SimpleSource


class SlappResponseObject:
    def __init__(self, response: dict):
        matched_players: List[Player] = [Player.from_dict(x) for x in response.get("Players", [])]
        matched_teams: List[Team] = [Team.from_dict(x) for x in response.get("Teams", [])]
        known_teams: Dict[str, Team] = {}
        placements_for_players: Dict[str, Dict[str, List[Bracket]]] = {}
        """Dictionary keyed by Player id, of value Dictionary keyed by Source id of value Placements list"""

        for team_id, team_dict in response.get("AdditionalTeams").items():
            known_teams[team_id.__str__()] = Team.from_dict(team_dict)
        for team in matched_teams:
            known_teams[team.guid.__str__()] = team

        # We're gonna tidy the mess that the serialization made.
        # The tuple is sent as a dict, which is keyed by Item1, Item2, and contains the Player (Item1) or bool (Item2).
        matched_players_for_teams: Dict[str, List[Tuple[Player, bool]]] = dict()
        """Dictionary keyed by Team id, of value (Player, bool)[], where the bool is if the Player is currently in the team."""
        for team_id, player_tuples in response.get("PlayersForTeams").items():
            for tup in player_tuples:
                player_dict = tup.get("Item1", None)
                if isinstance(player_dict, dict):
                    matched_players_for_teams\
                        .setdefault(team_id, [])\
                        .append((Player.from_dict(player_dict), bool(tup.get("Item2", False))))

        sources: Dict[str, SimpleSource] = {}
        for source_id, source_name in response.get("Sources").items():
            sources[source_id] = SimpleSource(id=source_id, name=source_name)

        for player_id, source_dicts in response.get("PlacementsForPlayers").items():
            for source_id, brackets in source_dicts.items():
                for bracket in brackets:
                    placements_for_players\
                        .setdefault(player_id, {})\
                        .setdefault(source_id, [])\
                        .append(Bracket.from_dict(bracket))

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

        return [tup[0] for tup in self.matched_players_for_teams.get(team_guid.__str__(), [])
                if tup and (tup[1] or include_ex_players)]

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

    def get_best_team_for_player(self, p: Player) -> Team:
        return self.get_best_team_by_div([self.get_team(t_uuid) for t_uuid in p.teams])

    def get_team_skills(self, team_guid: Union[UUID, str], include_ex_players: bool = True) -> Dict[Player, Skill]:
        """
        Return Player objects with their skills for the specified team id,
        optionally excluding players no longer in the team.
        """
        players = self.get_players_in_team(team_guid, include_ex_players)
        return {player: player.skill for player in players}

    def get_simple_sources(self, sources: Union[Player, Team, List[UUID]]) -> List[SimpleSource]:
        """Get the SimpleSource list for the specified sources/team/player."""
        if isinstance(sources, Player):
            sources = sources.sources
        elif isinstance(sources, Team):
            sources = sources.sources
        if not isinstance(sources, list):
            sources = [sources]

        result = []
        for source in sources:
            from slapp_py.core_classes.builtins import BuiltinSource
            if source == BuiltinSource.guid:
                result.append(SimpleSource(id=BuiltinSource.guid, name=BuiltinSource.name))
            else:
                simple_source = self.sources.get(source.__str__(), None)
                if not simple_source:
                    logging.error(f"Source was not specified in JSON: {source}")
                else:
                    result.append(simple_source)
        result.sort(key=lambda s: s.name, reverse=True)  # Sorting by name guaranteed - all sources should have a name.
        return result

    def get_grouped_sources(self, sources: Union[Player, Team, List[UUID]]) -> Dict[str, List[SimpleSource]]:
        """Group the SimpleSource list for the specified sources/team/player by tourney name."""
        simple_sources = self.get_simple_sources(sources)
        result = {}
        for simple_source in simple_sources:
            result.setdefault(simple_source.tournament_name or '', []).append(simple_source)

        for _, sources_for_tourney in result.items():
            sources_for_tourney.sort(key=lambda s: s.name, reverse=True)
        return result

    def get_grouped_sources_text(self, sources: Union[Player, Team, List[UUID]]) -> List[str]:
        """
        Group the SimpleSource list for the specified sources/team/player by tourney name.
        Duplicates are removed.
        """
        groups = self.get_grouped_sources(sources)
        message = []
        for tourney, simple_sources in groups.items():
            group_key = tourney + ': ' if tourney else ''
            group_value_array = list(set(
                [simple_source.get_linked_date_display() for simple_source in simple_sources]
                if group_key
                else [simple_source.get_linked_name_display() for simple_source in simple_sources]
            ))
            separator = ', ' if group_key else '\n'
            group_value = separator.join(group_value_array)
            message.append(f"{group_key}{group_value}")
        return message

    def get_brackets_for_player(self, p: Player, source_id: str) -> List[Bracket]:
        """
        Gets the brackets for the specified player for the source specified.
        """
        return self.placements_for_players.get(p.guid.__str__(), {}).get(source_id.__str__(), [])

    def get_first_placements(self, p: Player) -> List[str]:
        """
        Gets a list of displayed text in form {bracket.name} + ' in ' + {linked_source}
        where the specified player has come first.
        """
        result = []
        sources = self.get_simple_sources(p)
        for simple_source in sources:
            brackets = self.get_brackets_for_player(p, simple_source.id)
            for bracket in brackets:
                if 1 in bracket.placements.players_by_placement:
                    first_place_ids = [player_id.__str__() for player_id in
                                       bracket.placements.players_by_placement[1]]
                    if p.guid.__str__() in first_place_ids:
                        result.append(bracket.name + ' in ' + simple_source.get_linked_name_display())

        return result

    def get_low_ink_placements(self, p: Player) -> List[Tuple[int, str, str]]:
        """
        Returns the low ink placements this player has achieved, in form
        Ranking (number), bracket name, tournament name
        """
        result = []
        low_ink_sources = [s for s in self.placements_for_players.get(p.guid.__str__(), []) if
                           "low-ink-" in self.sources.get(s, s).name]

        for source_id in low_ink_sources:
            placements_for_source = self.placements_for_players[p.guid.__str__()][source_id]
            source_name = self.sources[source_id].name

            # Take only the brackets useful to us
            # i.e. Alpha, Beta, Gamma, and previous Top Cuts.
            # Plus the bracket must have had placements in it (a winning team)
            # We can't rely on placements that don't have one of these brackets as it may indicate that the
            # team dropped rather than was unplaced, and so is not in accordance with skill
            brackets = [b for b in placements_for_source if
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

    @staticmethod
    def get_best_team_by_div(known_teams: Iterable[Team]) -> Optional[Team]:
        """
        Calculate the best team by div in an iterable of teams.
        """
        if not known_teams:
            return None

        best_team = None
        current_highest_div = Division()
        for team in known_teams:
            highest_div = team.get_best_div()
            if highest_div < current_highest_div:
                current_highest_div = highest_div
                best_team = team

        return best_team
