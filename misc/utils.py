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


def save_to_file(path: str, content: Union[str, List[AnyStr]], overwrite: bool = True):
    """Save content to specified path"""
    with open(path, 'w' if overwrite else 'x') as the_file:
        if isinstance(content, str):
            the_file.write(content)
        else:
            the_file.writelines(content)


def load_json_from_file(path: str) -> Union[dict, List[dict]]:
    """Load JSON from specified path"""
    with open(path, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def assert_is_dict_recursive(val: Union[dict, list, str, int], comment: str = ''):
    if isinstance(val, str) or isinstance(val, int):
        # This is good.
        pass
    elif isinstance(val, dict):
        for element in val:
            assert_is_dict_recursive(val[element], f'{comment}/{element}')
    elif isinstance(val, list):
        for element in val:
            assert_is_dict_recursive(element, f'{comment}/values')
    else:
        assert False, f"This val is not a str/int, dict, or list: {comment} is {val=}"
