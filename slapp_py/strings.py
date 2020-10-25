from typing import List, Dict


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
    if team is None:
        return '(No team)'
    return f'{team["ClanTags"][0] if team["ClanTags"] else ""} {team["Name"]} ({div_to_string(team["Div"])})'


def div_is_unknown(div: dict) -> bool:
    return div["Value"] is None or div["Value"] == 2147483647


def div_to_string(div: dict) -> str:
    """
    Take the div dictionary entry and return a string.
    """
    value = div["Value"] if "Value" in div else None
    if div_is_unknown(div):
        return 'Div Unknown'

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
    highest_div: dict = team["Div"]
    best_player = None
    for player_tuple in players_for_team:
        p = player_tuple["Item1"]
        in_team = player_tuple["Item2"]
        if in_team and p["Teams"]:
            for team_id in p:
                player_team = known_teams[team_id.__str__()] if team_id in known_teams else None
                if player_team is not None and player_team["Div"]["Value"] < highest_div["Value"]:
                    highest_div = player_team["Div"]
                    best_player = p

    if div_is_unknown(highest_div):
        return ''
    elif highest_div["Value"] == team["Div"]["Value"]:
        return 'No higher div players.'
    else:
        return f"Highest div'd player is {best_player['Name']} at {div_to_string(highest_div)}."
