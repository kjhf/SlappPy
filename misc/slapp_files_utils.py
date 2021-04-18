import glob
from os.path import join
from typing import List, Optional, Generator

from core_classes.player import Player
from core_classes.source import Source
from core_classes.team import Team
from misc import utils
from tokens import SLAPP_APP_DATA

TOURNEY_INFO_SAVE_DIR = join(SLAPP_APP_DATA, "tourney_info")
TOURNEY_TEAMS_SAVE_DIR = join(SLAPP_APP_DATA, "tourney_teams")
STAGES_SAVE_DIR = join(TOURNEY_INFO_SAVE_DIR, "stages")


def get_all_snapshot_players_files() -> List[str]:
    return glob.glob(join(SLAPP_APP_DATA, f'Snapshot-Players-*.json'))


def get_all_snapshot_teams_files() -> List[str]:
    return glob.glob(join(SLAPP_APP_DATA, f'Snapshot-Teams-*.json'))


def get_latest_snapshot_players_file() -> Optional[str]:
    files = get_all_snapshot_players_files()
    if files:
        return files[-1]
    else:
        return None


def get_latest_snapshot_teams_file() -> Optional[str]:
    files = get_all_snapshot_teams_files()
    if files:
        return files[-1]
    else:
        return None


def load_latest_snapshot_players_file() -> Optional[List[Player]]:
    file = get_latest_snapshot_players_file()
    if file:
        print('Loading players from ' + file)
        loaded = utils.load_json_from_file(file)
        return [Player.from_dict(d) for d in loaded]
    else:
        print('Players file not found.')
        return None


def load_latest_snapshot_teams_file() -> Optional[List[Team]]:
    file = get_latest_snapshot_teams_file()
    if file:
        print('Loading teams from ' + file)
        loaded = utils.load_json_from_file(file)
        return [Team.from_dict(d) for d in loaded]
    else:
        print('Teams file not found.')
        return None


def get_all_snapshot_sources_files() -> List[str]:
    return glob.glob(join(SLAPP_APP_DATA, f'Snapshot-Sources-*.json'))


def get_latest_snapshot_sources_file() -> Optional[str]:
    files = get_all_snapshot_sources_files()
    if files:
        return files[-1]
    else:
        return None


def load_latest_snapshot_sources_file() -> Optional[List[Source]]:
    file = get_latest_snapshot_sources_file()
    if file:
        print('Loading sources from ' + file)
        loaded = utils.load_json_from_file(file)
        return [Source.from_dict(d) for d in loaded]
    else:
        print('Sources file not found.')
        return None


def enumerate_latest_snapshot_sources_file() -> Generator[Source, None, None]:
    file = get_latest_snapshot_sources_file()
    if file:
        print('Loading sources from ' + file)
        loaded = utils.load_json_from_file(file)
        for d in loaded:
            yield Source.from_dict(d)
    else:
        print('Sources file not found.')
