import discord
from discord.ext import commands
import time as t
import asyncio
import collections
from config import Config

class MafiaBot(commands.Bot):
    def __init__(self, command_prefix, token):
        super().__init__(
            command_prefix=command_prefix,
            intents=discord.Intents.all()
        )
        self.token = token

    @commands.command()
    async def votecount(self, ctx, in_channel_request=True, vote_change=None, is_unvote=False):
        # DEBUG LOG
        print(f'Command votecount: Author: {ctx.author.name} in_channel_request: {in_channel_request} '
              f'vote_change: {vote_change} is_unvote: {is_unvote}')  # DEBUG

        if in_channel_request is not True and in_channel_request is not False:
            await ctx.send(
                "You specified the wrong number of parameters.")
            return
        count = collections.OrderedDict()
        votes_required = len(Config.signup_list) // 2 + 1

        # Construct vote count for each player voted.  Should automatically be in order.
        for voter, voted in Config.votes.items():
            if voted in count:
                count[voted].append(voter)
            else:
                count[voted] = []
                count[voted].append(voter)

        # Construct message string
        game_thread_message = ''
        votecount_message = f"**Vote Count {Config.day_number}.{Config.vote_count_number} - **{ctx.message.jump_url}\n\n"
        endDay = False
        for voted, voters in count.items():
            remaining_votes = votes_required - len(voters)  # The number of votes remaining for a lynch
            lynch_status = '**LYNCH**' if remaining_votes == 0 else f"L-{remaining_votes}"
            voters_str = ', '.join(
                [voter.name if voter is not Config.prev_vote[0] else f'**{voter.name}**' for voter in voters])
            votecount_message += f"{voted.name}[{lynch_status}] - {voters_str}\n"
            if lynch_status == '**LYNCH**':
                endDay = True
            # Game thread lynch status message
            if voted is vote_change:
                game_thread_message = f"{voted.name} is {lynch_status}"
        not_voting = [player for player in Config.signup_list if player not in Config.votes.keys()]
        if len(not_voting) > 0:
            votecount_message += f"\nNot Voting - {', '.join([player.name if player is not Config.prev_vote[0] else f'**{player.name}**' for player in not_voting])}"
        else:
            votecount_message += f"\nNot Voting - (None)"
        if isinstance(Config.prev_vote[1], str):
            votecount_message += f"\n\n__Change__: *{Config.prev_vote[0].name} switched from {Config.prev_vote[1]} to {voted.name}*"
        elif is_unvote:
            votecount_message += f"\n\n__Change__: *{Config.prev_vote[0].name} has unvoted {Config.prev_vote[1]}*"
        else:
            votecount_message += f"\n\n__Change__: *{Config.prev_vote[0].name} switched from {Config.prev_vote[1].name} to {voted.name}*"
        votecount_message += f"\n\n*With {len(Config.signup_list)} alive, it takes {votes_required} to lynch.*"
        votecount_message += "\n" + "-" * 40

        # End of Day message
        if endDay:
            print(f'endDay activated')  # DEBUG LOG

            await self.kill(self, ctx, voted)
            votecount_message += f"\n\n**{voted.name} has been removed from the game**"
            votecount_message += f"\n\n**Night {Config.day_number + 1} begins now!**"
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            await Config.game_channel.set_permissions(alive_role, send_messages=False)
            await Config.game_channel.send("The day has ended with a lynch.")
        if in_channel_request:
            await ctx.send(votecount_message)
        else:
            votecount_sent = await Config.vote_channel.send(votecount_message)
        # Another in-thread lynch status alternative message
        if vote_change is not None and vote_change not in count:
            game_thread_message = f"{vote_change.name} has zero votes"
        # Test lynch status message
        if votecount_sent:
            game_thread_message += f": {votecount_sent.jump_url}"
        await Config.game_channel.send(game_thread_message)

        if in_channel_request:
            Config.vote_count_number += 1
        return

    @commands.command()
    # @commands.has_permissions(Administrator=True)
    async def kill(self, ctx, member: discord.Member):
        print(f'Command kill: Author: {ctx.author.name} Target: {member.name}')  # DEBUG LOG

        if member.name in Config.live_players:
            Config.live_players.remove(member.name)
            Config.signup_list.remove(member)
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            dead_role = discord.utils.get(ctx.guild.roles, name="Dead")
            if dead_role is None:
                dead_role = await ctx.guild.create_role(name="Dead")
            if alive_role in member.roles:
                await member.remove_roles(alive_role)
            if dead_role not in member.roles:
                await member.add_roles(dead_role)
            await ctx.send(f"{member.name} has been removed from the game.")
        else:
            await ctx.send(f"{member.name} is not in the game or already removed.")

# ROLE RELATED COMMAND
"""@bot.command()
async def roleinfo(ctx, *, role: str):
    role = role.lower()
    if role not in roles:
        await ctx.send('That role cannot be found. Try googling "(rolename) mafiascum wiki".')
    else:
        role_info = roles[role]
        await ctx.send(f'**{role.capitalize()}**\n{role_info["description"]}\n\n**Alignment:** {role_info["alignment"]}\n\n**Special Abilities:** {role_info["special_abilities"]}')
"""

# ROLE RELATED COMMAND
"""
@bot.command()
async def rolelist(ctx):
    formatted_roles = [role.capitalize() for role in roles]
    await ctx.send("**Displaying normal roles:**\n" + '\n'.join(formatted_roles))
"""

# Command is not used yet.  Review later.
"""
async def periodic_votecount_check():
    while True:
        if Config.vote_since_last_count >= 10:
            # Reset the counter
            Config.vote_since_last_count = 0
            # Call the votecount method (assumes it takes no arguments, modify as needed)
            await votecount()
        # Sleep for 10 seconds before checking again
        await asyncio.sleep(10)
"""

# bot.loop.create_task(periodic_votecount_check())
