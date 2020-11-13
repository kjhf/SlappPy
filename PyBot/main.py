from datetime import datetime
from typing import Optional, List, Dict

import discord
from discord import Role, Guild, Color
from discord.ext import commands
from discord.ext.commands import Bot, Context, CommandNotFound

from PyBot import embed_helper
from PyBot import str_helper
from slapp_py.slapipes import initialise_slapp, query_slapp
from slapp_py.strings import team_to_string, teams_to_string, best_team_player_div_string, div_to_string, \
    escape_characters, truncate_source
from tokens import BOT_TOKEN, CLIENT_ID, OWNER_ID

COMMAND_PREFIX = '~'

if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.members = True  # Subscribe to the privileged members intent for roles.
    intents.presences = False
    intents.typing = False
    bot: Bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, owner_id=OWNER_ID)

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
        name='Slapp',
        description="Query the slapp for a Splatoon player, team, tag, or other information",
        brief="Splatoon player and team lookup",
        aliases=['slapp', 'splattag'],
        help=f'{COMMAND_PREFIX}slapp <query>',
        pass_ctx=True)
    async def slapp(ctx: Context, *query):
        query: str = ' '.join(query)
        print('slapp called with query ' + query)
        now = datetime.utcnow()

        success, response = await query_slapp(query)
        if success:
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

                    # Transform names by adding a backslash to any underscores or stars.
                    if names:
                        names = list(map(lambda n: escape_characters(n), names))

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
                    sources = p["Sources"] if "Sources" in p else ['']
                    sources = ", ".join(list(map(lambda source: truncate_source(source), sources)))
                    info = f'{other_names}Plays for {team_to_string(current_team)}{old_teams}\n{twitter} ' \
                           f'_{sources}_'

                    top500 = "👑 " if "Top500" in p and p["Top500"] else ""
                    builder.add_field(name=str_helper.truncate(top500 + names[0], 1000, ""),
                                      value=str_helper.truncate(info, 1000, "…_"),
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
                            name = escape_characters(p["Names"][0]) if "Names" in p else '(Unknown player)'
                            player_strings += \
                                f'{name} {("(Most recent)" if in_team else "(Ex)" if in_team is False else "")}'
                            player_strings += separator

                    player_strings = player_strings[0:-len(separator)]
                    div_phrase = best_team_player_div_string(t, players, additional_teams)
                    sources = t["Sources"] if "Sources" in t else ['']
                    sources = ", ".join(list(map(lambda source: truncate_source(source), sources)))
                    info = f'{div_to_string(t["Div"])}. {div_phrase} Players: {player_strings}\n' \
                           f'_{sources}_'

                    builder.add_field(name=str_helper.truncate(team_to_string(t), 1000, ""),
                                      value=str_helper.truncate(info, 1000, "…_"),
                                      inline=False)

            builder.set_footer(
                text=f"Fetched in {int((datetime.utcnow() - now).microseconds / 1000)} milliseconds. " +
                     ('Only the first 9 results are shown for players and teams.' if show_limited else ''),
                icon_url="https://media.discordapp.net/attachments/471361750986522647/758104388824072253/icon.png")

            try:
                await ctx.send(embed=builder)
            except Exception as e:
                await ctx.send(content=f'Too many results, sorry 😔 ({e.__str__()})')


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
        await bot.change_presence(activity=discord.Game(name="with Slate"))


    initialise_slapp()
    bot.run(BOT_TOKEN)
