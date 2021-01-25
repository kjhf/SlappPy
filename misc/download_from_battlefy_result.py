import glob
import json
import sys
from datetime import datetime
from typing import List

from dateutil.parser import isoparse
from os import makedirs
from os.path import exists, join, isfile

from core_classes.bracket import Bracket
from core_classes.game import Game
from core_classes.score import Score
from core_classes.source import Source
from helpers.dict_helper import add_set_by_key
from tokens import SLAPP_APP_DATA, CLOUD_BACKEND
from misc import utils
from misc.utils import fetch_address, save_to_file

STAGE_STANDINGS_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + "/stages/{stage_id}/latest-round-standings"

STAGE_INFO_FETCH_ADDRESS_FORMAT: str = \
    'https://api.battlefy.com/stages/{stage_id}?extend%5Bmatches%5D%5Btop.team%5D%5Bplayers%5D%5Buser%5D=true' \
    '&extend%5Bmatches%5D%5Btop.team%5D%5BpersistentTeam%5D=true' \
    '&extend%5Bmatches%5D%5Bbottom.team%5D%5Bplayers%5D%5Buser%5D=true' \
    '&extend%5Bmatches%5D%5Bbottom.team%5D%5BpersistentTeam%5D=true' \
    '&extend%5Bgroups%5D%5Bteams%5D=true' \
    '&extend%5Bgroups%5D%5Bmatches%5D%5Btop.team%5D%5Bplayers%5D%5Buser%5D=true' \
    '&extend%5Bgroups%5D%5Bmatches%5D%5Btop.team%5D%5BpersistentTeam%5D=true' \
    '&extend%5Bgroups%5D%5Bmatches%5D%5Bbottom.team%5D%5Bplayers%5D%5Buser%5D=true' \
    '&extend%5Bgroups%5D%5Bmatches%5D%5Bbottom.team%5D%5BpersistentTeam%5D=true'

TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT: str = \
    "https://api.battlefy.com/tournaments/{tourney_id}?" \
    "extend%5Bcampaign%5D%5Bsponsor%5D=true" \
    "&extend%5Bstages%5D%5B%24query%5D%5BdeletedAt%5D%5B%24exists%5D=false" \
    "&extend%5Bstages%5D%5B%24opts%5D%5Bname%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5Bbracket%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5BstartTime%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5BendTime%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5Bschedule%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5BmatchCheckinDuration%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5BhasCheckinTimer%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5BhasStarted%5D=1" \
    "&extend%5Bstages%5D%5B%24opts%5D%5BhasMatchCheckin%5D=1" \
    "&extend%5Borganization%5D%5Bowner%5D%5B%24opts%5D%5Btimezone%5D=1" \
    "&extend%5Borganization%5D%5B%24opts%5D%5Bname%5D=1" \
    "&extend%5Borganization%5D%5B%24opts%5D%5Bslug%5D=1" \
    "&extend%5Borganization%5D%5B%24opts%5D%5BownerID%5D=1" \
    "&extend%5Borganization%5D%5B%24opts%5D%5BlogoUrl%5D=1" \
    "&extend%5Borganization%5D%5B%24opts%5D%5BbannerUrl%5D=1" \
    "&extend%5Borganization%5D%5B%24opts%5D%5Bfeatures%5D=1" \
    "&extend%5Borganization%5D%5B%24opts%5D%5Bfollowers%5D=1" \
    "&extend%5Bgame%5D=true" \
    "&extend%5Bstreams%5D%5B%24query%5D%5BdeletedAt%5D%5B%24exists%5D=false"
# TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/tournaments/%s'
TOURNAMENTS_SAVE_DIR = SLAPP_APP_DATA + "\\tournaments"


def get_or_fetch_tournament_file(tourney_id_to_fetch: str) -> dict:
    if not exists(TOURNAMENTS_SAVE_DIR):
        makedirs(TOURNAMENTS_SAVE_DIR)

    filename: str = f'{tourney_id_to_fetch}.json'
    matched_tourney_files = glob.glob(join(TOURNAMENTS_SAVE_DIR, f'*-{filename}'))
    full_path = matched_tourney_files[0] if len(matched_tourney_files) else join(TOURNAMENTS_SAVE_DIR, filename)
    if not isfile(full_path):
        tourney_contents = fetch_address(TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT.format(tourney_id=tourney_id_to_fetch))

        if len(tourney_contents) == 0:
            print(f'Nothing exists at {tourney_id_to_fetch}.')
        else:
            if '_id' in tourney_contents and 'slug' in tourney_contents and 'startTime' in tourney_contents:
                start_time: datetime = isoparse(tourney_contents['startTime'])
                filename = f'{start_time.strftime("%Y-%m-%d")}-{tourney_contents["slug"]}-' \
                           f'{tourney_id_to_fetch}.json'
                full_path = join(TOURNAMENTS_SAVE_DIR, filename)
            print(f'OK! (Saved read tourney to {full_path})')

        save_to_file(full_path, json.dumps(tourney_contents))
    else:
        tourney_contents = utils.load_json_from_file(full_path)

    if isinstance(tourney_contents, list):
        tourney_contents = tourney_contents[0]
    return tourney_contents


def get_stage_ids_for_tourney(tourney_id_to_fetch: str) -> List[str]:
    """"Returns stage (id, name) for the specified tourney"""
    _tourney_contents = get_or_fetch_tournament_file(tourney_id_to_fetch)
    return _tourney_contents['stageIDs']


def get_or_fetch_stage_file(tourney_id_to_fetch: str, stage_id_to_fetch: str) -> dict:
    _stages = get_stage_ids_for_tourney(tourney_id_to_fetch)
    assert stage_id_to_fetch in _stages

    _stage_path = join(TOURNAMENTS_SAVE_DIR, 'stages', tourney_id_to_fetch.__str__(),
                       f'{stage_id_to_fetch}-battlefy.json')
    if not isfile(_stage_path):
        _stage_contents = fetch_address(STAGE_INFO_FETCH_ADDRESS_FORMAT.format(stage_id=stage_id_to_fetch))
        assert len(_stage_contents) != 0, f'Nothing exists at {stage_id_to_fetch}'

        # Save the data
        _stage_dir = join(TOURNAMENTS_SAVE_DIR, 'stages', tourney_id_to_fetch.__str__())
        if not exists(_stage_dir):
            makedirs(_stage_dir)
        save_to_file(_stage_path, json.dumps(_stage_contents))
        print(f'OK! (Saved read stage {_stage_path})')
    else:
        _stage_contents = utils.load_json_from_file(_stage_path)

    if isinstance(_stage_contents, list):
        _stage_contents = _stage_contents[0]
    return _stage_contents


def get_or_fetch_standings_file(tourney_id_to_fetch: str, stage_id_to_fetch: str) -> dict:
    _stages = get_stage_ids_for_tourney(tourney_id_to_fetch)
    assert stage_id_to_fetch in _stages

    _stage_path = join(TOURNAMENTS_SAVE_DIR, 'stages', tourney_id_to_fetch.__str__(),
                       f'{stage_id_to_fetch}-standings.json')
    if not isfile(_stage_path):
        _stage_contents = fetch_address(STAGE_STANDINGS_FETCH_ADDRESS_FORMAT.format(stage_id=stage_id_to_fetch))
        assert len(_stage_contents) != 0, f'Nothing exists at {stage_id_to_fetch}'

        # Save the data
        _stage_dir = join(TOURNAMENTS_SAVE_DIR, 'stages', tourney_id_to_fetch.__str__())
        if not exists(_stage_dir):
            makedirs(_stage_dir)
        save_to_file(_stage_path, json.dumps(_stage_contents))
        print(f'OK! (Saved read stage {_stage_path})')
    else:
        _stage_contents = utils.load_json_from_file(_stage_path)

    return _stage_contents


if __name__ == '__main__':
    # Find the latest snapshot file.
    matched_snapshot_files = glob.glob(join(SLAPP_APP_DATA, f'Snapshot-Sources-*.json'))
    assert len(matched_snapshot_files), "Snapshot file not found."
    snapshot_path = matched_snapshot_files[-1]
    print(f'Using snapshot file: {snapshot_path}')

    # Ask for the tournament to update
    ids = \
        [
            input('Tournament id? (* will update all)')
        ]

    if not ids:
        print('Nothing specified.')
        sys.exit(0)

    print('Loading sources...')
    sources: List[dict] = utils.load_json_from_file(snapshot_path)

    if ids[0] == '*':
        # rpartition finds the last '-', we want the substring past that to the end which is [2].
        ids = set([source["Name"].rpartition('-')[2] for source in sources])

    for tourney_id in ids:
        stage_ids = get_stage_ids_for_tourney(tourney_id)

        # Find the suitable source in the latest sources snapshot
        source = None
        for source_dict_item in sources:
            source_name: str = source_dict_item["Name"]
            if not source_name.endswith(tourney_id):
                continue
            # else set Source object and
            # remove the source dictionary as we'll be replacing it
            source = Source.from_dict(source_dict_item)
            sources.remove(source_dict_item)

        if source:
            # For each stage, translate the stage bracket into a Bracket object
            for stage_id in stage_ids:
                stage_contents = get_or_fetch_stage_file(tourney_id, stage_id)
                bracket: Bracket = Bracket(name=stage_contents["name"])

                # We can get the relevant team from the sources file and matching against battlefy persistent team id
                # For now, let's store the teams in the bracket information - we'll have to convert them later.
                for match in stage_contents["matches"]:
                    if match["isBye"]:
                        continue

                    game = Game()
                    team_result_1 = match.get("top")
                    team_result_2 = match.get("bottom")

                    if not team_result_1 or not team_result_2:
                        print(f"Incomplete team result top/bottom, see {match=}")
                        continue

                    team1 = team_result_1.get("team")
                    team2 = team_result_2.get("team")

                    if not team1 or not team2:
                        print(f"Incomplete team data, see {team_result_1=} or {team_result_2=}")
                        continue

                    tournament_player_ids_to_persistent = {}

                    game.teams.add(team1["persistentTeamID"])
                    for player_dict in team1.get("players", []):
                        player_persistent_id = player_dict.get("persistentPlayerID")  # else None
                        if player_persistent_id:
                            game.players.add(player_persistent_id)
                            tournament_player_ids_to_persistent[player_dict.get("_id")] = player_persistent_id

                    game.teams.add(team2["persistentTeamID"])
                    for player_dict in team2.get("players", []):
                        player_persistent_id = player_dict.get("persistentPlayerID")  # else None
                        if player_persistent_id:
                            game.players.add(player_persistent_id)
                            tournament_player_ids_to_persistent[player_dict.get("_id")] = player_persistent_id

                    game.score = Score([team_result_1["score"], team_result_2["score"]])
                    bracket.matches.add(game)
                    bracket.players |= game.players
                    bracket.teams |= game.teams

                    # Add placements
                    standings_contents = get_or_fetch_standings_file(tourney_id, stage_id)
                    for standing_node in standings_contents:
                        place = standings_contents["place"]

                        player_uuids_set = set()

                        # For each player id, attempt to convert to a Slapp uuid
                        for player_id in set(standings_contents["team"]["playerIDs"]):
                            persistent_player_id = tournament_player_ids_to_persistent.get(player_id)
                            if persistent_player_id:
                                # First, search persistent ids.
                                found_player = next((player_in_source for player_in_source in source.players
                                                     if player_id in player_in_source.battlefy.persistent_ids), None)
                                if found_player:
                                    player_uuids_set.add(found_player.guid)
                                else:
                                    print(f'Could not translate persistentPlayerID ({persistent_player_id}) '
                                          f'into a Slapp Player Id.')
                            else:
                                print(f'Could not translate playerID ({player_id}) into a Slapp Player Id.')

                        # For each team id, attempt to convert to a Slapp uuid
                        team_uuid_as_set = set()

                        # First, search persistent ids.
                        team_id = standings_contents["team"]["persistentTeamID"]
                        found_team = next((team_in_source
                                           for team_in_source in source.teams
                                           if team_id in team_in_source.battlefy_persistent_team_ids), None)
                        if found_team:
                            team_uuid_as_set.add(found_team.guid)
                        else:
                            print(f'Could not translate persistentTeamID ({team_id}) into a Slapp Team Id.')

                        add_set_by_key(dictionary=bracket.placements.players_by_placement,
                                       key=place,
                                       values=player_uuids_set)

                        add_set_by_key(dictionary=bracket.placements.teams_by_placement,
                                       key=place,
                                       values=team_uuid_as_set)

                # Add to the Source
                source.brackets.append(bracket)

            # Finish up
            # Save the snapshot file
            dict_to_save = source.to_dict()
            utils.assert_is_dict_recursive(dict_to_save)
            sources.append(dict_to_save)
            json.dump(sources, snapshot_path + "_edited.json")
            # TODO:
            #  Do clout calculator and get if banned from Low Ink status
            #  Then: Load in Slapp and check compatibility

        else:
            print("Could not find a source in the snapshots that matches this tournament id.")
