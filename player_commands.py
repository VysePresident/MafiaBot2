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
                await ctx.send(f'Thank you for signing up, {ctx.author.name}!')
            else:
                await ctx.send(f'You have already signed up, {ctx.author.name}!')
        else:
            await ctx.send('Sign ups are currently closed.')

    @commands.command()
    async def unsignup(self, ctx):
        # DEBUG LOG
        print(f"Command unsignup: Author: {ctx.author.name}")

        if ctx.author in Config.signup_list:
            Config.signup_list.remove(ctx.author)
            await ctx.send(f'You have been removed from the sign up list, {ctx.author.name}!')
        else:
            await ctx.send(f'You are not on the sign up list, {ctx.author.name}!')

    @commands.command()
    async def signuplist(self, ctx):
        # DEBUG LOG
        print(f"Command signuplist: Author: {ctx.author.name}")
        if not Config.signup_list:
            await ctx.send('No one has signed up yet.')
        else:
            signups = "\n".join([user.name for user in Config.signup_list])
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

        if ctx.author in Config.votes:
            # print("Gate Change Vote")
            Config.prev_vote = (ctx.author, Config.votes.pop(ctx.author))
        else:
            # print("Gate Wasn't Voting")
            Config.prev_vote = (ctx.author, "not voting")
        Config.votes[ctx.author] = voted

        # DEBUG LOGS
        """print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
        if ctx.author in Config.votes:
            # DEBUG
            print(f'RESULT: This is prev_vote[0]: {Config.prev_vote[0].name} and prev_vote[1]: {Config.prev_vote[1].name}')
        else:
            # DEBUG
            print(f'RESULT: This is prev_vote[0]: {Config.prev_vote[0].name} and prev_vote[1]: {Config.prev_vote[1]}')"""

        # DEBUG LOGS:
        print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
        print(f'Finishing vote - prev_vote: prev_vote[0]: {Config.prev_vote[0]} and prev_vote[1]: {Config.prev_vote[1]}')
        await ctx.send(f"{ctx.author.name} has voted for {Config.votes[ctx.author].name}.")  # TEST
        await self.bot.votecount(self.bot, ctx=ctx, in_channel_request=False, vote_change=voted)
        return

    @commands.command()
    async def unvote(self, ctx):
        # DEBUG LOG
        print(f'command unvote: ctx.author: {ctx.author.name} has unvoted')

        if ctx.channel != Config.game_channel:
            await ctx.send("You can only vote in the game chat.")
            return
        if ctx.author in Config.votes:
            Config.prev_vote = (ctx.author, Config.votes.pop(ctx.author))  # TEST
            await ctx.send(f"{ctx.author.name} has unvoted.")
            await self.bot.votecount(self.bot, ctx=ctx, in_channel_request=False,
                                                             vote_change=Config.prev_vote[1], is_unvote=True)
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
                alive_players.append(member.name)
            elif discord.utils.get(member.roles, name="Dead"):
                dead_players.append(member.name)
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
