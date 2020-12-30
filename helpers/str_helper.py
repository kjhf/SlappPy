from typing import Optional


def truncate(string: str, max_length: int, indicator: str = "") -> str:
    """
    Truncates the given string up to a maximum length.
    Optionally specify a truncation indicator.
    :param string: The string to truncate
    :param max_length: The maximum length of the string
    :param indicator: Indicator appended if truncated, e.g. …
    :return: The result string.
    """
    if string is None:
        raise ValueError('string is None.')

    if not isinstance(string, str):
        raise ValueError('string specified to truncate is not a string.')

    if len(indicator) > max_length:
        raise ValueError('Truncation indicator length cannot be greater than the maximum length of the string.')

    if len(string) <= max_length:
        return string

    return string[0:max_length - len(indicator)] + indicator


def equals_ignore_case(str1: str, str2: str) -> bool:
    if str1 is None or str2 is None:
        return False

    def normalize_caseless(text):
        import unicodedata
        return unicodedata.normalize("NFKD", text.casefold())

    return normalize_caseless(str1) == normalize_caseless(str2)


def is_none_or_whitespace(value: Optional[str]) -> bool:
    """
    Indicates whether a specified string is null, empty, or consists only of white-space characters.

    :param value: The string to test
    :returns: True if the value parameter is None or Empty, or if value consists exclusively of white-space characters.
    """
    if value is None:
        return True

    for i in range(0, len(value)):
        if value[i].isspace():
            return False
    return True


def join(separator: str, collection: list) -> str:
    """
    Join a list of objects together as a string
    :param separator: The separator between the elements
    :param collection: The list of objects
    :return: Joined string
    """
    return separator.join(map(str, collection))
