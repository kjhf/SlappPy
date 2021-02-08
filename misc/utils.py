import json
from typing import Union, List, AnyStr, Iterable

import requests


def fetch_address(address) -> dict:
    """Fetch JSON from an address, assert a 200 success."""
    print(f'Getting from {address}')

    response = requests.get(address)
    assert response.status_code == 200, f"Bad response from {address} ({response.status_code})"

    # Validate json content
    return json.loads(response.content)


# Using List for the content type as json doesn't like dumping other collections.
def save_as_json_to_file(path: str,
                         content: Union[dict, str, List[AnyStr], List[dict]],
                         overwrite: bool = True,
                         indent: int = 2):
    """Save content by dumping as json and saving to specified path"""
    with open(file=path, mode='w' if overwrite else 'a', encoding='utf8') as json_file:
        json.dump(content, json_file, ensure_ascii=False, default=str, indent=indent)


def save_text_to_file(path: str, content: Union[AnyStr, Iterable[AnyStr]], overwrite: bool = True):
    """Save content as text to specified path"""
    with open(file=path,
              mode='w' if overwrite else 'a',
              encoding='utf-8') as the_file:
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
