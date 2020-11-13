import json
from typing import Union, List, AnyStr

import requests


def fetch_address(address) -> dict:
    """Fetch JSON from an address, assert a 200 success."""
    print(f'Getting from {address}')

    response = requests.get(address)
    assert response.status_code == 200

    # Validate json content
    return json.loads(response.content)


def save_to_file(path: str, content: Union[str, List[AnyStr]]):
    """Save content to specified path"""
    with open(path, 'x') as the_file:
        if isinstance(content, str):
            the_file.write(content)
        else:
            the_file.writelines(content)


def load_json_from_file(path: str) -> dict:
    """Load JSON from specified path"""
    with open(path, 'r', encoding='utf-8') as infile:
        return json.load(infile)
