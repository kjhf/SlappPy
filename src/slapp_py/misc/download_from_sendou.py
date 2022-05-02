from datetime import datetime
from os.path import join, exists
from typing import List, Optional

import requests

from battlefy_toolkit.caching.fileio import save_as_json_to_file
from slapp_py.misc.slapp_files_utils import TOURNEY_TEAMS_SAVE_DIR


def download_users_from_sendou() -> List[dict]:
    url = 'https://sendou.ink/api/users'
    return requests.get(url).json()


def download_plus_server_from_sendou() -> List[dict]:
    url = 'https://sendou.ink/api/plus'
    return requests.get(url).json()


def download_from_sendou() -> List[dict]:
    """Downloads and merges membership tiers. Returns the users as dictionaries."""
    # Download all users list
    users = download_users_from_sendou()

    # Merge in plus server membership details
    plus_server_info = download_plus_server_from_sendou()
    for user in users:
        user_plus_entry = next((entry for entry in plus_server_info if entry["user"]["discordId"].__str__() == user["discordId"].__str__()), None)
        if user_plus_entry:
            user["membershipTier"] = user_plus_entry["membershipTier"]

    # Return all users
    return users


def download_from_sendou_and_save(destination_path: Optional[str] = None) -> str:
    """Downloads from Sendou and saves the JSON file. Returns the file path."""
    users = download_from_sendou()
    destination = destination_path or get_sendou_path()
    save_as_json_to_file(destination, users, indent=0)
    return destination


def conditionally_download_from_sendou_and_save() -> str:
    """Downloads from Sendou and saves the JSON file, if one has not been downloaded today. Returns the file path."""
    destination = get_sendou_path()
    if not exists(destination):
        download_from_sendou_and_save(destination)
    return destination


def get_sendou_path() -> str:
    return join(TOURNEY_TEAMS_SAVE_DIR, f"{datetime.strftime(datetime.now(), '%Y-%m-%d')}-Sendou.json")


if __name__ == '__main__':
    conditionally_download_from_sendou_and_save()
