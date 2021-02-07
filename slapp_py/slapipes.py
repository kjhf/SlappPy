"""
This slapipes module handles the communication between Slapp and Dola.
The pipes to the Slapp.
"""

import asyncio
import base64
import json
import os
import re
import traceback
from asyncio import Queue
from typing import List, Dict, Union, Callable, Any, Awaitable, Set
from uuid import UUID

from discord import Color, Embed

from PyBot.helpers.embed_helper import to_embed
from core_classes.bracket import Bracket
from core_classes.player import Player
from core_classes.skill import Skill
from core_classes.team import Team
from helpers.dict_helper import from_list
from helpers.str_helper import join, truncate
from slapp_py.footer_phrases import get_random_footer_phrase
from slapp_py.strings import escape_characters, attempt_link_source

MAX_RESULTS = 20
slapp_write_queue: Queue[str] = Queue()
slapp_loop = True


async def _default_response_handler(success_message: str, response: dict) -> None:
    assert False, f"Slapp response handler not set. Discarding: {success_message=}, {response=}"


response_function: Callable[[str, dict], Awaitable[None]] = _default_response_handler


async def _read_stdout(stdout):
    global response_function
    global slapp_loop

    print('_read_stdout')
    while slapp_loop:
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
    global slapp_loop

    print('_read_stderr')
    while slapp_loop:
        try:
            response: str = (await stderr.readline()).decode('utf-8')
            if not response:
                print('stderr: none response, this indicates Slapp has exited.')
                print('stderr: Terminating slapp_loop.')
                slapp_loop = False
                break
            else:
                print('stderr: ' + response)
        except Exception as e:
            print(f'_read_stderr EXCEPTION: {e}\n{traceback.format_exc()}')


async def _write_stdin(stdin):
    global slapp_loop

    print('_write_stdin')
    while slapp_loop:
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


async def _run_slapp(slapp_path: str, mode: str):
    global slapp_loop

    proc = await asyncio.create_subprocess_shell(
        f'dotnet \"{slapp_path}\" \"%#%@%#%\" {mode}',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        encoding=None,  # encoding must be None
        errors=None,  # errors must be None
        shell=True,
        limit=100 * 1024 * 1024,  # 100 MiB
    )

    slapp_loop = True
    await asyncio.gather(
        _read_stderr(proc.stderr),
        _read_stdout(proc.stdout),
        _write_stdin(proc.stdin)
    )
    print("_run_slapp returned!")


async def initialise_slapp(new_response_function: Callable[[str, dict], Any], mode: str = "--keepOpen"):
    import subprocess
    global response_function

    print("Initialising Slapp ...")
    result = subprocess.run(['cd'], stdout=subprocess.PIPE, encoding='utf-8', shell=True)
    slapp_path = result.stdout.strip(" \r\n")
    print('cd: ' + slapp_path)
    if 'SlapPy' in slapp_path:
        slapp_path = slapp_path[0:slapp_path.index('SlapPy')]
    slapp_path = os.path.join(slapp_path, 'SlapPy', 'venv', 'Slapp', 'SplatTagConsole.dll')
    assert os.path.isfile(slapp_path), f'Not a file: {slapp_path}'
    Skill.setup()

    print(f"Using Slapp found at {slapp_path}")
    response_function = new_response_function
    await _run_slapp(slapp_path, mode)


async def query_slapp(query: str):
    """Query Slapp. The response comes back through the callback function that was passed in initialise_slapp."""
    options: Set[str] = set()

    # Handle options
    insensitive_exact_case = re.compile(re.escape('--exactcase'), re.IGNORECASE)
    (query, n) = insensitive_exact_case.subn('', query)
    query = query.strip()
    if n:
        options.add("--exactCase")

    insensitive_match_case = re.compile(re.escape('--matchcase'), re.IGNORECASE)
    (query, n) = insensitive_match_case.subn('', query)
    query = query.strip()
    if n:
        options.add("--exactCase")

    insensitive_query_is_regex = re.compile(re.escape('--queryisregex'), re.IGNORECASE)
    (query, n) = insensitive_query_is_regex.subn('', query)
    query = query.strip()
    if n:
        options.add("--queryIsRegex")

    insensitive_regex = re.compile(re.escape('--regex'), re.IGNORECASE)
    (query, n) = insensitive_regex.subn('', query)
    query = query.strip()
    if n:
        options.add("--queryIsRegex")

    print(f"Posting {query=} to existing Slapp process with options {' '.join(options)} ...")
    await slapp_write_queue.put('--b64 ' + str(base64.b64encode(query.encode("utf-8")), "utf-8") + ' ' +
                                ' '.join(options))


async def slapp_describe(slapp_id: str):
    await slapp_write_queue.put(f'--slappId {slapp_id}')


def process_slapp(response: dict) -> (Embed, Color):
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
            names = list(set([escape_characters(name.value) for name in p.names if name and name.value]))
            current_name = f"{names[0]}" if len(names) else "(Unnamed Player)"

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

            current_team = f'Plays for: ```{resolved_teams[0]}```\n' if resolved_teams else ''

            if len(resolved_teams) > 1:
                old_teams = truncate('Old teams: \n```' + join("\n", resolved_teams[1:]) + '```\n', 1000, "…\n```\n")
            else:
                old_teams = ''

            if len(names) > 1:
                other_names = truncate("_ᴬᴷᴬ_ ```" + '\n'.join(names[1:]) + "```\n", 1000, "…\n```\n")
            else:
                other_names = ''

            battlefy = ''
            for battlefy_profile in p.battlefy.slugs:
                battlefy += f'⚔ Battlefy (Slug): [{escape_characters(battlefy_profile.value)}]' \
                            f'({battlefy_profile.uri})\n'

            discord = ''
            for discord_profile in p.discord.ids:
                did = escape_characters(discord_profile.value)
                discord += f'🎮 Discord ID: [{did}]' \
                            f'(https://discord.id/), 🦑 [Sendou](https://sendou.ink/u/{did})\n'

            twitch = ''
            for twitch_profile in p.twitch_profiles:
                twitch += f'📽 Twitch: [{escape_characters(twitch_profile.value)}]' \
                            f'({twitch_profile.uri})\n'

            twitter = ''
            for twitter_profile in p.twitter_profiles:
                twitter += f'🐦 Twitter: [{escape_characters(twitter_profile.value)}]' \
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
            player_sources: List[str] = list(map(lambda s: attempt_link_source(s), player_source_names))
            top500 = "👑 " if p.top500 else ''
            country_flag = p.country_flag + ' ' if p.country_flag else ''
            notable_results = get_first_placements(placements_for_players, sources, p)

            if '`' in current_name:
                current_name = f"```{current_name}```"
            elif '_' in current_name or '*' in current_name:
                current_name = f"`{current_name}`"
            field_head = truncate(country_flag + top500 + current_name, 256) or ' '

            # If there's just the one matched player, move the extras to another field.
            if matched_players_len == 1 and matched_teams_len < 15:
                field_body = f'{other_names}'
                builder.add_field(name=field_head,
                                  value=truncate(field_body, 1023, "…") or "(Nothing else to say)",
                                  inline=False)

                if current_team or old_teams:
                    field_body = f'{current_team}{old_teams}'
                    builder.add_field(name='    Teams:',
                                      value=truncate(field_body, 1023, "…") or "(Nothing else to say)",
                                      inline=False)

                if twitch or twitter or battlefy or discord:
                    field_body = f'{twitch}{twitter}{battlefy}{discord}'
                    builder.add_field(name='    Socials:',
                                      value=truncate(field_body, 1023, "…") or "(Nothing else to say)",
                                      inline=False)

                if len(notable_results):
                    notable_results_str = ''
                    for win in notable_results:
                        notable_results_str += '🏆 Won ' + win + '\n'

                    builder.add_field(name='    Notable Wins:',
                                      value=truncate(notable_results_str, 1023, "…"),
                                      inline=False)

                if len(p.weapons):
                    builder.add_field(name='    Weapons:',
                                      value=truncate(', '.join(p.weapons), 1023, "…"),
                                      inline=False)

                if len(player_sources):
                    for source_batch in range(0, 15):
                        sources_count = len(player_sources)
                        value = ''
                        for j in range(0, min(sources_count, 6)):
                            value += player_sources[j] + '\n'

                        builder.add_field(name='    ' + f'Sources ({(source_batch + 1)}):',
                                          value=truncate(value, 1023, "…"),
                                          inline=False)

                        player_sources = player_sources[min(sources_count, 7):]
                        if len(player_sources) <= 0:
                            break

            else:
                if len(notable_results):
                    notable_results_str = ''
                    for win in notable_results:
                        notable_results_str += '🏆 Won ' + win + '\n'
                else:
                    notable_results_str = ''

                additional_info = "\n `~full " + p.guid.__str__() + "`\n"

                player_sources: str = "Sources:\n" + "\n".join(player_sources)
                field_body = (f'{other_names}{current_team}{old_teams}'
                              f'{twitch}{twitter}{battlefy}{discord}'
                              f'{notable_results_str}{player_sources}') or "(Nothing else to say)"
                if len(field_body) + len(additional_info) < 1024:
                    field_body += additional_info
                else:
                    field_body = truncate(field_body, 1020 - len(additional_info), indicator="…")
                    if (field_body.count('```') % 2) == 1:  # If we have an unclosed ```
                        field_body += '```'
                    field_body += additional_info

                builder.add_field(name=field_head, value=field_body, inline=False)

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
                    name = p.name.value
                    if '`' in name:
                        name = f"```{name}```"
                    elif '_' in name or '*' in name:
                        name = f"`{name}`"

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
            team_sources: str = "\n ".join([attempt_link_source(s) for s in team_source_names])

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
        text=get_random_footer_phrase() + (
            f'Only the first {MAX_RESULTS} results are shown for players and teams.' if show_limited else ''
        ),
        icon_url="https://media.discordapp.net/attachments/471361750986522647/758104388824072253/icon.png")
    return builder, embed_colour


def get_first_placements(placements_for_players: Dict[str, Dict[str, List[Bracket]]],
                         source_ids_to_name: Dict[str, str],
                         p: Player) -> List[str]:
    result = []
    if p.guid.__str__() in placements_for_players:
        sources = placements_for_players[p.guid.__str__()]
        for source_id in sources:
            brackets = placements_for_players[p.guid.__str__()][source_id]
            for bracket in brackets:
                if 1 in bracket.placements.players_by_placement:
                    first_place_ids = [player_id.__str__() for player_id in bracket.placements.players_by_placement[1]]
                    if p.guid.__str__() in first_place_ids:
                        result.append(bracket.name + ' in ' + attempt_link_source(source_ids_to_name[source_id]))

    return result
