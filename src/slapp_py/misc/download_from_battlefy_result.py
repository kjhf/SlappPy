import glob
import json
import os
from datetime import datetime
from typing import List, Optional, Union, Set, Generator

from dateutil.parser import isoparse
from os import makedirs
from os.path import exists, join, isfile

from battlefy_toolkit.caching.fileio import load_json_from_file, save_as_json_to_file

from slapp_py.helpers.fetch_helper import fetch_address
from slapp_py.misc.models.tournament_information import TournamentInformation
from slapp_py.misc.slapp_files_utils import \
    load_latest_snapshot_sources_file, TOURNEY_TEAMS_SAVE_DIR, STAGES_SAVE_DIR, \
    TOURNEY_INFO_SAVE_DIR
from slapp_py.helpers.battlefy_helper import is_valid_battlefy_id, filter_non_battlefy_source

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
        print(f"Fetching tourney_info_file as {force=} or {isfile(full_path)=}")
        tourney_contents = fetch_address(TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT.format(tourney_id=tourney_id_to_fetch), assert_success=force)

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

        save_as_json_to_file(full_path, tourney_contents, indent=0)
    else:
        tourney_contents = load_json_from_file(full_path)

    if isinstance(tourney_contents, list):
        tourney_contents = tourney_contents[0]
    return tourney_contents


def get_stage_ids_for_tourney(tourney_id_to_fetch: str, force: bool = False) -> Set[str]:
    """"Returns stage (id, name) for the specified tourney"""
    _tourney_contents = get_or_fetch_tourney_info_file(tourney_id_to_fetch, force=force) or set()
    return set(_tourney_contents.get('stageIDs', set()))


def get_or_fetch_tourney_information(tourney_id_to_fetch: str, force: bool = False) -> TournamentInformation:
    """"Returns the Tournament Information for the specified tourney"""
    _tourney_contents = get_or_fetch_tourney_info_file(tourney_id_to_fetch, force=force) or {}
    return TournamentInformation.from_dict(_tourney_contents)


def get_or_fetch_stage_file(tourney_id_to_fetch: str, stage_id_to_fetch: str, force: bool = False) -> Optional[dict]:
    if not tourney_id_to_fetch or not stage_id_to_fetch:
        raise ValueError(f'get_or_fetch_stage_file: Expected ids. {tourney_id_to_fetch=} {stage_id_to_fetch=}')

    _stages = get_stage_ids_for_tourney(tourney_id_to_fetch, force=force)
    _stages = {stage_id for stage_id in _stages if is_valid_battlefy_id(stage_id)}
    assert stage_id_to_fetch in _stages

    _stage_path = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__(),
                       f'{stage_id_to_fetch}-battlefy.json')
    if force or not isfile(_stage_path):
        _stage_contents = fetch_address(STAGE_INFO_FETCH_ADDRESS_FORMAT.format(stage_id=stage_id_to_fetch), assert_success=force)
        if len(_stage_contents) == 0:
            print(f'ERROR get_or_fetch_stage_file: Nothing exists at {tourney_id_to_fetch=} / {stage_id_to_fetch=}')
            return None

        # Save the data
        _stage_dir = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__())
        if not exists(_stage_dir):
            makedirs(_stage_dir)
        save_as_json_to_file(_stage_path, _stage_contents, indent=0)
        print(f'OK! (Saved read stage {_stage_path})')
    else:
        _stage_contents = load_json_from_file(_stage_path)

    if isinstance(_stage_contents, list):
        _stage_contents = _stage_contents[0]
    return _stage_contents


def get_or_fetch_standings_file(tourney_id_to_fetch: str, stage_id_to_fetch: str, force: bool = False) -> Optional[dict]:
    _stages = get_stage_ids_for_tourney(tourney_id_to_fetch)
    _stages = {stage_id for stage_id in _stages if is_valid_battlefy_id(stage_id)}
    assert stage_id_to_fetch in _stages

    _stage_path = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__(),
                       f'{stage_id_to_fetch}-standings.json')
    if force or not isfile(_stage_path):
        _stage_contents = fetch_address(STAGE_STANDINGS_FETCH_ADDRESS_FORMAT.format(stage_id=stage_id_to_fetch), assert_success=force)
        if len(_stage_contents) == 0:
            print(f'ERROR get_or_fetch_standings_file: Nothing exists at {tourney_id_to_fetch=} / {stage_id_to_fetch=}')
            return None

        # Save the data
        _stage_dir = join(STAGES_SAVE_DIR, tourney_id_to_fetch.__str__())
        if not exists(_stage_dir):
            makedirs(_stage_dir)
        save_as_json_to_file(_stage_path, _stage_contents, indent=0)
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
        teams_contents = fetch_address(TEAMS_FETCH_ADDRESS_FORMAT % tourney_id_to_fetch, assert_success=force)

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
        save_as_json_to_file(full_path, teams_contents, indent=0)
        print(f'OK! (Saved read tourney teams file to {full_path})')

        if force:
            # We just downloaded so no need to force get this again
            for stage_id in get_stage_ids_for_tourney(tourney_id_to_fetch, force=False):
                get_or_fetch_stage_file(tourney_id_to_fetch, stage_id, force=True)

    else:
        teams_contents = load_json_from_file(full_path)

    return teams_contents


def force_update_from_battlefy_slug(incoming_slug: str):
    """Redownload all sources that contain a given Battlefy Slug"""
    sources = [source for source in load_latest_snapshot_sources_file()
               if filter_non_battlefy_source(source.name)]

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
