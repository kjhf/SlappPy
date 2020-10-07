from urllib.parse import quote

import requests


def download_from_sendou():
    url = 'https://sendou.ink/graphql'
    query: str = f"""
query {{
    users
    {{
        username,
        discord_id,
        id,
        twitch_name,
        twitter_name,
        country,
        weapons,
        top500
    }}
}}";
"""

    built_url: str = f"{url}?query={quote(query, safe='')}"
    requests.get(built_url)
