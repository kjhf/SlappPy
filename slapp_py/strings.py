import re
from typing import List, Dict, Union

from PyBot.helpers.str_helper import truncate


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
    div = team["Div"] if "Div" in team else ''
    if div_is_unknown(div):
        div = ''
    else:
        div = f' ({div_to_string(team["Div"])})'
    return f'{clan_tag} {name}{div}'


def div_is_unknown(div: dict) -> bool:
    return div is None or \
           "Value" not in div or \
           "DivType" not in div or \
           div["Value"] is None or \
           div["Value"] == 2147483647 or \
           div["DivType"] is None or \
           div["DivType"] == 0


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
    elif div_type_str == '3':
        div_type_str = 'DSB'

    return f'{div_type_str} Div {value_str}'


def best_team_player_div_string(team: dict, players_for_team: List[dict], known_teams: Dict[str, dict]):
    if not team or not players_for_team or not known_teams:
        return ''

    highest_div: dict = team["Div"] if not div_is_unknown(team["Div"]) else {"Value": None, "DivType": None}
    best_player = None
    for player_tuple in players_for_team:
        if player_tuple:
            p = player_tuple["Item1"] if "Item1" in player_tuple else {}
            in_team = player_tuple["Item2"] if "Item2" in player_tuple else False
            if in_team and "Teams" in p and len(p["Teams"]) > 0:
                for team_id in p["Teams"]:
                    player_team = known_teams[team_id.__str__()] if known_teams and team_id in known_teams else None
                    if (player_team is not None) \
                            and (not div_is_unknown(player_team["Div"])) \
                            and ((div_is_unknown(highest_div)) or (player_team["Div"]["Value"] < highest_div["Value"])):
                        highest_div = player_team["Div"]
                        best_player = p

    if div_is_unknown(highest_div) or div_is_unknown(team["Div"]) or best_player is None or best_player is {}:
        return ''
    elif highest_div["Value"] == team["Div"]["Value"]:
        return 'No higher div players.'
    else:
        if 'Name' in best_player:
            name: str = best_player['Name']
        elif 'Names' in best_player and len(best_player['Names']) > 0:
            name: str = best_player['Names'][0]
        else:
            name: str = '(unknown)'
        return f"Highest div'd player is {escape_characters(name)} at {div_to_string(highest_div)}."


def escape_characters(string: Union[str, dict], characters: str = '_*\\', escape_character: str = '\\') -> str:
    """
    Escape characters in a string with the specified escape character(s).
    :param string: The string to escape
    :param characters: The characters that must be escaped
    :param escape_character: The character to use an an escape
    :return: The escaped string
    """
    if isinstance(string, dict):
        for element in string:
            for char in characters:
                element = element.replace(char, escape_character + char)
    else:
        for char in characters:
            string = string.__str__().replace(char, escape_character + char)
    return string


def truncate_source(source: str, max_length: int = 128) -> str:
    # Strip the source id
    source = re.sub("-+[0-9a-fA-F]+$", '', source)
    source = escape_characters(source)

    # Truncate
    source = truncate(source, max_length, '…')
    return source


def attempt_link_source(source: str) -> str:
    """Take a source and attempt to convert it into a link"""

    # Mapping takes a list of tournament names and gives an organisation name
    mapping: Dict[str, List[str]] = {
        'inkling-performance-labs': ['-low-ink-', '-testing-grounds-' '-swim-or-sink-'],
        'inktv': ['-bns-', '-swl-winter-snowflake-', '-splatoon-world-league-',
                  '-inktv-open-', '-extrafaganza-', '-inkvitational-'],
        'sitback-saturdays': ['-sitback-saturdays-'],
        'splatoon2': ['-splatoon-2-north-american-online-open-'],
        'squidboards-splatoon-2-community-events': ['-sqss-', '-squidboards-splat-series-'],
        'squid-spawning-grounds': ['-squid-spawning-grounds-'],
        'fresh-start-cup': ['-fresh-start-cup-'],
        'swift-second-saturdays': ['-sss-'],
        'gamesetmatch': ['-gsm-'],
        'area-cup': ['-area-cup-'],
        'asquidmin': ['-turtlement-'],
    }

    for organiser in mapping:
        for tourneys in mapping[organiser]:
            for name in tourneys:
                if name in source:
                    m = re.search("-+([0-9a-fA-F]+)$", source, re.I)
                    text = truncate_source(source)
                    if m:
                        guid = m.groups()[0]
                        return f'[{text}](https://battlefy.com/{organiser}//{guid}/info)'
                    else:
                        return text
    return truncate_source(source)


def equals_ignore_case(str1: str, str2: str) -> bool:
    if str1 is None or str2 is None:
        return False

    def normalize_caseless(text):
        import unicodedata
        return unicodedata.normalize("NFKD", text.casefold())

    return normalize_caseless(str1) == normalize_caseless(str2)
