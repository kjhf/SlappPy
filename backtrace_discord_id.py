import json
import time

import requests

from SlapPy.tokens import BOT_TOKEN

_reset_time = None


def clear_reset_time():
    global _reset_time
    _reset_time = None


def backtrace_discord_id(discord_id: int) -> dict:
    global _reset_time
    url = 'https://discord.com/api/users/' + discord_id.__str__()
    headers = {'Authorization': 'Bot ' + BOT_TOKEN}

    if _reset_time is not None:
        now_seconds = int(time.time())
        if _reset_time >= now_seconds:
            diff = (_reset_time - now_seconds) + 2
            print(f'Sleeping for {diff}s before continuing.')
            time.sleep(diff)
            _reset_time = None

    response = requests.get(url, headers=headers)
    print(f'{response.status_code}: {response.content}')

    # The number of remaining requests that can be made
    remaining_requests = int(response.headers["X-RateLimit-Remaining"])

    # Epoch time (seconds since 00:00:00 UTC on January 1, 1970) at which the rate limit resets
    reset_time = int(response.headers["X-RateLimit-Reset"])

    if remaining_requests < 3:
        now_seconds = time.time()
        remaining = (reset_time - now_seconds)
        print(f'{remaining_requests} request(s) remaining ({remaining} seconds till reset).')

        # Setting this will cause us to wait before sending another request.
        if remaining_requests == 0:
            _reset_time = reset_time

    return json.loads(response.content)


if __name__ == '__main__':
    result = backtrace_discord_id(97288493029416960)
    print(result["id"])
    print(result["username"] + '#' + result["discriminator"])
    print(result["avatar"])
    print(result["public_flags"])

