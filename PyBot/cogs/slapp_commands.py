"""Slapp commands cog."""
import traceback
from collections import namedtuple, deque
from typing import Optional, List, Tuple, Dict, Deque

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context

from operator import itemgetter
from PyBot.constants.bot_constants import COMMAND_PREFIX
from PyBot.constants.emojis import TROPHY, CROWN
from core_classes.builtins import UNKNOWN_PLAYER
from core_classes.player import Player
from core_classes.skill import Skill
from helpers.str_helper import equals_ignore_case, truncate
from slapp_py.slapipes import query_slapp, process_slapp, slapp_describe
from slapp_py.slapp_response_object import SlappResponseObject
from vlee.battlefyToolkit import tournament_ids

SlappQueueItem = namedtuple('SlappQueueItem', ('Context', 'str'))
slapp_ctx_queue: Deque[SlappQueueItem] = deque()
module_autoseed_list: Optional[Dict[str, List[dict]]] = dict()
module_predict_team_1: Optional[dict] = None


class SlappCommands(commands.Cog):
    """A grouping of Slapp-related commands."""

    @commands.command(
        name='autoseed',
        description="Auto seed the teams that have signed up to the tourney",
        help=f'{COMMAND_PREFIX}autoseed <tourney_id>',
        pass_ctx=True)
    async def autoseed(self, ctx: Context, tourney_id: Optional[str]):
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

    @commands.command(
        name='verify',
        description="Verify a signed-up team.",
        help=f'{COMMAND_PREFIX}verify <team_slug>',
        pass_ctx=True)
    async def verify(self, ctx: Context, team_slug_or_confirmation: Optional[str], tourney_id: Optional[str]):
        if not tourney_id:
            tourney_id = self.get_latest_ipl()

        from misc.download_from_battlefy_result import download_from_battlefy
        tournament = list(download_from_battlefy(tourney_id))
        if isinstance(tournament, list) and len(tournament) == 1:
            tournament = tournament[0]

        if len(tournament) == 0:
            await ctx.send(f"I couldn't download the latest tournament data 😔 (id: {tourney_id})")
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

    @commands.command(
        name='Slapp',
        description="Query the slapp for a Splatoon player, team, tag, or other information",
        brief="Splatoon player and team lookup",
        aliases=['slapp', 'splattag', 'search'],
        help=f'{COMMAND_PREFIX}search <mode_to_translate>',
        pass_ctx=True)
    async def slapp(self, ctx: Context, *, query):
        print('slapp called with mode_to_translate ' + query)
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'slapp'))
        await query_slapp(query)

    @commands.command(
        name='Slapp (Full description)',
        description="Fully describe the given id.",
        brief="Splatoon player or team full description",
        aliases=['full', 'describe'],
        help=f'{COMMAND_PREFIX}full <slapp_id>',
        pass_ctx=True)
    async def full(self, ctx: Context, slapp_id: str):
        print('full called with mode_to_translate ' + slapp_id)
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'full'))
        await slapp_describe(slapp_id)

    @commands.command(
        name='Fight',
        description="Get a match rating and predict the winner between two teams or two players.",
        brief="Two Splatoon teams/players to fight and rate winner",
        aliases=['fight', 'predict'],
        help=f'{COMMAND_PREFIX}predict <slapp_id_1> <slapp_id_2>',
        pass_ctx=True)
    async def predict(self, ctx: Context, slapp_id_team_1: str, slapp_id_team_2: str):
        print(f'predict called with teams {slapp_id_team_1=} {slapp_id_team_2=}')
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'predict_1'))
        await slapp_describe(slapp_id_team_1)
        slapp_ctx_queue.append(SlappQueueItem(ctx, 'predict_2'))
        await slapp_describe(slapp_id_team_2)
        # This comes back in the receive_slapp_response -> handle_predict

    @staticmethod
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

    @staticmethod
    async def handle_autoseed(ctx: Optional[Context], description: str, response: Optional[dict]):
        global module_autoseed_list

        if description.startswith("autoseed_start"):
            module_autoseed_list.clear()
        elif not description.startswith("autoseed_end"):
            team_name = description.rpartition(':')[2]  # take the right side of the colon
            if module_autoseed_list.get(team_name):
                module_autoseed_list[team_name].append(response)
            else:
                module_autoseed_list[team_name] = [response]
        else:
            # End, do the thing
            message = ''

            # Team name, list of players, clout, confidence, emoji str
            teams_by_clout: List[Tuple[str, List[str], int, int, str]] = []

            if module_autoseed_list:
                for team_name in module_autoseed_list:
                    team_players = []
                    team_awards = []
                    for player_response in module_autoseed_list[team_name]:
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

    @staticmethod
    async def handle_predict(ctx: Context, description: str, response: dict):
        global module_predict_team_1
        is_part_2 = description == "predict_2"
        if not is_part_2:
            module_predict_team_1 = response
        else:
            response_1 = SlappResponseObject(module_predict_team_1)
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
                team_2_skills = response_2.get_team_skills(team_2.guid).values()
                if team_2_skills:
                    (_, _), (max_clout_2, max_conf_2) = Skill.team_clout(team_2_skills)
                    message += Skill.make_message_clout(max_clout_2, max_conf_2, truncate(team_2.name.value, 25, "…")) + '\n'

                if team_1_skills and team_2_skills:
                    if max_conf_1 > 2 and max_conf_2 > 2:
                        favouring_team_1, favouring_team_2 = Skill.calculate_quality_of_game_teams(team_1_skills, team_2_skills)
                        if favouring_team_1 != favouring_team_2:
                            message += "Hmm, it'll depend on who's playing, but... "
                        message += Skill.make_message_fairness(favouring_team_1) + '\n'
                        favouring_team_1, favouring_team_2 = Skill.calculate_win_probability(team_1_skills, team_2_skills)
                        message += Skill.make_message_win(favouring_team_1, favouring_team_2, team_1, team_2) + '\n'

                else:
                    message += "Hmm, I don't have any skill information to make a good guess on the outcome.\n"

            elif matching_mode == 'players':
                p1 = response_1.matched_players[0]
                message += Skill.make_message_clout(p1.skill.clout, p1.skill.confidence, truncate(p1.name.value, 25, "…")) + '\n'
                p2 = response_2.matched_players[0]
                message += Skill.make_message_clout(p2.skill.clout, p2.skill.confidence, truncate(p2.name.value, 25, "…")) + '\n'
                quality = Skill.calculate_quality_of_game_players(p1.skill, p2.skill)
                message += Skill.make_message_fairness(quality) + '\n'
            else:
                message += f"WTF IS {matching_mode}?!"

            await ctx.send(message)

    @staticmethod
    async def receive_slapp_response(success_message: str, response: dict):
        if len(slapp_ctx_queue) == 0:
            print(f"receive_slapp_response but queue is empty. Discarding result: {success_message=}, {response=}")
        else:
            ctx, description = slapp_ctx_queue.popleft()
            if description.startswith('predict_'):
                if success_message != "OK":
                    await SlappCommands.send_slapp(
                        ctx=ctx,
                        success_message=success_message,
                        response=response)
                else:
                    await SlappCommands.handle_predict(ctx, description, response)
            elif description.startswith('autoseed'):
                if success_message != "OK":
                    await SlappCommands.send_slapp(
                        ctx=ctx,
                        success_message=success_message,
                        response=response)

                # If the start, send on and read again.
                if description.startswith("autoseed_start"):
                    await SlappCommands.handle_autoseed(None, description, None)
                    ctx, description = slapp_ctx_queue.popleft()

                await SlappCommands.handle_autoseed(ctx, description, response)

                # Check if last.
                ctx, description = slapp_ctx_queue[0]
                if description.startswith("autoseed_end"):
                    await SlappCommands.handle_autoseed(ctx, description, None)
                    slapp_ctx_queue.popleft()

            else:
                await SlappCommands.send_slapp(
                    ctx=ctx,
                    success_message=success_message,
                    response=response)

    @staticmethod
    def get_latest_ipl():
        return tournament_ids('inkling-performance-labs')[0]
