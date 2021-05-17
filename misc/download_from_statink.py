from datetime import datetime

from caching.fileio import save_as_json_to_file  # battlefy-toolkit
from dateutil.parser import isoparse
from os import makedirs
from os.path import exists

from helpers.fetch_helper import fetch_address

STAT_INK_ADDRESS_FORMAT: str = 'https://stat.ink/api/v2/battle/%s?format=pretty'

if __name__ == '__main__':
    # ids = [input("Id?")]
    ids = range(3200000, 3199890, -1)

    for id_to_fetch in ids:
        contents = fetch_address(STAT_INK_ADDRESS_FORMAT % id_to_fetch)

        if len(contents) == 0:
            print(f'Nothing exists at {id_to_fetch}.')
            continue

        # Handle tournament summary...
        name = f'{id_to_fetch}.json'
        if 'id' in contents and 'end_at' in contents:
            if not exists('./statink'):
                makedirs('./statink')
            start_time: datetime = isoparse(contents['end_at']['iso8601'])
            name = f'{start_time.strftime("%Y-%m-%d")}-stat.ink-' \
                   f'{id_to_fetch}.json'
            save_as_json_to_file(f'./statink/{name}', contents)
            print(f'OK! (Saved contents {name})')
        else:
            save_as_json_to_file(f'{id_to_fetch}.json', contents)
            print(f'OK! (Saved generic {id_to_fetch})')
