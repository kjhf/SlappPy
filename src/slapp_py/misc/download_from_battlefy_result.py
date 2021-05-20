import glob
import json
import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Set, Iterable, Generator, Collection
from uuid import UUID

import dotenv
from dateutil.parser import isoparse
from os import makedirs
from os.path import exists, join, isfile

from battlefy_toolkit.caching.fileio import load_json_from_file, save_as_json_to_file
from battlefy_toolkit.utils.misc import assert_is_dict_recursive

from slapp_py.core_classes.bracket import Bracket
from slapp_py.core_classes.game import Game
from slapp_py.core_classes.player import Player
from slapp_py.core_classes.score import Score
from slapp_py.core_classes.source import Source
from slapp_py.core_classes.team import Team
from slapp_py.helpers.dict_helper import add_set_by_key, first_key
from slapp_py.helpers.fetch_helper import fetch_address
from slapp_py.misc.slapp_files_utils import get_latest_snapshot_sources_file, \
    load_latest_snapshot_players_file, load_latest_snapshot_sources_file, TOURNEY_TEAMS_SAVE_DIR, STAGES_SAVE_DIR, \
    TOURNEY_INFO_SAVE_DIR
from slapp_py.slapp_runner.slapipes import SLAPP_DATA_FOLDER

CLOUD_BACKEND = os.getenv("CLOUD_BACKEND")

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

BATTLEFY_LOW_INK_ADDRESS_FORMAT: str = 'https://battlefy.com/low-ink//%s/participants'
TOURNAMENT_INFO_MINIMAL_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/tournaments/%s'
TEAMS_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/tournaments/%s/teams'


def download_from_battlefy(ids: Union[str, List[str]], force: bool = False) -> Generator[List[dict], None, None]:
    if isinstance(ids, str):
        if ids.startswith('['):
            ids = json.loads(ids)
        else:
            ids = [ids]

    for id_to_fetch in ids:
        # This also gets the info file.
        yield get_or_fetch_tourney_teams_file(id_to_fetch, force=force)


def get_or_fetch_tourney_info_file(tourney_id_to_fetch: str, force: bool = False) -> Optional[dict]:
    if not exists(TOURNEY_INFO_SAVE_DIR):
        makedirs(TOURNEY_INFO_SAVE_DIR)

    filename: str = f'{tourney_id_to_fetch}.json'
    matched_tourney_files = glob.glob(join(TOURNEY_INFO_SAVE_DIR, f'*{filename}'))
    full_path = matched_tourney_files[0] if len(matched_tourney_files) else join(TOURNEY_INFO_SAVE_DIR, filename)
    if force or not isfile(full_path):
        tourney_contents = fetch_address(TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT.format(tourney_id=tourney_id_to_fetch))

        if len(tourney_contents) == 0:
            print(f'ERROR get_or_fetch_tournament_file: Nothing exists at {tourney_id_to_fetch=}.')
            return None

        if isinstance(tourney_contents, list):
            tourney_contents = tourney_contents[0]

        if '_id' in tourney_contents and 'slug' in tourney_contents and 'startTime' in tourney_contents:
            start_time: datetime = isoparse(tourney_contents['startTime'])
            filename = f'{start_time.strftime("%Y-%m-%d")}-{tourney_contents["slug"]}-' \
                       f'{tourney_id_to_fetch}.json'
            full_path = join(TOURNEY_INFO_SAVE_DIR, filename)
        else:
            print(f"Couldn't name the downloaded tourney info file: "
                  f"{'_id' in tourney_contents=} "
                  f"{'slug' in tourney_contents=} "
                  f"{'startTime' in tourney_contents=}")

        print(f'OK! (Saved read tourney info file to {full_path})')

        save_as_json_to_file(full_path, tourney_contents)
    else:
        tourney_contents = load_json_from_file(full_path)

    if isinstance(tourney_contents, list):
        tourney_contents = tourney_contents[0]
    return tourney_contents


def get_stage_ids_for_tourney(tourney_id_to_fetch: str, force: bool = False) -> Set[str]:
    """"Returns stage (id, name) for the specified tourney"""
    _tourney_contents = get_or_fetch_tourney_info_file(tourney_id_to_fetch, force=force) or set()
    return set(_tourney_contents.get('stageIDs', set()))


def get_or_fetch_stage_file(tourney_id_to_fetch: str, stage_id_to_fetch: str, force: bool = False) -> Optional[dict]:
    if not tourney_id_to_fetch or not stage_id_to_fetch:
        raise ValueError(f'get_or_fetch_stage_file: Expected ids. {tourney_id_to_fetch=} {stage_id_to_fetch=}')

    _stages = get_stage_ids_for_tourney(tourney_id_to_fetch, force=force)
    _stages = set([stage_id for stage_id in _stages if is_valid_battlefy_id(stage_id)])
    assert stage_id_to_fetch in _stages

    _stage_path = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__(),
                       f'{stage_id_to_fetch}-battlefy.json')
    if force or not isfile(_stage_path):
        _stage_contents = fetch_address(STAGE_INFO_FETCH_ADDRESS_FORMAT.format(stage_id=stage_id_to_fetch))
        if len(_stage_contents) == 0:
            print(f'ERROR get_or_fetch_stage_file: Nothing exists at {tourney_id_to_fetch=} / {stage_id_to_fetch=}')
            return None

        # Save the data
        _stage_dir = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__())
        if not exists(_stage_dir):
            makedirs(_stage_dir)
        save_as_json_to_file(_stage_path, _stage_contents)
        print(f'OK! (Saved read stage {_stage_path})')
    else:
        _stage_contents = load_json_from_file(_stage_path)

    if isinstance(_stage_contents, list):
        _stage_contents = _stage_contents[0]
    return _stage_contents


def get_or_fetch_standings_file(tourney_id_to_fetch: str, stage_id_to_fetch: str, force: bool = False) -> Optional[dict]:
    _stages = get_stage_ids_for_tourney(tourney_id_to_fetch)
    _stages = set([stage_id for stage_id in _stages if is_valid_battlefy_id(stage_id)])
    assert stage_id_to_fetch in _stages

    _stage_path = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__(),
                       f'{stage_id_to_fetch}-standings.json')
    if force or not isfile(_stage_path):
        _stage_contents = fetch_address(STAGE_STANDINGS_FETCH_ADDRESS_FORMAT.format(stage_id=stage_id_to_fetch))
        if len(_stage_contents) == 0:
            print(f'ERROR get_or_fetch_standings_file: Nothing exists at {tourney_id_to_fetch=} / {stage_id_to_fetch=}')
            return None

        # Save the data
        _stage_dir = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__())
        if not exists(_stage_dir):
            makedirs(_stage_dir)
        save_as_json_to_file(_stage_path, _stage_contents)
        print(f'OK! (Saved read stage {_stage_path})')
    else:
        _stage_contents = load_json_from_file(_stage_path)
    return _stage_contents


def get_or_fetch_tourney_teams_file(tourney_id_to_fetch: str, force: bool = False) -> Optional[List[dict]]:
    if not exists(TOURNEY_TEAMS_SAVE_DIR):
        makedirs(TOURNEY_TEAMS_SAVE_DIR)

    filename: str = f'{tourney_id_to_fetch}.json'
    matched_tourney_files = glob.glob(join(TOURNEY_TEAMS_SAVE_DIR, f'*{filename}'))
    full_path = matched_tourney_files[0] if len(matched_tourney_files) else join(TOURNEY_TEAMS_SAVE_DIR, filename)
    if force or not isfile(full_path):
        teams_contents = fetch_address(TEAMS_FETCH_ADDRESS_FORMAT % tourney_id_to_fetch)

        if len(teams_contents) == 0:
            print(f'ERROR get_or_fetch_tourney_teams_file: Nothing exists at {tourney_id_to_fetch=}.')
            return None

        # To name this file, we need the tourney file that goes with it.
        info_contents = get_or_fetch_tourney_info_file(tourney_id_to_fetch, force=force)

        if '_id' in info_contents and 'slug' in info_contents and 'startTime' in info_contents:
            start_time: datetime = isoparse(info_contents['startTime'])
            filename = f'{start_time.strftime("%Y-%m-%d")}-{info_contents["slug"]}-' \
                       f'{tourney_id_to_fetch}.json'
            full_path = join(TOURNEY_TEAMS_SAVE_DIR, filename)
        else:
            print(f"Couldn't name the downloaded tourney teams file as the tourney info is incomplete: "
                  f"{'_id' in info_contents=} "
                  f"{'slug' in info_contents=} "
                  f"{'startTime' in info_contents=}")

        print(f'OK! (Saved read tourney to {full_path})')

        # else
        save_as_json_to_file(full_path, teams_contents)
        print(f'OK! (Saved read tourney teams file to {full_path})')

        if force:
            # We just downloaded so no need to force get this again
            for stage_id in get_stage_ids_for_tourney(tourney_id_to_fetch, force=False):
                get_or_fetch_stage_file(tourney_id_to_fetch, stage_id, force=True)

    else:
        teams_contents = load_json_from_file(full_path)

    return teams_contents


_global_player_local_id_to_slapp_id = dict()


def player_local_id_to_slapp_id(_local_player_id: Union[str, UUID],
                                _player_id_to_persistent_id: Dict[str, str],
                                _players: Iterable[Player]) -> Optional[UUID]:
    global _global_player_local_id_to_slapp_id
    if _local_player_id in _global_player_local_id_to_slapp_id:
        return _global_player_local_id_to_slapp_id[_local_player_id]

    # Search for the persistent id for this player.
    _persistent_id = _player_id_to_persistent_id.get(_local_player_id.__str__())
    if _persistent_id:
        slapp_id = player_persistent_id_to_slapp_id(_persistent_id, _players)
        _global_player_local_id_to_slapp_id[_local_player_id] = slapp_id
        return slapp_id
    else:
        # print(f'Could not translate local player ID ({_local_player_id})'
        #       f' into a persistent Player Id.'
        #       # f'_player_id_to_persistent_id={", ".join(_player_id_to_persistent_id.keys())}')
        return None


_global_player_persistent_id_to_slapp_id = dict()


def player_persistent_id_to_slapp_id(_persistent_player_id: Union[str, UUID],
                                     _players: Iterable[Player]) -> Optional[UUID]:
    global _global_player_persistent_id_to_slapp_id
    if isinstance(_persistent_player_id, UUID):
        _persistent_player_id = _persistent_player_id.__str__()

    if _persistent_player_id in _global_player_persistent_id_to_slapp_id:
        return _global_player_persistent_id_to_slapp_id[_persistent_player_id]

    # Search for the Slapp record of this player.
    _found_player = next(
        (player_in_source for player_in_source in _players
         if _persistent_player_id in player_in_source.battlefy.battlefy_persistent_id_strings), None)
    if _found_player:
        _global_player_persistent_id_to_slapp_id[_persistent_player_id] = _found_player.guid.__str__()
        return _found_player.guid
    else:
        print(f'Could not translate persistentPlayerID ({_persistent_player_id}) '
              f'into a Slapp Player Id.')
        return None


def team_persistent_id_to_slapp_id(_persistent_team_id: Union[str, UUID], _teams: Iterable[Team]) -> Optional[UUID]:
    # Search for the Slapp record of this team.
    _found_team = next(
        (team_in_source for team_in_source in _teams
         if _persistent_team_id.__str__() in team_in_source.battlefy_persistent_id_strings), None)
    if _found_team:
        return _found_team.guid
    else:
        print(f'Could not translate persistentTeamID ({_persistent_team_id}) '
              f'into a Slapp Team Id.')
        return None


def is_valid_battlefy_id(_battlefy_id: str) -> bool:
    return 20 <= len(_battlefy_id) < 30 and re.match("^[A-Fa-f0-9]*$", _battlefy_id)


def get_source_by_tourney_id(tourney_id: str,
                             sources: List[Source]) -> Optional[Source]:
    return next((s for s in sources if s.tournament_id == tourney_id), None)


def add_tourney_placement_to_source(tourney_id: str,
                                    players: Iterable[Player],
                                    sources: List[Source]) -> bool:
    stage_ids = set([stage_id for stage_id in get_stage_ids_for_tourney(tourney_id)
                     if is_valid_battlefy_id(stage_id)])
    if len(stage_ids) == 0:
        print(f'No stages found in {tourney_id=}.')
        return False

    # Find the suitable source in the latest sources snapshot
    source = get_source_by_tourney_id(tourney_id, sources)
    if not source:
        print(f"Could not find a source in the snapshot that matches {tourney_id=}. Not adding.")
        return False

    if source.brackets:
        print(f"Brackets already exist for this source. Skipping.")
        return False

    _global_player_local_id_to_slapp_id.clear()

    # For each stage, translate the stage bracket into a Bracket object
    for stage_id in stage_ids:
        stage_contents = get_or_fetch_stage_file(tourney_id, stage_id, force=False)
        if not stage_contents:
            continue

        bracket: Bracket = Bracket(name=stage_contents["name"])

        # We can get the relevant team from the sources file and matching against battlefy persistent team id
        # For now, let's store the teams in the bracket information - we'll have to convert them later.
        player_id_to_persistent_id_lookup = dict()
        for match in stage_contents["matches"]:
            if match["isBye"]:
                continue

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

            if "persistentTeamID" not in team1 or "persistentTeamID" not in team2:
                print(f"Incomplete team: persistentTeamID not defined. {team_result_1=} or {team_result_2=}")
                continue

            team1_slapp_id = team_persistent_id_to_slapp_id(team1["persistentTeamID"], source.teams) or None
            team1_player_slapp_ids = []
            for player_dict in team1.get("players", []):
                player_persistent_id = player_dict.get("persistentPlayerID")  # else None
                if player_persistent_id:
                    team1_player_slapp_ids.append(player_persistent_id_to_slapp_id(player_persistent_id, players))
                    player_id_to_persistent_id_lookup[player_dict["_id"]] = player_persistent_id
                else:
                    print(f"Skipping player in {json.dumps(player_dict)} - there's no persistentPlayerID.")

            team2_slapp_id = team_persistent_id_to_slapp_id(team2["persistentTeamID"], source.teams) or None
            team2_player_slapp_ids = []
            for player_dict in team2.get("players", []):
                player_persistent_id = player_dict.get("persistentPlayerID")  # else None
                if player_persistent_id:
                    team2_player_slapp_ids.append(player_persistent_id_to_slapp_id(player_persistent_id, players))
                    player_id_to_persistent_id_lookup[player_dict["_id"]] = player_persistent_id
                else:
                    print(f"Skipping player in {json.dumps(player_dict)} - there's no persistentPlayerID.")

            if team1_slapp_id and team2_slapp_id:
                ids_dictionary = {
                    team1_slapp_id: team1_player_slapp_ids,
                    team2_slapp_id: team2_player_slapp_ids,
                }
                game = Game(score=Score([team_result_1.get("score", -1), team_result_2.get("score", -1)]),
                            ids=ids_dictionary)
                bracket.matches.add(game)
            else:
                print(f"Skipping game in {json.dumps(match)} - the team(s) were not matched to Slapp ids.")

            # Loop to next match

        # Add placements
        standings_contents = get_or_fetch_standings_file(tourney_id, stage_id, force=False)
        if standings_contents:
            # If place is present (i.e. for finals), order by that.
            standings_placements = {}

            first_node = first_key(standings_contents)
            if isinstance(first_node, str):
                first_node = standings_contents[first_node]

            if first_node.get('place', False):
                standings_placements = \
                    sorted(standings_contents,
                           key=lambda k:
                           (
                               int(k.get("place", 99999)),
                               k.get("team", {}).get("name", '')
                           ))

            # Otherwise, work out the order:
            #  1. The team's match wins ["matchWinPercentage"]
            #  2. The opponent's match win percentage ["opponentsMatchWinPercentage"]
            #  3. The team's game win percentage ["gameWinPercentage"]
            #  4. The opponent's opponent's match win percentage ["opponentsOpponentsMatchWinPercentage"]
            elif first_node.get('matchWinPercentage') \
                    and first_node.get('opponentsMatchWinPercentage') \
                    and first_node.get('gameWinPercentage') \
                    and first_node.get('opponentsOpponentsMatchWinPercentage'):
                standings_placements = sorted(standings_contents,
                                              key=lambda k:
                                              (
                                                  int(k.get("matchWinPercentage", -1) or -1),
                                                  int(k.get("opponentsMatchWinPercentage", -1) or -1),
                                                  int(k.get("gameWinPercentage", -1) or -1),
                                                  int(k.get("opponentsOpponentsMatchWinPercentage", -1) or -1)
                                              ), reverse=True)
            else:
                print(f'ERROR: Skipping calculation of placements as this node does not have '
                      f'the required fields: {json.dumps(first_node)}')

            for i, standing_node in enumerate(standings_placements):
                place = (i + 1)
                standing_node: Dict[str, Any]

                add_set_by_key(dictionary=bracket.placements.players_by_placement,
                               key=place,
                               values={
                                   player_local_id_to_slapp_id(
                                       _local_player_id=local_id,
                                       _player_id_to_persistent_id=player_id_to_persistent_id_lookup,
                                       _players=players
                                   ) or ''
                                   for local_id in standing_node.get("team", {}).get("playerIDs", [])
                               })
                bracket.placements.players_by_placement[place].discard('')

                add_set_by_key(dictionary=bracket.placements.teams_by_placement,
                               key=place,
                               values={
                                   team_persistent_id_to_slapp_id(
                                       _persistent_team_id=standing_node.get("team", {}).get("persistentTeamID", ''),
                                       _teams=source.teams)
                                   or ''
                               })
                bracket.placements.teams_by_placement[place].discard('')

        # Add to the Source
        source.brackets.append(bracket)

    # Finish up
    # Save the snapshot file
    dict_to_save = source.to_dict()
    assert_is_dict_recursive(dict_to_save)
    return True


def update_sources_with_placements(tourney_ids: Optional[Collection[str]] = None,
                                   destination_sources_path: Optional[str] = None,
                                   sources: Optional[List[Source]] = None,
                                   players: Optional[List[Player]] = None):

    if not sources:
        print('Loading sources...')
        sources = load_latest_snapshot_sources_file()
        assert sources, "No Sources found in the Sources snapshot file."

    if not players:
        print('Loading players...')
        players = load_latest_snapshot_players_file()
        assert players, "No Players found in the Players snapshot file."

    if not tourney_ids:
        tourney_ids = set([source.tournament_id for source in sources
                           if not source.brackets
                           and '-stat.ink-' not in source.name
                           and '-LUTI-' not in source.name
                           and 'Twitter-' not in source.name])

    if not destination_sources_path:
        destination_sources_path = \
            join(SLAPP_DATA_FOLDER, f"Snapshot-Sources-{datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')}.json")

    # Filter ids that are less than 20 characters or more than 30 (id is probably not correct) --
    # expected 24 chars, and hex numbers only.
    original_count = len(tourney_ids)
    tourney_ids = set([tourney_id for tourney_id in tourney_ids if is_valid_battlefy_id(tourney_id)])
    actual_count = len(tourney_ids)
    if original_count != actual_count:
        print(f'Some ids were filtered as they were invalid ({original_count} -> {len(tourney_ids)})')

    for i, tourney_id in enumerate(tourney_ids):
        print(f'[{i+1}/{actual_count}] Working on {tourney_id=}')
        has_changes = add_tourney_placement_to_source(tourney_id, players, sources)
        if has_changes:
            print(f"Finished {tourney_id=}, changes made.")
        else:
            print(f"Finished {tourney_id=} but no changes.")

    print(f"All done, saving sources to: " + destination_sources_path)
    save_as_json_to_file(destination_sources_path, [source.to_dict() for source in sources])


def force_update_from_battlefy_slug(incoming_slug: str):
    """Redownload all sources that contain a given Battlefy Slug"""
    sources = [source for source in load_latest_snapshot_sources_file()
               if '-stat.ink-' not in source.name
               and '-LUTI-' not in source.name
               and 'Twitter-' not in source.name]

    filtered = \
        [
            # Filtering sources, if any ...
            source for source in sources if any(
                # players in this source...
                any(
                    # have a battlefy slug that matches our input (lower-cased)
                    incoming_slug.lower() == slug.value.lower() for slug in player.battlefy.slugs
                ) for player in source.players
            )
        ]

    for source in filtered:
        print("Force downloading " + source.name)
        _ = list(download_from_battlefy(source.tournament_id, force=True))


# if __name__ == '__main__':
#     dotenv.load_dotenv()
#     force_update_from_battlefy_slug()
#     sys.exit(0)

if __name__ == '__main__':
    dotenv.load_dotenv()
    # Ask for the tournament to update
    global_ids = \
        [
            input('Tournament id? (* will update all, DISCARD will update all and discard old brackets)')
        ]

    if not len(global_ids):
        print('Nothing specified.')
        sys.exit(0)

    print('Loading sources...')
    global_sources: List[Source] = load_latest_snapshot_sources_file()
    assert global_sources
    global_snapshot_sources_path = get_latest_snapshot_sources_file()

    if global_ids[0] == '*':
        global_ids = set([source.tournament_id for source in global_sources
                          if not source.brackets
                          and '-stat.ink-' not in source.name
                          and '-LUTI-' not in source.name
                          and 'Twitter-' not in source.name])

    elif global_ids[0] == 'DISCARD':
        global_ids = set([source.tournament_id for source in global_sources
                          if '-stat.ink-' not in source.name
                          and '-LUTI-' not in source.name
                          and 'Twitter-' not in source.name])

    update_sources_with_placements(tourney_ids=global_ids,
                                   destination_sources_path=global_snapshot_sources_path + ".edited.json",
                                   sources=global_sources)
