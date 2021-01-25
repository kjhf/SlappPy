"""
This slapipes module handles the communication between Slapp and Dola.
The pipes to the Slapp.
"""

import asyncio
import json
import os
import traceback
from asyncio import Queue
from datetime import datetime
from typing import List, Dict, Union, Callable, Any, Awaitable, Optional
from uuid import UUID

from discord import Color, Embed

from PyBot.helpers.embed_helper import to_embed
from core_classes.bracket import Bracket
from core_classes.player import Player
from core_classes.team import Team
from helpers.dict_helper import from_list
from helpers.str_helper import join, truncate
from slapp_py.strings import escape_characters, attempt_link_source

MAX_RESULTS = 20
slapp_write_queue: Queue[str] = Queue()


async def _default_response_handler(success: bool, response: dict) -> None:
    assert False, f"Slapp response handler not set. Discarding: {success=}, {response=}"


response_function: Callable[[bool, dict], Awaitable[None]] = _default_response_handler


async def _read_stdout(stdout):
    global response_function
    print('_read_stdout')
    while True:
        try:
            response: str = (await stdout.readline()).decode('utf-8')
            if not response:
                print('stdout: (none response)')
                await asyncio.sleep(1)
            else:
                print('stdout: ' + response)
                if response.startswith('{'):
                    response: dict = json.loads(response)
                    await response_function(response.get("Message") == "OK", response)
        except Exception as e:
            print(f'_read_stdout EXCEPTION: {e}\n{traceback.format_exc()}')


async def _read_stderr(stderr):
    print('_read_stderr')
    while True:
        try:
            response: str = (await stderr.readline()).decode('utf-8')
            if not response:
                print('stderr: (none response)')
                await asyncio.sleep(1)
            else:
                print('stderr: ' + response)
        except Exception as e:
            print(f'_read_stderr EXCEPTION: {e}\n{traceback.format_exc()}')


async def _write_stdin(stdin):
    print('_write_stdin')
    while True:
        try:
            while not slapp_write_queue.empty():
                query = await slapp_write_queue.get()
                print(f'_write_stdin: writing {query}')
                stdin.write(f'{query}\n'.encode('utf-8'))
                await stdin.drain()
                await asyncio.sleep(0.1)
            await asyncio.sleep(1)
        except Exception as e:
            print(f'_write_stdin EXCEPTION: {e}\n{traceback.format_exc()}')


async def _run_slapp(slapp_path: str):
    proc = await asyncio.create_subprocess_shell(
        f'dotnet \"{slapp_path}\" \"should_not-have-any_results1\" --keepOpen',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        encoding=None,  # encoding must be None
        errors=None,  # errors must be None
        shell=True,
        limit=100 * 1024 * 1024,  # 100 MiB
    )

    await asyncio.gather(
        _read_stderr(proc.stderr),
        _read_stdout(proc.stdout),
        _write_stdin(proc.stdin)
    )
    print("_run_slapp returned!")


async def initialise_slapp(new_response_function: Callable[[bool, dict], Any]):
    import subprocess
    global response_function

    print("Initialising Slapp ...")
    result = subprocess.run(['cd'], stdout=subprocess.PIPE, encoding='utf-8', shell=True)
    slapp_path = result.stdout.strip(" \r\n")
    print('cd: ' + slapp_path)
    if not slapp_path.endswith('SlapPy') and 'PyBot' in slapp_path:
        slapp_path = slapp_path[0:slapp_path.index('PyBot')]
    slapp_path = os.path.join(slapp_path, 'venv', 'Slapp', 'SplatTagConsole.dll')
    assert os.path.isfile(slapp_path), f'Not a file: {slapp_path}'

    print(f"Using Slapp found at {slapp_path}")
    response_function = new_response_function
    await _run_slapp(slapp_path)


async def query_slapp(query):
    """Query Slapp. The response comes back through the callback function that was passed in initialise_slapp."""

    print("Posting query to existing Slapp process...")
    await slapp_write_queue.put(query)


def process_slapp(response: dict, now: datetime) -> (Embed, Color):
    matched_players: List[Player] = from_list(lambda x: Player.from_dict(x), response.get("Players"))
    matched_players_len = len(matched_players)
    matched_teams: List[Team] = from_list(lambda x: Team.from_dict(x), response.get("Teams"))
    matched_teams_len = len(matched_teams)
    known_teams: Dict[str, Team] = {}
    placements_for_players: Dict[str, Dict[str, List[Bracket]]] = {}
    """Dictionary keyed by Player id, of value Dictionary keyed by Source id of value Placements list"""

    for team_id in response.get("AdditionalTeams"):
        known_teams[team_id.__str__()] = Team.from_dict(response.get("AdditionalTeams")[team_id])
    for team in matched_teams:
        known_teams[team.guid.__str__()] = team

    matched_players_for_teams: Dict[str, List[Dict[str, Union[Player, bool]]]] = {}
    for team_id in response.get("PlayersForTeams"):
        matched_players_for_teams[team_id] = []
        for tup in response.get("PlayersForTeams")[team_id]:
            player_tuple_for_team: Dict[str, Union[Player, bool]] = \
                {"Item1": Player.from_dict(tup["Item1"]) if "Item1" in tup else None,
                 "Item2": "Item2" in tup}
            matched_players_for_teams[team_id].append(player_tuple_for_team)

    sources: Dict[str, str] = {}
    low_ink_sources: Dict[str, str] = {}

    for source_id in response.get("Sources"):
        source_name = response.get("Sources")[source_id]
        sources[source_id] = source_name
        if 'low-ink-' in source_name:
            low_ink_sources[source_id] = source_name

    for player_id in response.get("PlacementsForPlayers"):
        placements_for_players[player_id.__str__()] = {}
        for source_id in response.get("PlacementsForPlayers")[player_id]:
            placements_for_players[player_id][source_id] = []
            for bracket in response.get("PlacementsForPlayers")[player_id][source_id]:
                placements_for_players[player_id][source_id].append(Bracket.from_dict(bracket))

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

    builder = to_embed('', colour=colour, title=title)
    embed_colour = colour

    if has_matched_players:
        for i in range(0, MAX_RESULTS):
            if i >= matched_players_len:
                break

            p = matched_players[i]

            # Transform names by adding a backslash to any backslashes.
            names = p.escape_names
            current_name = \
                (names[0] if len(names) else None) \
                or (names[1] if len(names) > 1 else None) \
                or "(Unnamed Player)"

            team_ids: List[UUID] = p.teams
            resolved_teams: List[Team] = []
            for team_id in team_ids:
                from core_classes.builtins import NoTeam
                if team_id == NoTeam.guid:
                    resolved_teams.append(NoTeam)
                else:
                    team = known_teams.get(team_id.__str__(), None)
                    if not team:
                        print(f"Team id was not specified in JSON: {team_id}")
                    else:
                        resolved_teams.append(team)

            current_team = f'Plays for {resolved_teams[0]}\n' if resolved_teams else ''

            if len(resolved_teams) > 1:
                old_teams = f'Old teams: {join(", ", resolved_teams[1:])}\n'
            else:
                old_teams = ''

            if len(names) > 1:
                other_names = truncate("_ᴬᴷᴬ_ " + ', '.join(names[1:]) + "\n", 1022, "…\n")
            else:
                other_names = ''

            chars = "\\"
            battlefy = ''
            for battlefy_profile in p.battlefy.slugs:
                battlefy += f'[{escape_characters(battlefy_profile.value, chars)}]' \
                            f'({battlefy_profile.uri})\n'

            twitch = ''
            for twitch_profile in p.twitch_profiles:
                twitch += f'[{escape_characters(twitch_profile.value, chars)}]' \
                            f'({twitch_profile.uri})\n'

            twitter = ''
            for twitter_profile in p.twitter_profiles:
                twitter += f'[{escape_characters(twitter_profile.value, chars)}]' \
                            f'({twitter_profile.uri})\n'

            player_sources: List[UUID] = p.sources
            player_sources.reverse()  # Reverse so last added source is first ...
            player_source_names: List[str] = []
            for source in player_sources:
                from core_classes.builtins import BuiltinSource
                if source == BuiltinSource.guid:
                    player_source_names.append("(builtin)")
                else:
                    name = sources.get(source.__str__(), None)
                    if not name:
                        print(f"Source was not specified in JSON: {source}")
                    else:
                        player_source_names.append(name)
            player_sources: str = \
                "\n ".join(list(map(lambda s: attempt_link_source(s), player_source_names)))
            top500 = "👑 " if p.top500 else ''
            country_flag = p.country_flag + ' ' if p.country_flag else ''
            low_ink_tourney = has_won_low_ink(placements_for_players, low_ink_sources, p)
            banned_from_low_ink = f"🚫 Won LowInk in {low_ink_tourney}\n" if low_ink_tourney else ''

            # If there's just the one matched player, move the sources to the next field.
            if matched_players_len == 1:
                info = f'{other_names}{current_team}{old_teams}{twitch}{twitter}{battlefy}{banned_from_low_ink}'
                builder.add_field(name=truncate(country_flag + top500 + current_name, 256, "") or ' ',
                                  value=truncate(info, 1023, "…_"),
                                  inline=False)

                builder.add_field(name='\tSources:',
                                  value=truncate('_' + player_sources + '_', 1023, "…_"),
                                  inline=False)
            else:
                info = f'{other_names}{current_team}{old_teams}{twitch}{twitter}{battlefy}\n' \
                       f'_{player_sources}_'
                builder.add_field(name=truncate(country_flag + top500 + current_name, 256, "") or ' ',
                                  value=truncate(info, 1023, "…_"),
                                  inline=False)

    if has_matched_teams:
        separator = ',\n' if matched_teams_len == 1 else ', '

        for i in range(0, MAX_RESULTS):
            if i >= matched_teams_len:
                break

            t = matched_teams[i]
            players = matched_players_for_teams[t.guid.__str__()]
            player_strings = ''
            for player_tuple in players:
                if player_tuple:
                    p = player_tuple["Item1"]
                    in_team = player_tuple["Item2"]
                    name = escape_characters(p.name.value)
                    player_strings += \
                        f'{name} {("(Most recent)" if in_team else "(Ex)" if in_team is False else "")}'
                    player_strings += separator

            player_strings = player_strings[0:-len(separator)]
            div_phrase = Team.best_team_player_div_string(t, players, known_teams)
            if div_phrase:
                div_phrase += '\n'
            team_sources: List[UUID] = t.sources
            team_sources.reverse()  # Reverse so last added source is first ...
            team_source_names: List[str] = []
            for source in team_sources:
                from core_classes.builtins import BuiltinSource
                if source == BuiltinSource.guid:
                    team_source_names.append("(builtin)")
                else:
                    name = sources.get(source.__str__(), None)
                    if not name:
                        print(f"Source was not specified in JSON: {source}")
                    else:
                        team_source_names.append(name)
            team_sources: str = \
                "\n ".join(list(map(lambda s: attempt_link_source(s), team_source_names)))

            # If there's just the one matched team, move the sources to the next field.
            if matched_teams_len == 1:
                info = f'{div_phrase}Players: {player_strings}'
                builder.add_field(name=truncate(t.__str__(), 256, "") or "Unnamed Team",
                                  value=truncate(info, 1023, "…_"),
                                  inline=False)

                builder.add_field(name='\tSources:',
                                  value=truncate('_' + team_sources + '_', 1023, "…_"),
                                  inline=False)
            else:
                info = f'{div_phrase}Players: {player_strings}\n' \
                       f'_{team_sources}_'
                builder.add_field(name=truncate(t.__str__(), 256, "") or "Unnamed Team",
                                  value=truncate(info, 1023, "…_"),
                                  inline=False)

    builder.set_footer(
        text=f"Fetched in {int((datetime.utcnow() - now).microseconds / 1000)} milliseconds. " +
             (f'Only the first {MAX_RESULTS} results are shown for players and teams.' if show_limited else ''),
        icon_url="https://media.discordapp.net/attachments/471361750986522647/758104388824072253/icon.png")
    return builder, embed_colour


def has_won_low_ink(placements_for_players: Dict[str, Dict[str, List[Bracket]]],
                    low_ink_sources: Dict[str, str],
                    p: Player) -> Optional[str]:
    """
    Get if the player has won Low Ink (and is therefore banned).
    Returns the tournament they won (or None)
    :param placements_for_players: The Placements dictionary
    :param low_ink_sources: The Sources, pre-filtered to LowInk sources
    :param p: The Player
    :return: The tournament UUID they won (or None)
    """

    if p.guid.__str__() in placements_for_players:
        sources = placements_for_players[p.guid.__str__()]
        for source in sources:
            if source in low_ink_sources:
                brackets = placements_for_players[p.guid.__str__()][source]
                for bracket in brackets:
                    if bracket.name.lower() == 'alpha' or bracket.name.lower() == 'top cut':
                        if p.guid in bracket.placements.players_by_placement[1]:
                            return low_ink_sources[source]  # return the name.
    return None
