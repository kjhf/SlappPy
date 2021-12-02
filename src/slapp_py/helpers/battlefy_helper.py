import re


def is_valid_battlefy_id(_battlefy_id: str) -> bool:
    """
    Filter out ids that are less than 20 characters or more than 30 (id is probably not correct) and not hex.
    Expected 24 chars, and hex numbers only.
    :param _battlefy_id: The id to test
    :return: True if valid else False.
    """
    return 20 <= len(_battlefy_id) < 30 and re.match("^[A-Fa-f0-9]*$", _battlefy_id)


def filter_non_battlefy_source(source_name: str):
    return not any(x in source_name for x in ["-stat.ink-", "-LUTI-", "Twitter-"])
