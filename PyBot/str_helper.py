def truncate(string: str, max_length: int, indicator: str = "") -> str:
    """
    Truncates the given string up to a maximum length.
    Optionally specify a truncation indicator.
    :param string: The string to truncate
    :param max_length: The maximum length of the string
    :param indicator: Indicator appended if truncated
    :return: The result string.
    """
    if string is None:
        raise ValueError('string is None.')

    if len(indicator) > max_length:
        raise ValueError('Truncation indicator length cannot be greater than the maximum length of the string.')

    if len(string) <= max_length:
        return string

    return string[0:max_length - len(indicator)] + indicator
