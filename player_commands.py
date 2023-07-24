import discord
import time as t
from discord.ext import commands
from config import Config


class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def signup(self, ctx):
        # DEBUG LOG
        print(f"Command signup: Author: {ctx.author.name}")

        if Config.signups_open:
            if ctx.author not in Config.signup_list:
                Config.signup_list.append(ctx.author)
                # await ctx.send(f'Thank you for signing up, {ctx.author.name}!')
                await ctx.send(f'Thank you for signing up, {ctx.author.display_name}!')
            else:
                # await ctx.send(f'You have already signed up, {ctx.author.name}!')
                await ctx.send(f'You have already signed up, {ctx.author.display_name}!')
        else:
            await ctx.send('Sign ups are currently closed.')

    @commands.command()
    async def unsignup(self, ctx):
        # DEBUG LOG
        print(f"Command unsignup: Author: {ctx.author.name}")

        if ctx.author in Config.signup_list:
            Config.signup_list.remove(ctx.author)
            # await ctx.send(f'You have been removed from the sign up list, {ctx.author.name}!')
            await ctx.send(f'You have been removed from the sign up list, {ctx.author.display_name}!')
        else:
            # await ctx.send(f'You are not on the sign up list, {ctx.author.name}!')
            await ctx.send(f'You are not on the sign up list, {ctx.author.display_name}!')

    @commands.command()
    async def signuplist(self, ctx):
        # DEBUG LOG
        print(f"Command signuplist: Author: {ctx.author.name}")
        if not Config.signup_list:
            await ctx.send('No one has signed up yet.')
        else:
            # signups = "\n".join([user.name for user in Config.signup_list])
            signups = "\n".join([user.display_name for user in Config.signup_list])
            await ctx.send(f'There are currently {len(Config.signup_list)} signups:\n\n{signups}')

    @commands.command()
    async def vote(self, ctx, voted: discord.Member):
        # DEBUG LOG
        print(f'command vote: ctx.author: {ctx.author.name} and voted: {voted.name}')

        if ctx.author not in Config.signup_list or voted not in Config.signup_list:
            await ctx.send("Either the voter or the voted player is not in the game.")
            return
        if ctx.author in Config.votes and Config.votes[ctx.author] == voted:
            await ctx.send("You've already voted for this player.")
            return
        if ctx.channel != Config.game_channel:
            await ctx.send("You can only vote in the game chat.")
            return

        voter = ctx.author
        prev_vote = ''
        current_vote = voted

        if ctx.author in Config.votes:
            # print("Gate Change Vote")
            prev_vote = Config.votes.pop(ctx.author)
        else:
            # print("Gate Wasn't Voting")
            prev_vote = Config.NOT_VOTING
        Config.votes[ctx.author] = voted

        # DEBUG LOGS:
        """if prev_vote != Config.NOT_VOTING and current_vote != Config.NOT_VOTING:
            print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
            print(f'Finishing vote - prev_vote: {prev_vote.name} current_vote: {current_vote.name} voter: {voter.name}')
        elif prev_vote == Config.NOT_VOTING:
            print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
            print(f'Finishing vote - prev_vote: {prev_vote} current_vote: {current_vote.name} voter: {voter.name}')
        else:
            print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
            print(f'Finishing vote - prev_vote: {prev_vote.name} current_vote: {current_vote} voter: {voter.name}')"""

        # await ctx.send(f"{ctx.author.name} has voted for {Config.votes[ctx.author].name}.")
        await ctx.send(f"{ctx.author.display_name} has voted for {Config.votes[ctx.author].display_name}.")
        await self.bot.votecount(self.bot, ctx, voter, prev_vote, current_vote)
        return

    @commands.command()
    async def unvote(self, ctx):
        # DEBUG LOG
        print(f'command unvote: ctx.author: {ctx.author.name} has unvoted')

        if ctx.channel != Config.game_channel:
            await ctx.send("You can only vote in the game chat.")
            return
        if ctx.author in Config.votes:
            prev_vote = Config.votes.pop(ctx.author)
            current_vote = Config.NOT_VOTING
            voter = ctx.author
            # await ctx.send(f"{ctx.author.name} has unvoted {prev_vote.name}.")
            await ctx.send(f"{ctx.author.display_name} has unvoted {prev_vote.display_name}.")
            await self.bot.votecount(self.bot, ctx, voter, prev_vote, current_vote)
        else:
            await ctx.send("You haven't voted yet.")
        return

    @commands.command()
    async def time(self, ctx):
        # DEBUG
        print(f'command time: ctx.author: {ctx.author.name} used %time')

        if Config.day_end_time is None:
            await ctx.send("The game hasn't started yet.")
        else:
            time_remaining = Config.day_end_time - t.time()
            if time_remaining <= 0:
                print(f'RESULT: The day has ended.')
                await ctx.send("The day has ended.")
            else:
                hours, rem = divmod(time_remaining, 3600)
                minutes, seconds = divmod(rem, 60)
                # DEBUG LOG
                print(f'RESULT of {ctx.author.name} using %time: '
                      f'Time remaining: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.')

                await ctx.send(
                    f"Time remaining: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")

    @commands.command()
    async def playerlist(self, ctx):
        # DEBUG
        print(f'command time: ctx.author: {ctx.author.name} used %playerlist')

        alive_players = []
        dead_players = []
        for member in ctx.guild.members:
            if discord.utils.get(member.roles, name="Alive"):
                # alive_players.append(member.name)
                alive_players.append(member.display_name)
            elif discord.utils.get(member.roles, name="Dead"):
                # dead_players.append(member.name)
                dead_players.append(member.display_name)
        if not alive_players:
            alive_players.append("No players alive.")
        if not dead_players:
            dead_players.append("No players dead.")
        playerlist_string = "\n\n__**Alive Players**__\n" + '\n'.join(alive_players) + '\n'
        playerlist_string += "\n__**Dead Players**__\n" + '\n'.join(dead_players)
        print(f"This is result of {ctx.author.name} using playerlist: {playerlist_string}")
        await ctx.send(f"{playerlist_string}")


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
