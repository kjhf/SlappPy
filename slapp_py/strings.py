import re
from typing import List, Dict

from PyBot.str_helper import truncate


def teams_to_string(teams: List[dict]):
    """
    Take the team dictionary entry and return a string.
    """
    for team in teams:
        yield team_to_string(team)


def team_to_string(team: dict) -> str:
    """
    Take the team dictionary entry and return a string.
    """
    if not team:
        return '(No team)'
    clan_tag = escape_characters(team["ClanTags"][0]) if team["ClanTags"] else ""
    name = escape_characters(team["Name"]) if team["Name"] else "(Unnamed Team)"
    div = div_to_string(team["Div"])
    return f'{clan_tag} {name} ({div})'


def div_is_unknown(div: dict) -> bool:
    return div is None or \
           "Value" not in div or \
           "DivType" not in div or \
           div["Value"] is None or \
           div["Value"] == 2147483647 or \
           div["DivType"] is None or \
           div["DivType"] is 0


def div_to_string(div: dict) -> str:
    """
    Take the div dictionary entry and return a string.
    """
    if div_is_unknown(div):
        return 'Div Unknown'

    value = div["Value"] if "Value" in div else None
    if value == -1:
        value_str = 'X+'
    elif value == 0:
        value_str = 'X'
    else:
        value_str = value.__str__()

    div_type_str = div["DivType"].__str__() if "DivType" in div else None
    if div_type_str == '0':
        div_type_str = 'Unknown'
    elif div_type_str == '1':
        div_type_str = 'LUTI'
    elif div_type_str == '2':
        div_type_str = 'EBTV'

    return f'{div_type_str} Div {value_str}'


def best_team_player_div_string(team: dict, players_for_team: List[dict], known_teams: Dict[str, dict]):
    if not team or not players_for_team or not known_teams:
        return ''

    highest_div: dict = team["Div"] if "Div" in team else {"Value": None, "DivType": None}
    best_player = None
    for player_tuple in players_for_team:
        if player_tuple:
            p = player_tuple["Item1"] if "Item1" in player_tuple else {}
            in_team = player_tuple["Item2"] if "Item2" in player_tuple else False
            if in_team and "Teams" in p and p["Teams"]:
                for team_id in p["Teams"]:
                    player_team = known_teams[team_id.__str__()] if known_teams and team_id in known_teams else None
                    if player_team is not None \
                            and not div_is_unknown(player_team["Div"]) \
                            and (div_is_unknown(highest_div) or player_team["Div"]["Value"] < highest_div["Value"]):
                        highest_div = player_team["Div"]
                        best_player = p

    if div_is_unknown(highest_div):
        return ''
    elif highest_div["Value"] == team["Div"]["Value"]:
        return 'No higher div players.'
    else:
        return f"Highest div'd player is {escape_characters(best_player['Name'])} at {div_to_string(highest_div)}."


def escape_characters(string: str, characters: str = '_*', escape_character: str = '\\') -> str:
    """
    Escape characters in a string with the specified escape character(s).
    :param string: The string to escape
    :param characters: The characters that must be escaped
    :param escape_character: The character to use an an escape
    :return: The escaped string
    """
    for char in characters:
        string.replace(char, escape_character + char)
    return string


def truncate_source(source: str) -> str:
    # Strip the source id
    source = re.sub("-+[0-9a-fA-F]+$", '', source)

    # Truncate to max 100 chars
    source = truncate(source, 100, '…')
    return source
