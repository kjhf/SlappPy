import json
from typing import Union, List, AnyStr

import requests


def fetch_address(address):
    print(f'Getting from {address}')

    response = requests.get(address)
    assert response.status_code == 200

    # Validate json content
    return json.loads(response.content)


def save_to_file(path: str, content: Union[str, List[AnyStr]]):
    with open(path, 'x') as the_file:
        if isinstance(content, str):
            the_file.write(content)
        else:
            the_file.writelines(content)
