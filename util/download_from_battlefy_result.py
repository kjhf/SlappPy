import glob
import json
from datetime import datetime
from dateutil.parser import isoparse
from os import makedirs
from os.path import exists, join, isfile
from tokens import CLOUD_BACKEND
from util import utils
from util.utils import fetch_address, save_to_file

RESULT_INFO_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/stages/%s/latest-round-standings'
TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/tournaments/%s'
TOURNAMENTS_SAVE_DIR = "./tournaments"


def get_or_fetch_tournament_file(id_to_fetch: str) -> str:
    if not exists(TOURNAMENTS_SAVE_DIR):
        makedirs(TOURNAMENTS_SAVE_DIR)

    filename: str = f'{id_to_fetch}.json'
    results = glob.glob(join(TOURNAMENTS_SAVE_DIR, f'*-{filename}'))
    full_path = results[0] if len(results) else join(TOURNAMENTS_SAVE_DIR, f'*{filename}')
    if not isfile(full_path):
        tourney_contents = fetch_address(TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT % id_to_fetch)

        if len(tourney_contents) == 0:
            print(f'Nothing exists at {id_to_fetch}.')
        else:
            if '_id' in tourney_contents and 'slug' in tourney_contents and 'startTime' in tourney_contents:
                start_time: datetime = isoparse(tourney_contents['startTime'])
                filename = f'{start_time.strftime("%Y-%m-%d")}-{tourney_contents["slug"]}-' \
                           f'{id_to_fetch}.json'
                full_path = join(TOURNAMENTS_SAVE_DIR, filename)
            print(f'OK! (Saved read tourney to {full_path})')

        save_to_file(full_path, json.dumps(tourney_contents))
    return full_path


if __name__ == '__main__':
    ids = \
        [
            input('Tournament id?')
        ]

    for id_to_fetch in ids:
        tournament_file = get_or_fetch_tournament_file(id_to_fetch)
        stage_ids = utils.load_json_from_file(tournament_file)['stageIDs']

        for stage_id in stage_ids:
            stage_contents = fetch_address(RESULT_INFO_FETCH_ADDRESS_FORMAT % stage_id)

            if len(stage_contents) == 0:
                print(f'Nothing exists at {stage_id}')
                continue

            # Save the data
            stage_path = join(TOURNAMENTS_SAVE_DIR, 'stages', id_to_fetch.__str__())
            if not exists(stage_path):
                makedirs(stage_path)
            stage_file_path = join(stage_path, f'{stage_id}.json')
            save_to_file(stage_file_path, json.dumps(stage_contents))
            print(f'OK! (Saved read stage {stage_file_path})')
