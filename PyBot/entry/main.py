import asyncio
import os
import re
import sys
import traceback
from asyncio import Queue
from datetime import datetime
from typing import Optional, Union, List

import discord
import requests
from discord import Role, Guild, Embed
from discord.ext import commands
from discord.ext.commands import Bot, Context, CommandNotFound

from helpers.str_helper import equals_ignore_case
from slapp_py.slapipes import initialise_slapp, query_slapp, process_slapp
from tokens import BOT_TOKEN, CLIENT_ID, OWNER_ID

COMMAND_PREFIX = '~'
IMAGE_FORMATS = ["image/png", "image/jpeg", "image/jpg"]
slapp_ctx_queue: Queue[(Context, datetime)] = Queue()

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
        name='verify',
        description="Verify a signed-up team.",
        help=f'{COMMAND_PREFIX}verify <team_slug>',
        pass_ctx=True)
    async def verify(ctx: Context, team_slug_or_confirmation: Optional[str]):
        november_2020_low_ink = '5f98cdae7d10b0459b2812dd'
        from misc.download_from_battlefy import download_from_battlefy
        tournament: dict = download_from_battlefy(november_2020_low_ink)
        if len(tournament) == 1:
            tournament = tournament[0]

        if len(tournament) == 0:
            await ctx.send(f"I couldn't download the latest tournament data 😔 (id: {november_2020_low_ink})")
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
                            await slapp_ctx_queue.put((ctx, datetime.now()))
                            await query_slapp(player_slug)
                else:
                    continue

        if verification_message:
            await ctx.send(verification_message)

    @bot.command(
        name='Slapp',
        description="Query the slapp for a Splatoon player, team, tag, or other information",
        brief="Splatoon player and team lookup",
        aliases=['slapp', 'splattag'],
        help=f'{COMMAND_PREFIX}slapp <query>',
        pass_ctx=True)
    async def slapp(ctx: Context, *, query):
        print('slapp called with query ' + query)
        await slapp_ctx_queue.put((ctx, datetime.now()))
        await query_slapp(query)

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

    async def send_slapp(ctx: Context, now: datetime, success_message: str, response: dict):
        if success_message == "OK":
            try:
                builder, colour = process_slapp(response, now)
            except Exception as e:
                await ctx.send(content=f'Something went wrong processing the result from Slapp. Blame Slate. 😒🤔 '
                                       f'({e.__str__()})')
                print(traceback.format_exc())
                return

            try:
                removed_fields: List[dict] = []
                message = 1
                while message <= 10:
                    while builder.__len__() > 6000 or len(builder.fields) > 20:
                        index = len(builder.fields) - 1
                        removed: dict = builder._fields[index]
                        builder.remove_field(index)
                        removed_fields.append(removed)

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

    async def receive_slapp_response(success_message: str, response: dict):
        if slapp_ctx_queue.empty():
            print(f"receive_slapp_response but queue is empty. Discarding result: {success_message=}, {response=}")
        else:
            ctx, now = await slapp_ctx_queue.get()
            await send_slapp(ctx, now, success_message, response)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(
            initialise_slapp(receive_slapp_response),
            bot.start(BOT_TOKEN)
        )
    )
    print("Main exited!")
