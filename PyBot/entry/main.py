import asyncio
import os
import re
import sys
import traceback
from collections import deque, namedtuple
from operator import itemgetter
from typing import Optional, Union, List, Tuple, Deque, Dict

import discord
import requests
from discord import Role, Guild, Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, CommandNotFound

from PyBot.constants.emojis import TROPHY, CROWN
from core_classes.builtins import UNKNOWN_PLAYER
from core_classes.player import Player
from core_classes.skill import Skill
from helpers.str_helper import equals_ignore_case, truncate
from slapp_py.slapipes import initialise_slapp, query_slapp, process_slapp, slapp_describe
from slapp_py.slapp_response_object import SlappResponseObject
from slapp_py.weapons import get_random_weapon
from tokens import BOT_TOKEN, CLIENT_ID, OWNER_ID

COMMAND_PREFIX = '~'
IMAGE_FORMATS = ["image/png", "image/jpeg", "image/jpg"]
SlappQueueItem = namedtuple('SlappQueueItem', ('Context', 'str'))
slapp_ctx_queue: Deque[SlappQueueItem] = deque()

if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True  # Subscribe to the privileged members intent for roles.
    intents.presences = False
    intents.typing = False
    bot: Bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, owner_id=OWNER_ID)

    @bot.command(
        name='jpg',
        description='jpgs your avatar',
        pass_ctx=True
    )
    async def jpg(ctx: Context, quality_or_url: Union[str, int] = 10, quality: int = 10):
        try:
            import tempfile
            (handle_int, filename) = tempfile.mkstemp('.jpg')
            if isinstance(quality_or_url, str) and re.match(r"[-+]?\d+$", quality_or_url) is None:
                with open(filename, 'wb') as handle:
                    r = requests.head(quality_or_url)
                    if r.headers["content-type"] not in IMAGE_FORMATS:
                        await ctx.send(f"Something went wrong 😔 (not an image)")
                        return

                    r = requests.get(quality_or_url, stream=True)
                    if r.status_code != 200:
                        await ctx.send(f"Something went wrong 😔 {r.__str__()}")
                        return

                    for block in r.iter_content(1024):
                        if not block:
                            break
                        handle.write(block)
                print(f'Saved url {quality_or_url} temp to {filename}')
            else:
                quality = int(quality_or_url)
                await ctx.author.avatar_url.save(filename)
                print(f'Saved {ctx.author} avatar at url {ctx.author.avatar_url} temp to {filename}')

            from PIL import Image
            im = Image.open(filename)
            im = im.convert("RGB")
            im.save(filename, format='JPEG', quality=quality)

            file = discord.File(fp=filename)
            await ctx.send(f"Here you go! (Quality: {quality})", file=file)
            os.close(handle_int)
            os.remove(filename)
        except Exception as e:
            await ctx.send(f"Something went wrong 😔 {e}")

    @bot.command(
        name='Hello',
        description="Says hello.",
        brief="Says hi.",
        aliases=['hello', 'hi', 'hey'],
        help=f'{COMMAND_PREFIX}hello.',
        pass_ctx=True)
    async def hello(ctx: Context):
        await ctx.send("Hello, {}".format(ctx.message.author.mention))

    @bot.command(
        name='Weapon',
        description="Draws a random Splatoon 2 weapon.",
        brief="Draws a random Splatoon 2 weapon.",
        aliases=['weapon'],
        help=f'{COMMAND_PREFIX}weapon.',
        pass_ctx=True)
    async def weapon(ctx: Context):
        await ctx.send(get_random_weapon())

    @bot.command(
        name='Invite',
        description="Grab an invite link.",
        brief="Grab an invite link.",
        aliases=['invite'],
        help=f'{COMMAND_PREFIX}invite',
        pass_ctx=True)
    async def invite(ctx: Context):
        await ctx.send(f"https://discordapp.com/oauth2/authorize?client_id={CLIENT_ID}&scope=bot")

    @bot.command(
        name='Members',
        description="Count number of members with a role specified, or leave blank for all in the server.",
        brief="Member counting.",
        aliases=['members', 'count_members'],
        help=f'{COMMAND_PREFIX}members [role]',
        pass_ctx=True)
    async def members(ctx: Context, role: Optional[Role]):
        guild: Optional[Guild] = ctx.guild
        if guild:
            await ctx.guild.fetch_roles()
            ctx.guild.fetch_members(limit=None)
            if role:
                count = sum(1 for user in guild.members if role in user.roles)
                await ctx.send(f"{count}/{guild.member_count} users are in this server with the role {role.name}!")
            else:
                await ctx.send(f"{guild.member_count} users are in the server!")
        else:
            await ctx.send("Hmm... we're not in a server! 😅")


    @bot.command(
        name='autoseed',
        description="Auto seed the teams that have signed up to the tourney",
        help=f'{COMMAND_PREFIX}autoseed <tourney_id>',
        pass_ctx=True)
    async def autoseed(ctx: Context, tourney_id: Optional[str]):
        if not tourney_id:
            tourney_id = '6019b6d0ce01411daff6bca6'

        from misc.download_from_battlefy_result import download_from_battlefy
        tournament = list(download_from_battlefy(tourney_id, force=True))
        if isinstance(tournament, list) and len(tournament) == 1:
            tournament = tournament[0]

        if len(tournament) == 0:
            await ctx.send(f"I couldn't download the latest tournament data 😔 (id: {tourney_id})")
            return

        if not any(team.get('players', None) for team in tournament):
            await ctx.send(f"There are no teams in this tournament 😔 (id: {tourney_id})")
            return

        verification_message = ''
        slapp_ctx_queue.append(SlappQueueItem(None, 'autoseed_start'))

        for team in tournament:
            name = team.get('name', None)
            team_id = team.get('persistentTeamID', None)

            if not name or not team_id:
                continue

            players = team.get('players', None)
            if not players:
                verification_message += f'The team {name} ({team_id}) has no players!\n'
                continue

            ignored_players = [truncate(player.get("inGameName", "(unknown player)"), 25, '…')
                               for player in players if not player.get('persistentPlayerID')]

            players = [player for player in players if player.get('persistentPlayerID')]
            if len(players) < 4:
                verification_message += f"Ignoring the player(s) from team {name} ({team_id}) as they don't have a persistent id: [{', '.join(ignored_players)}]\n"
                verification_message += f"The team {name} ({team_id}) only has {len(players)} players, not calculating.\n"
                continue

            for player in players:
                player_slug = player['persistentPlayerID']  # We've already verified this field is good
                slapp_ctx_queue.append(SlappQueueItem(None, 'autoseed:' + name))
                await query_slapp(player_slug)

        # Finish off the autoseed list
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'autoseed_end'))

        if verification_message:
            await ctx.send(verification_message)

        # Finished in handle_autoseed


    @bot.command(
        name='verify',
        description="Verify a signed-up team.",
        help=f'{COMMAND_PREFIX}verify <team_slug>',
        pass_ctx=True)
    async def verify(ctx: Context, team_slug_or_confirmation: Optional[str], low_ink_id: Optional[str]):
        if not low_ink_id:
            low_ink_id = '6019b6d0ce01411daff6bca6'

        from misc.download_from_battlefy_result import download_from_battlefy
        tournament = list(download_from_battlefy(low_ink_id))
        if isinstance(tournament, list) and len(tournament) == 1:
            tournament = tournament[0]

        if len(tournament) == 0:
            await ctx.send(f"I couldn't download the latest tournament data 😔 (id: {low_ink_id})")
            return

        if not team_slug_or_confirmation:
            await ctx.send(f"Found {len(tournament)} teams. To verify all these teams use `{COMMAND_PREFIX}verify all`")
            return

        do_all: bool = equals_ignore_case(team_slug_or_confirmation, 'all')
        verification_message: str = ""

        if do_all:
            verification_message: str = "I'm working on it, come back later :) - Slate"
        else:
            team_slug = team_slug_or_confirmation
            for team in tournament:
                name = team['name'] if 'name' in team else None
                team_id = team['persistentTeamID'] if 'persistentTeamID' in team else None
                if not name or not team_id:
                    verification_message += f'The team data is incomplete or in a bad format.\n'
                    break

                if team['_id'] == team_slug or team['persistentTeamID'] == team_slug:
                    players = team['players'] if 'players' in team else None
                    if not players:
                        verification_message += f'The team {name} ({team_id}) has no players!\n'
                        continue
                    await ctx.send(content=f'Checking team: {name} ({team_id})')

                    for player in players:
                        player_slug = player['userSlug'] if 'userSlug' in player else None
                        if not player_slug:
                            verification_message += f'The team {name} ({team_id}) has a player with no slug!\n'
                            continue
                        else:
                            slapp_ctx_queue.append(SlappQueueItem(ctx, 'verify'))
                            await query_slapp(player_slug)
                else:
                    continue

        if verification_message:
            await ctx.send(verification_message)

    @bot.command(
        name='Slapp',
        description="Query the slapp for a Splatoon player, team, tag, or other information",
        brief="Splatoon player and team lookup",
        aliases=['slapp', 'splattag', 'search'],
        help=f'{COMMAND_PREFIX}search <query>',
        pass_ctx=True)
    async def slapp(ctx: Context, *, query):
        print('slapp called with query ' + query)
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'slapp'))
        await query_slapp(query)


    @bot.command(
        name='Slapp (Full description)',
        description="Fully describe the given id.",
        brief="Splatoon player or team full description",
        aliases=['full', 'describe'],
        help=f'{COMMAND_PREFIX}full <slapp_id>',
        pass_ctx=True)
    async def full(ctx: Context, slapp_id: str):
        print('full called with query ' + slapp_id)
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'full'))
        await slapp_describe(slapp_id)


    @bot.command(
        name='Fight teams/players',
        description="Get a match rating and predict the winner between two teams or two players.",
        brief="Two Splatoon teams/players to fight and rate winner",
        aliases=['fight', 'predict'],
        help=f'{COMMAND_PREFIX}predict <slapp_id_1> <slapp_id_2>',
        pass_ctx=True)
    async def predict(ctx: Context, slapp_id_team_1: str, slapp_id_team_2: str):
        print(f'predict called with teams {slapp_id_team_1=} {slapp_id_team_2=}')
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'predict_1'))
        await slapp_describe(slapp_id_team_1)
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'predict_2'))
        await slapp_describe(slapp_id_team_2)
        # This comes back in the receive_slapp_response -> handle_predict

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, CommandNotFound):
            return
        raise error

    @bot.event
    async def on_message(message):
        # We do not want the bot to reply to itself
        if message.author == bot.user:
            return
        await bot.process_commands(message)

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user.name}, id {bot.user.id}')

        # noinspection PyUnreachableCode
        if __debug__:
            presence = "--=IN DEV=--"
        else:
            presence = "with Slate"

        if 'pydevd' in sys.modules or 'pdb' in sys.modules or '_pydev_bundle.pydev_log' in sys.modules:
            presence += ' (Debug Attached)'

        await bot.change_presence(activity=discord.Game(name=presence))

    async def send_slapp(ctx: Context, success_message: str, response: dict):
        if success_message == "OK":
            try:
                builder, colour = process_slapp(response)
            except Exception as e:
                await ctx.send(content=f'Something went wrong processing the result from Slapp. Blame Slate. 😒🤔 '
                                       f'({e.__str__()})')
                print(traceback.format_exc())
                return

            try:
                removed_fields: List[dict] = []
                message = 1
                # Only send 10 messages tops
                while message <= 10:
                    # While the message is more than the allowed 6000, or
                    # The message has more than 20 fields, or
                    # The removed fields has one only (the footer cannot be alone)
                    while builder.__len__() > 6000 or len(builder.fields) > 20 or len(removed_fields) == 1:
                        index = len(builder.fields) - 1
                        removed: dict = builder._fields[index]
                        builder.remove_field(index)
                        removed_fields.append(removed)

                    if builder:
                        await ctx.send(embed=builder)

                    if len(removed_fields):
                        message += 1
                        removed_fields.reverse()
                        builder = Embed(title=f'Page {message}', colour=colour, description='')
                        for field in removed_fields:
                            try:
                                builder._fields.append(field)
                            except AttributeError:
                                builder._fields = [field]
                        removed_fields.clear()
                    else:
                        break

            except Exception as e:
                await ctx.send(content=f'Too many results, sorry 😔 ({e.__str__()})')
                print(traceback.format_exc())
                print(f'Attempted to send:\n{builder.to_dict()}')
        else:
            await ctx.send(content=f'Unexpected error from Slapp 🤔: {success_message}')


    global_handle_autoseed_list: Optional[Dict[str, List[dict]]] = dict()

    async def handle_autoseed(ctx: Optional[Context], description: str, response: Optional[dict]):
        global global_handle_autoseed_list

        if description.startswith("autoseed_start"):
            global_handle_autoseed_list.clear()
        elif not description.startswith("autoseed_end"):
            team_name = description.rpartition(':')[2]  # take the right side of the colon
            if global_handle_autoseed_list.get(team_name):
                global_handle_autoseed_list[team_name].append(response)
            else:
                global_handle_autoseed_list[team_name] = [response]
        else:
            # End, do the thing
            message = ''

            # Team name, list of players, clout, confidence, emoji str
            teams_by_clout: List[Tuple[str, List[str], int, int, str]] = []

            if global_handle_autoseed_list:
                for team_name in global_handle_autoseed_list:
                    team_players = []
                    team_awards = []
                    for player_response in global_handle_autoseed_list[team_name]:
                        r = SlappResponseObject(player_response)

                        if r.matched_players_len == 0:
                            p = Player(names=[r.query or UNKNOWN_PLAYER], sources=r.sources.keys())
                            pass
                        elif r.matched_players_len > 1:
                            p = Player(names=[r.query or UNKNOWN_PLAYER], sources=r.sources.keys())
                            message += f"Too many matches for player {r.query} 😔 " \
                                       f"({r.matched_players_len=})\n"
                        else:
                            p = r.matched_players[0]

                        team_players.append(p)
                        team_awards.append(r.get_first_placements(p))

                    player_skills = [player.skill for player in team_players]
                    player_skills.sort(reverse=True)
                    awards = TROPHY * len({award for award_line in team_awards for award in award_line})
                    awards += CROWN * len([player for player in team_players if player.top500])
                    (_, _), (max_clout, max_confidence) = Skill.team_clout(player_skills)
                    teams_by_clout.append(
                        (team_name,
                         [truncate(player.name.value, 25, '…') for player in team_players],
                         max_clout,
                         max_confidence,
                         awards)
                    )
                teams_by_clout.sort(key=itemgetter(2), reverse=True)
            else:
                message = "Err... I didn't get any teams back from Slapp."

            if message:
                await ctx.send(message)

            message = ''
            lines: List[str] = ["Here's how I'd order the teams and their players from best-to-worst, and assuming each team puts its best 4 players on:\n```"]
            for line in [f"{truncate(tup[0], 50, '…')} (Clout: {tup[2]} with {tup[3]}% confidence) [{', '.join(tup[1])}] {tup[4]}" for tup in teams_by_clout]:
                lines.append(line)

            for line in lines:
                if len(message) + len(line) > 1996:
                    await ctx.send(message + "\n```")
                    message = '```\n'

                message += line + '\n'

            if message:
                await ctx.send(message + "\n```")

    global_handle_predict_team_1: Optional[dict] = None

    async def handle_predict(ctx: Context, description: str, response: dict):
        global global_handle_predict_team_1
        is_part_2 = description == "predict_2"
        if not is_part_2:
            global_handle_predict_team_1 = response
        else:
            response_1 = SlappResponseObject(global_handle_predict_team_1)
            response_2 = SlappResponseObject(response)

            if response_1.matched_players_len == 1 and response_2.matched_players_len == 1:
                matching_mode = 'players'
            elif response_1.matched_teams_len == 1 and response_2.matched_teams_len == 1:
                matching_mode = 'teams'
            else:
                await ctx.send(content=f"I didn't get the right number of players/teams back 😔 "
                                       f"({response_1.matched_players_len=}/{response_1.matched_teams_len=}, "
                                       f"{response_2.matched_players_len=}/{response_2.matched_teams_len=})")
                return

            message = ''
            if matching_mode == 'teams':
                team_1 = response_1.matched_teams[0]
                team_1_skills = response_1.get_team_skills(team_1.guid).values()
                if team_1_skills:
                    (_, _), (max_clout_1, max_conf_1) = Skill.team_clout(team_1_skills)
                    message += Skill.make_message_clout(max_clout_1, max_conf_1, truncate(team_1.name.value, 25, "…")) + '\n'

                team_2 = response_2.matched_teams[0]
                team_2_skills = response_1.get_team_skills(team_2.guid).values()
                if team_2_skills:
                    (_, _), (max_clout_2, max_conf_2) = Skill.team_clout(team_2_skills)
                    message += Skill.make_message_clout(max_clout_2, max_conf_2, truncate(team_2.name.value, 25, "…")) + '\n'

                if team_1_skills and team_2_skills:
                    favouring_team_1, favouring_team_2 = Skill.calculate_quality_of_game_teams(team_1_skills, team_2_skills)
                    if max_conf_1 > 2 and max_conf_2 > 2:
                        if favouring_team_1 != favouring_team_2:
                            message += "Hmm, it'll depend on who's playing, but... "

                        message += Skill.make_message_fairness(favouring_team_1)
                else:
                    message += "Hmm, I don't have any skill information to make a good guess on the outcome."

            elif matching_mode == 'players':
                p1 = response_1.matched_players[0]
                message += Skill.make_message_clout(p1.skill.clout, p1.skill.confidence, truncate(p1.name.value, 25, "…")) + '\n'
                p2 = response_2.matched_players[0]
                message += Skill.make_message_clout(p2.skill.clout, p2.skill.confidence, truncate(p2.name.value, 25, "…")) + '\n'
                quality = Skill.calculate_quality_of_game_players(p1.skill, p2.skill)
                message += Skill.make_message_fairness(quality)
            else:
                message += f"WTF IS {matching_mode}?!"

            await ctx.send(message)


    async def receive_slapp_response(success_message: str, response: dict):
        if len(slapp_ctx_queue) == 0:
            print(f"receive_slapp_response but queue is empty. Discarding result: {success_message=}, {response=}")
        else:
            ctx, description = slapp_ctx_queue.popleft()
            if description.startswith('predict_'):
                if success_message != "OK":
                    await send_slapp(ctx=ctx,
                                     success_message=success_message,
                                     response=response)
                else:
                    await handle_predict(ctx, description, response)
            elif description.startswith('autoseed'):
                if success_message != "OK":
                    await send_slapp(ctx=ctx,
                                     success_message=success_message,
                                     response=response)

                # If the start, send on and read again.
                if description.startswith("autoseed_start"):
                    await handle_autoseed(None, description, None)
                    ctx, description = slapp_ctx_queue.popleft()

                await handle_autoseed(ctx, description, response)

                # Check if last.
                ctx, description = slapp_ctx_queue[0]
                if description.startswith("autoseed_end"):
                    await handle_autoseed(ctx, description, None)
                    slapp_ctx_queue.popleft()

            else:
                await send_slapp(ctx=ctx,
                                 success_message=success_message,
                                 response=response)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(
            initialise_slapp(receive_slapp_response),
            bot.start(BOT_TOKEN)
        )
    )
    print("Main exited!")
