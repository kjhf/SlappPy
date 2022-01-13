import json
import logging
from json import JSONDecodeError

import requests


def fetch_address(address: str, assert_success: bool = True) -> dict:
    """Fetch JSON from an address. Optionally assert 200 success."""
    logging.debug(f"Fetching from {address}")

    try:
        response = requests.get(address)
    except requests.exceptions.RequestException as ex:
        logging.exception("Fetch address raised an exception", exc_info=ex)
        if assert_success:
            assert False, f"Fetch address raised an exception: {ex}"
        return {}

    if assert_success:
        assert response.status_code == 200, f"Bad response from {address} ({response.status_code})"

    # Validate json content
    try:
        return json.loads(response.content or "{}")
    except JSONDecodeError as ex:
        logging.exception(f"Battlefy sent us bad JSON: {response.content}", exc_info=ex)
        return {}
