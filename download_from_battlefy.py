import json
import requests

from SlapPy.tokens import CLOUD_BACKEND

BATTLEFY_LOW_INK_ADDRESS_FORMAT: str = 'https://battlefy.com/low-ink//%s/participants'
FETCH_ADDRESS_FORMAT: str = CLOUD_BACKEND + '/tournaments/%s/teams'

if __name__ == '__main__':
    id_to_fetch = input('id?')
    address = FETCH_ADDRESS_FORMAT % id_to_fetch
    print(f'Getting from {address}')

    response = requests.get(address)
    assert response.status_code == 200

    # Validate json content
    dl = json.loads(response.content)

    # Save to file
    f = open(f'{id_to_fetch}.json', "x")
    f.write(json.dumps(dl))
    f.close()
    print('OK!')
