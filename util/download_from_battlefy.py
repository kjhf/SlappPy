import json
from datetime import datetime
from dateutil.parser import isoparse
from os import makedirs
from os.path import exists
from tokens import CLOUD_BACKEND
from util.utils import fetch_address, save_to_file

BATTLEFY_LOW_INK_ADDRESS_FORMAT: str = 'https://battlefy.com/low-ink//%s/participants'
TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/tournaments/%s'
TEAMS_FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/tournaments/%s/teams'


if __name__ == '__main__':
    ids = [input('id?')]

    for id_to_fetch in ids:
        tourney_contents = fetch_address(TOURNAMENT_INFO_FETCH_ADDRESS_FORMAT % id_to_fetch)
        team_contents = fetch_address(TEAMS_FETCH_ADDRESS_FORMAT % id_to_fetch)

        if len(tourney_contents) == 0:
            print(f'Nothing exists at {id_to_fetch}.')
            continue

        # Handle tournament summary...
        name = f'{id_to_fetch}.json'
        if '_id' in tourney_contents and 'slug' in tourney_contents and 'startTime' in tourney_contents:
            if not exists('./tournaments'):
                makedirs('./tournaments')
            start_time: datetime = isoparse(tourney_contents['startTime'])
            name = f'{start_time.year}-{start_time.month}-{start_time.day}-{tourney_contents["slug"]}-' \
                   f'{id_to_fetch}.json'
            save_to_file(f'./tournaments/{name}', json.dumps(tourney_contents))
            print(f'OK! (Saved read tourney {name})')
        else:
            save_to_file(f'{id_to_fetch}.json', json.dumps(tourney_contents))
            print(f'OK! (Saved generic {id_to_fetch})')

        # Handle teams...
        if not exists('./teams'):
            makedirs('./teams')
        save_to_file(f'./teams/{name}', json.dumps(team_contents))
        print(f'OK! (Saved read teams {name})')
