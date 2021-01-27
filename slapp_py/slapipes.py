"""
This slapipes module handles the communication between Slapp and Dola.
The pipes to the Slapp.
"""

import asyncio
import base64
import binascii
import json
import os
import traceback
from asyncio import Queue
from datetime import datetime
from typing import List, Dict, Union, Callable, Any, Awaitable
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


async def _default_response_handler(success_message: str, response: dict) -> None:
    assert False, f"Slapp response handler not set. Discarding: {success_message=}, {response=}"


response_function: Callable[[str, dict], Awaitable[None]] = _default_response_handler


async def _read_stdout(stdout):
    global response_function
    print('_read_stdout')
    while True:
        try:
            response = (await stdout.readline())
            if not response:
                print('stdout: (none response)')
                await asyncio.sleep(1)
            elif response.startswith(b"eyJNZXNzYWdlIjoiT"):  # This is the b64 start of a Slapp message.
                decoded_bytes = base64.b64decode(response)
                response = json.loads(str(decoded_bytes, "utf-8"))
                await response_function(response.get("Message", "Response does not contain Message."), response)
            else:
                print('stdout: ' + response.decode('utf-8'))
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


async def initialise_slapp(new_response_function: Callable[[str, dict], Any]):
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


async def query_slapp(query: str):
    """Query Slapp. The response comes back through the callback function that was passed in initialise_slapp."""

    if '--exactCase' in query:
        query = query.replace('--exactCase', '') + " --exactCase"

    if '--queryIsRegex' in query:
        query = query.replace('--queryIsRegex', '') + " --queryIsRegex"

    print(f"Posting {query=} to existing Slapp process...")
    await slapp_write_queue.put('--b64 ' + str(base64.b64encode(query.encode("utf-8")), "utf-8"))


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

    for source_id in response.get("Sources"):
        source_name = response.get("Sources")[source_id]
        sources[source_id] = source_name

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
            notable_results = get_first_placements(placements_for_players, sources, p)

            # If there's just the one matched player, move the sources to the next field.
            if matched_players_len == 1:
                info = f'{other_names}{current_team}{old_teams}{twitch}{twitter}{battlefy}'
                builder.add_field(name=truncate(country_flag + top500 + current_name, 256, "") or ' ',
                                  value=truncate(info, 1023, "…_"),
                                  inline=False)

                if len(notable_results):
                    notable_results_str = ''
                    for win in notable_results:
                        notable_results_str += '🏆 Won ' + win + '\n'

                    builder.add_field(name='\tNotable Wins:',
                                      value=truncate(notable_results_str, 1023, "…_"),
                                      inline=False)

                builder.add_field(name='\tSources:',
                                  value=truncate('_' + player_sources + '_', 1023, "…_"),
                                  inline=False)
            else:
                if len(notable_results):
                    notable_results_str = '🏆 Won ' + ', '.join(notable_results) + '\n'
                else:
                    notable_results_str = ''

                info = f'{other_names}{current_team}{old_teams}{twitch}{twitter}{battlefy}{notable_results_str}\n' \
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


def get_first_placements(placements_for_players: Dict[str, Dict[str, List[Bracket]]],
                         source_ids_to_name: Dict[str, str],
                         p: Player) -> List[str]:
    result = []
    print(f"get_first_placements: Searching {p.guid.__str__()}, "
          f"has persistent ids: {', '.join(p.battlefy.battlefy_persistent_id_strings)}")
    if p.guid.__str__() in placements_for_players:
        print(f"get_first_placements: Found {p.guid.__str__()} in placements_for_players")
        sources = placements_for_players[p.guid.__str__()]
        for source_id in sources:
            brackets = placements_for_players[p.guid.__str__()][source_id]
            print(f"get_first_placements: Looking at {len(brackets)} brackets under {source_ids_to_name[source_id]}")
            for bracket in brackets:
                first_place_ids = [player_id.__str__() for player_id in bracket.placements.players_by_placement[1]]
                print(f"get_first_placements: {bracket.name=}: Looking for ids {', '.join(first_place_ids)}")
                if p.guid.__str__() in first_place_ids:
                    print(f"get_first_placements: p.guid is in bracket.placements.players_by_placement[1]!")
                    result.append(bracket.name + ' in ' + source_ids_to_name[source_id])
                elif p.guid in bracket.players:
                    found = False
                    print(f"get_first_placements: Found the player guid in the bracket. "
                          f"Searching {bracket.placements.players_by_placement} ranks.")
                    for place in bracket.placements.players_by_placement:
                        p_ids = [player_id.__str__() for player_id in bracket.placements.players_by_placement[place]]
                        if p.guid.__str__() in p_ids:
                            print(f"get_first_placements: The player placed [{place}].")
                            found = True

                    if not found:
                        print(f"get_first_placements: Didn't find the guid in placements. Here they are: ")
                        print(f"get_first_placements: " + json.dumps(bracket.placements.players_by_placement,
                                                                     default=str, indent=2))
                else:
                    print(f"get_first_placements: Did not find the player guid in this bracket.")

    return result


def has_won_low_ink(placements_for_players: Dict[str, Dict[str, List[Bracket]]],
                    source_ids_to_name: Dict[str, str],
                    p: Player) -> List[str]:
    """
    Get if the player has won Low Ink (and is therefore banned).
    Returns the tournament they won (or None)
    :param placements_for_players: The Placements dictionary
    :param source_ids_to_name: The source lookup dictionary
    :param p: The Player
    :return: The tournament name they won (or None)
    """

    result = []
    if p.guid.__str__() in placements_for_players:
        sources = placements_for_players[p.guid.__str__()]
        for source_id in sources:
            if source_id in filter_low_ink_sources(source_ids_to_name):
                brackets = placements_for_players[p.guid.__str__()][source_id]
                for bracket in brackets:
                    if 'alpha' in bracket.name.lower() or 'top cut' in bracket.name.lower():
                        if p.guid in bracket.placements.players_by_placement[1]:
                            result.append(source_ids_to_name[source_id])
    return result


def filter_low_ink_sources(sources: Dict[str, str]) -> Dict[str, str]:
    return {k: v for k, v in sources.items() if 'low-ink-' in v}
