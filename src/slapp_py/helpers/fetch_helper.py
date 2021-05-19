import json

import requests


def fetch_address(address) -> dict:
    """Fetch JSON from an address, assert a 200 success."""
    print(f'Getting from {address}')

    response = requests.get(address)
    assert response.status_code == 200, f"Bad response from {address} ({response.status_code})"

    # Validate json content
    return json.loads(response.content)
