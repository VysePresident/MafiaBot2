import discord
from discord.ext import commands
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
    async def votecount(self, ctx, voter, prev_vote, current_vote):
        # DEBUG LOG
        print(f'Command votecount: Author: {ctx.author.name} voter: {voter.name} prev_vote: {prev_vote} '
              f'current_vote: {current_vote}')

        # Construct ordered vote count for each player voted.
        count = self.constructVoteCounts()
        # Create and send votecount message
        votecount_strings, check_if_end_day, lynch_status = self.createVoteCountMessage(count, voter, prev_vote, current_vote)

        votecount_message = f"**Vote Count {Config.day_number}.{Config.vote_count_number} - **{ctx.message.jump_url}\n\n"
        votecount_message += votecount_strings + "\n"
        votecount_message += self.findNotVoting(voter) + "\n"
        votecount_message += self.findChangedVote(voter, prev_vote, current_vote) + "\n"
        votecount_message += self.playersNeededToLynch()
        votecount_message += Config.LINE_BREAK + "\n"
        if check_if_end_day:
            print("LOG 1: It is endDay my dudes")
            # votecount_message += f"**{current_vote.name} has been removed from the game**\n\n"
            votecount_message += f"**{current_vote.display_name} has been removed from the game**\n\n"
            votecount_message += f"**Night {Config.day_number + 1} begins now!**\n\n"
        votecount_sent = await Config.vote_channel.send(votecount_message)

        # Create and send gamechat message
        vote_change = prev_vote if current_vote == Config.NOT_VOTING else current_vote  # lynch_status is None
        game_thread_message = self.returnLynchStatus(ctx, vote_change, lynch_status)
        game_thread_message += f": {votecount_sent.jump_url}"
        await Config.game_channel.send(game_thread_message)

        if check_if_end_day:
            print("LOG 2: It is endDay my dudes")
            await Config.game_channel.send(f"{Config.LINE_BREAK}\nThe day has ended with a lynch.")
            await self.kill(self, ctx, current_vote)
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            await Config.game_channel.set_permissions(alive_role, send_messages=False)

        Config.vote_count_number += 1

    def createVoteCountMessage(self, count, changed_voter, prev_vote, current_vote):
        votes_required = len(Config.signup_list) // 2 + 1

        votecount_chains = ''
        check_if_end_day = False
        changed_lynch_status = None
        changed_vote_target = None
        if current_vote == Config.NOT_VOTING:
            changed_vote_target = prev_vote
        else:
            changed_vote_target = current_vote

        for voted, voters in count.items():
            remaining_votes = votes_required - len(voters)  # The number of votes remaining for a lynch
            lynch_status = '**LYNCH**' if remaining_votes == 0 else f"L-{remaining_votes}"
            voters_str = ', '.join(
                [voter.display_name if voter is not changed_voter else f'**{voter.display_name}**' for voter in voters])
            votecount_chains += f"{voted.display_name}[{lynch_status}] - {voters_str}\n"
            if lynch_status == '**LYNCH**':
                check_if_end_day = True
            # Lynch status of voted target
            # if voted is current_vote:
            if voted is changed_vote_target:
                changed_lynch_status = lynch_status

        return votecount_chains, check_if_end_day, changed_lynch_status

    def findNotVoting(self, changed_voter):
        not_voting_message = ''
        not_voting = [player for player in Config.signup_list if player not in Config.votes.keys()]
        if len(not_voting) > 0:
            not_voting_message += f"Not Voting - "
            # not_voting_message += ', '.join([player.name if player is not changed_voter else f'**{player.name}**' for player in not_voting])
            not_voting_message += ', '.join([player.display_name if player is not changed_voter else f'**{player.display_name}**' for player in not_voting])
        else:
            not_voting_message += f"Not Voting - (None)"
        not_voting_message += "\n"
        return not_voting_message

    def returnLynchStatus(self, ctx, voted, lynch_status):
        if lynch_status == "**LYNCH**":
            # return f'{voted.name} has been lynched!'
            return f'{voted.display_name} has been lynched!'
        elif lynch_status is None:
            # return f'{voted.name} has zero votes'
            return f'{voted.display_name} has zero votes'
        else:
            # return f'{voted.name} is {lynch_status}'
            return f'{voted.display_name} is {lynch_status}'

    def findChangedVote(self, voter, prev_vote, current_vote):
        changed_vote_message = '__CHANGE__: '
        if current_vote == Config.NOT_VOTING:
            # changed_vote_message += f'{voter.name} has unvoted {prev_vote.name}'
            changed_vote_message += f'{voter.display_name} has unvoted {prev_vote.display_name}'
        elif prev_vote == Config.NOT_VOTING:
            # changed_vote_message += f'{voter.name} has switched from {Config.NOT_VOTING} to voting {current_vote.name}'
            changed_vote_message += f'{voter.display_name} has switched from {Config.NOT_VOTING} to voting {current_vote.display_name}'
        else:
            # changed_vote_message += f'{voter.name} has switched their vote from {prev_vote.name} to {current_vote.name}'
            changed_vote_message += f'{voter.display_name} has switched their vote from {prev_vote.display_name} to {current_vote.display_name}'
        changed_vote_message += "\n"
        return changed_vote_message

    def playersNeededToLynch(self):
        votes_required = len(Config.signup_list) // 2 + 1
        return f"*With {len(Config.signup_list)} alive, it takes {votes_required} to lynch.*\n"

    def constructVoteCounts(self):
        count = collections.OrderedDict()
        for voter, voted in Config.votes.items():
            if voted in count:
                count[voted].append(voter)
            else:
                count[voted] = []
                count[voted].append(voter)
        return count

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
                print(f"!!!KILL SANITY CHECK!!!: {member.name} should receive DEAD role")
                # await member.add_roles(dead_role)
            # await ctx.send(f"{member.name} has been removed from the game. NOTE: Dead role must be added manually for now")
            await ctx.send(f"{member.display_name} has been removed from the game. NOTE: Dead role must be added manually for now")
        else:
            # await ctx.send(f"{member.name} is not in the game or already removed.")
            await ctx.send(f"{member.display_name} is not in the game or already removed.")


# ROLE RELATED COMMAND
"""@bot.command()
async def roleInfo(ctx, *, role: str):
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
