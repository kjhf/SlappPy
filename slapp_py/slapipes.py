import json
import os
import subprocess
from datetime import datetime
from typing import List, Dict
from urllib.parse import quote

from discord import Color, Embed

from PyBot.helpers import embed_helper, str_helper
from slapp_py.strings import escape_characters, teams_to_string, attempt_link_source, team_to_string, \
    best_team_player_div_string, div_to_string

slapp_path = None


def initialise_slapp():
    global slapp_path

    result = subprocess.run(['cd'], stdout=subprocess.PIPE, encoding='utf-8', shell=True)
    slapp_path = result.stdout.strip(" \r\n")
    print('cd: ' + slapp_path)
    if not slapp_path.endswith('SlapPy') and 'PyBot' in slapp_path:
        slapp_path = slapp_path[0:slapp_path.index('PyBot')]
    slapp_path = os.path.join(slapp_path, 'venv', 'Slapp', 'SplatTagConsole.dll')
    assert os.path.isfile(slapp_path), f'Not a file: {slapp_path}'


async def query_slapp(query) -> (bool, dict):
    """Query Slapp. Returns success and the JSON response."""
    # global slapp_process
    # if slapp_process is None:
    slapp_process = subprocess.Popen(
        # f'dotnet \"{slapp_path}\" {query} --keepOpen',
        f'dotnet \"{slapp_path}\" \"{query}\"',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding='utf-8',
        errors='replace'
    )
    # else:
    #     slapp_process.stdin.writelines([query])
    #     await sleep(0.005)

    while True:
        response: str = slapp_process.stdout.readline()
        if response.startswith('{'):
            break
    response: dict = json.loads(response)
    print(response)
    return response["Message"] == "OK", response


def process_slapp(response: dict, now: datetime) -> Embed:
    matched_players: List[dict] = (response["Players"])
    matched_players_len = len(matched_players)
    matched_teams: List[dict] = (response["Teams"])
    matched_teams_len = len(matched_teams)
    additional_teams: Dict[str, dict] = response["AdditionalTeams"]
    matched_players_for_teams: Dict[str, List[dict]] = response["PlayersForTeams"]

    has_matched_players = matched_players_len != 0
    has_matched_teams = matched_teams_len != 0
    show_limited = matched_players_len > 9 or matched_teams_len > 9

    if has_matched_players and has_matched_teams:
        title = f"Found {matched_players_len} player{('' if (matched_players_len == 1) else 's')} " \
                f"and {matched_teams_len} team{('' if (matched_teams_len == 1) else 's')}!"
        colour = Color.green()
    elif has_matched_players and not has_matched_teams:
        title = f"Found {matched_players_len} player{('' if (matched_players_len == 1) else 's')}!"
        colour = Color.blue()
    elif not has_matched_players and has_matched_teams:
        title = f"Found {matched_teams_len} team{('' if (matched_teams_len == 1) else 's')}!"
        colour = Color.gold()
    else:
        title = f"Didn't find anything 😔"
        colour = Color.red()

    builder = embed_helper.to_embed('', colour=colour, title=title)

    if has_matched_players:
        for i in range(0, 9):
            if i >= matched_players_len:
                break

            p = matched_players[i]
            names = p["Names"] if "Names" in p else ['']

            # Transform names by adding a backslash to any backslashes.
            if names:
                names = list(map(lambda n: escape_characters(n, '\\'), names))

            teams = list(map(lambda team_id: additional_teams[team_id.__str__()], p["Teams"]))
            current_team = teams[0] if teams else None

            if len(teams) > 1:
                old_teams = f'\nOld teams: {", ".join((teams_to_string(teams[1:])))}'
            else:
                old_teams = ''

            if len(names) > 1:
                other_names = str_helper.truncate("_ᴬᴷᴬ_ " + ', '.join(names[1:]) + "\n", 1000, "…")
            else:
                other_names = ''

            twitter = f'{p["Twitter"]}\n' if "Twitter" in p else ""
            if "BattlefySlugs" in p:
                battlefy = ''.join(list(map(
                    lambda slug: '[' + escape_characters(slug, "\\") +
                                 f'](https://battlefy.com/users/{quote(slug)})\n',
                    p['BattlefySlugs'])))
            else:
                battlefy = ''
            sources = p["Sources"] if "Sources" in p else ['']
            sources.reverse()  # Reverse so last added source is first ...
            sources = "\n ".join(list(map(lambda source: attempt_link_source(source), sources)))
            top500 = "👑 " if "Top500" in p and p["Top500"] else ""

            # If there's just the one matched player, move the sources to the next field.
            if matched_players_len == 1:
                info = f'{other_names}Plays for {team_to_string(current_team)}{old_teams}\n{twitter}{battlefy}'
                builder.add_field(name=str_helper.truncate(top500 + names[0], 256, ""),
                                  value=str_helper.truncate(info, 1023, "…_"),
                                  inline=False)

                builder.add_field(name='\tSources:',
                                  value=str_helper.truncate('_' + sources + '_', 1023, "…_"),
                                  inline=False)
            else:
                info = f'{other_names}Plays for {team_to_string(current_team)}{old_teams}\n{twitter}{battlefy}' \
                       f'_{sources}_'
                builder.add_field(name=str_helper.truncate(top500 + names[0], 256, ""),
                                  value=str_helper.truncate(info, 1023, "…_"),
                                  inline=False)

    if has_matched_teams:
        separator = ',\n' if matched_teams_len == 1 else ', '

        for i in range(0, 9):
            if i >= matched_teams_len:
                break

            t = matched_teams[i]
            players = matched_players_for_teams[t["Id"].__str__()]
            player_strings = ''
            for player_tuple in players:
                if player_tuple:
                    p = player_tuple["Item1"] if "Item1" in player_tuple else {}
                    in_team = player_tuple["Item2"] if "Item2" in player_tuple else None
                    name = escape_characters(p["Names"][0]) \
                        if "Names" in p and len(p["Names"]) > 0 \
                        else '(Unknown player)'
                    player_strings += \
                        f'{name} {("(Most recent)" if in_team else "(Ex)" if in_team is False else "")}'
                    player_strings += separator

            player_strings = player_strings[0:-len(separator)]
            div_phrase = best_team_player_div_string(t, players, additional_teams)
            sources = t["Sources"] if "Sources" in t else ['']
            sources.reverse()  # Reverse so last added source is first ...
            sources = "\n".join(list(map(lambda source: attempt_link_source(source), sources)))

            # If there's just the one matched team, move the sources to the next field.
            if matched_teams_len == 1:
                info = f'{div_to_string(t["Div"])}. {div_phrase}\nPlayers: {player_strings}'
                builder.add_field(name=str_helper.truncate(team_to_string(t), 256, ""),
                                  value=str_helper.truncate(info, 1023, "…_"),
                                  inline=False)

                builder.add_field(name='\tSources:',
                                  value=str_helper.truncate('_' + sources + '_', 1023, "…_"),
                                  inline=False)
            else:
                info = f'{div_to_string(t["Div"])}. {div_phrase}\nPlayers: {player_strings}\n' \
                       f'_{sources}_'
                builder.add_field(name=str_helper.truncate(team_to_string(t), 256, ""),
                                  value=str_helper.truncate(info, 1023, "…_"),
                                  inline=False)

    builder.set_footer(
        text=f"Fetched in {int((datetime.utcnow() - now).microseconds / 1000)} milliseconds. " +
             ('Only the first 9 results are shown for players and teams.' if show_limited else ''),
        icon_url="https://media.discordapp.net/attachments/471361750986522647/758104388824072253/icon.png")
    return builder
