import json
from datetime import datetime
from os import makedirs
from os.path import exists

import challonge
from dateutil.parser import isoparse

from tokens import CHALLONGE_API_KEY, CHALLONGE_USERNAME
from util.utils import save_to_file

if __name__ == '__main__':
    challonge.set_credentials(CHALLONGE_USERNAME, CHALLONGE_API_KEY)

    ids = [input('id/url? NOTE FOR SUBDOMAINS YOU MUST PREPEND THE SUBDOMAIN TO THE ID e.g. paddling-abc123')]

    for id_to_fetch in ids:

        # Retrieve a tournament by its id (or its url).
        tourney_contents = challonge.tournaments.show(id_to_fetch)
        print(tourney_contents)
        if isinstance(tourney_contents, str):
            tourney_contents = json.loads(tourney_contents)

        if len(tourney_contents) == 0:
            print(f'Nothing exists at {id_to_fetch}.')
            continue

        # Retrieve the participants for a given tournament.
        team_contents = challonge.participants.index(tourney_contents["id"])

        if isinstance(team_contents, str):
            team_contents = json.loads(team_contents)

        print(team_contents)

        # Handle tournament summary...
        name = f'{id_to_fetch}.json'
        if 'id' in tourney_contents and 'name' in tourney_contents and 'created_at' in tourney_contents:
            if not exists('./tournaments'):
                makedirs('./tournaments')
            start_time: datetime = tourney_contents['created_at']
            if isinstance(start_time, str):
                if start_time.startswith('datetime.'):
                    start_time = eval(start_time)
                else:
                    start_time = isoparse(start_time)

            name = f'{start_time.strftime("%Y-%m-%d")}-{tourney_contents["name"]}-' \
                   f'{id_to_fetch}.json'
            save_to_file(f'./tournaments/{name}', json.dumps(tourney_contents, default=str))
            print(f'OK! (Saved read tourney {name})')
        else:
            save_to_file(f'{id_to_fetch}.json', json.dumps(tourney_contents, default=str))
            print(f'OK! (Saved generic {id_to_fetch})')

        # Handle teams...
        if not exists('./teams'):
            makedirs('./teams')
        save_to_file(f'./teams/{name}', json.dumps(team_contents, default=str))
        print(f'OK! (Saved read teams {name})')
