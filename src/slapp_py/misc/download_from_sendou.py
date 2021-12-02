from datetime import datetime
from os.path import join
from typing import List

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


if __name__ == '__main__':
    __users = download_from_sendou()
    __destination = join(TOURNEY_TEAMS_SAVE_DIR, f"{datetime.strftime(datetime.now(), '%Y-%m-%d')}-Sendou.json")
    save_as_json_to_file(__destination, __users, indent=0)
