from datetime import datetime
from os.path import join
from typing import List, Dict, Optional, Iterable
from uuid import UUID

from caching.fileio import save_as_json_to_file  # battlefy-toolkit

from core_classes import division
from core_classes.player import Player
from core_classes.skill import Skill
from core_classes.source import Source
from core_classes.team import Team
from misc.slapp_files_utils import load_latest_snapshot_players_file, \
    load_latest_snapshot_teams_file, enumerate_latest_snapshot_sources_file
from tokens import SLAPP_APP_DATA


def update_sources_with_skills(
        clear_current_skills: bool,
        destination_players_path: Optional[str] = None,
        sources: Optional[Iterable[Source]] = None,
        players: Optional[List[Player]] = None,
        teams: Optional[List[Team]] = None):

    if not sources:
        sources = enumerate_latest_snapshot_sources_file()
        assert sources, "No Sources found in the Sources snapshot file."

    if not players:
        print('Loading players...')
        players = load_latest_snapshot_players_file()
        assert players, "No Players found in the Players snapshot file."

    if not teams:
        print('Loading teams...')
        teams: List[Team] = load_latest_snapshot_teams_file()
        assert teams, "No Teams found in the Teams snapshot file."

    teams: Dict[UUID, Team] = {t.guid: t for t in teams}

    if clear_current_skills:
        for player in players:
            player.skill.set_to_default()

    if not destination_players_path:
        destination_players_path = \
            join(SLAPP_APP_DATA, f"Snapshot-Players-{datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')}.json")

    players_dict: Dict[UUID, Player] = {p.guid: p for p in players}

    print("Sorting sources by date.")
    sources = sorted(sources, key=lambda s: s.start)
    for source in sources:
        has_changes = False
        print(f'Working on {source.name}')
        for bracket in source.brackets:
            for match in bracket.matches:
                if match.score.winning_team_index != -1:
                    match_dict = [
                        # [0] team 1
                        {
                            # 'id': match.team1_uuid,
                            'score': match.score.points[0],
                            # 'skills': {player_uuid: players_dict[player_uuid].skill for player_uuid in match.ids[match.team1_uuid]}
                            'skills': {}
                        },
                        # [1] team 2
                        {
                            # 'id': match.team2_uuid,
                            'score': match.score.points[1],
                            # 'skills': {player_uuid: players_dict[player_uuid].skill for player_uuid in match.ids[match.team2_uuid]}
                            'skills': {}
                        }
                    ]

                    match_dict[0]['skills'] = {}
                    for player_uuid in match.ids[match.team1_uuid]:
                        # If the skill is default, we should seed accordingly.
                        player = players_dict[player_uuid]
                        match_dict[0]['skills'][player_uuid] = \
                            player.skill if not player.skill.is_default else seed_new_skill(player, teams)

                    match_dict[1]['skills'] = {}
                    for player_uuid in match.ids[match.team2_uuid]:
                        # If the skill is default, we should seed accordingly.
                        player = players_dict[player_uuid]
                        match_dict[1]['skills'][player_uuid] = \
                            player.skill if not player.skill.is_default else seed_new_skill(player, teams)

                    skills_need_updating = False
                    for i in range(0, match_dict[0]['score']):
                        if len(match.players) == 4 and len(match.teams) == 2:
                            Skill.calculate_and_adjust_2v2(team1=list(match_dict[0]['skills'].values()),
                                                           team2=list(match_dict[1]['skills'].values()),
                                                           did_team_1_win=True)
                            skills_need_updating = True
                        else:
                            Skill.calculate_and_adjust_4v4(team1=list(match_dict[0]['skills'].values()),
                                                           team2=list(match_dict[1]['skills'].values()),
                                                           did_team_1_win=True)
                            skills_need_updating = True

                    for i in range(0, match_dict[1]['score']):
                        if len(match.players) == 4 and len(match.teams) == 2:
                            Skill.calculate_and_adjust_2v2(team1=list(match_dict[0]['skills'].values()),
                                                           team2=list(match_dict[1]['skills'].values()),
                                                           did_team_1_win=False)
                            skills_need_updating = True
                        else:
                            Skill.calculate_and_adjust_4v4(team1=list(match_dict[0]['skills'].values()),
                                                           team2=list(match_dict[1]['skills'].values()),
                                                           did_team_1_win=False)
                            skills_need_updating = True

                    # Put the skills back into the player objects if needed
                    if skills_need_updating:
                        has_changes = True
                        for j, player_uuid in enumerate(match.team1_players):
                            players_dict[player_uuid].skill = match_dict[0]['skills'][player_uuid]
                        for j, player_uuid in enumerate(match.team2_players):
                            players_dict[player_uuid].skill = match_dict[1]['skills'][player_uuid]

        if has_changes:
            print(f"Finished {source.name=}, changes made.")
        else:
            print(f"Finished {source.name=} but no changes.")

    print("All done, saving the Players snapshot to: " + destination_players_path)
    save_as_json_to_file(destination_players_path, list(map(Player.to_dict, players_dict.values())))


def seed_new_skill(player, teams: Dict[UUID, Team]) -> Skill:
    player_best_div = division.Unknown
    for team_id in player.teams:
        team: Team = teams.get(team_id, None)
        if team and team.current_div < player_best_div:
            player_best_div = team.current_div

    return Skill.from_division(player_best_div.normalised_value)


if __name__ == '__main__':
    update_sources_with_skills(clear_current_skills=True)
