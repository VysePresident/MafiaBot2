import discord
import time as t
from discord.ext import commands
from config import Config


class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def signup(self, ctx):
        print("This is signups_open in signup(): " + str(Config.signups_open))
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
        if ctx.author in Config.signup_list:
            Config.signup_list.remove(ctx.author)
            await ctx.send(f'You have been removed from the sign up list, {ctx.author.name}!')
        else:
            await ctx.send(f'You are not on the sign up list, {ctx.author.name}!')

    @commands.command()
    async def signuplist(self, ctx):
        if not Config.signup_list:
            await ctx.send('No one has signed up yet.')
        else:
            signups = "\n".join([user.name for user in Config.signup_list])
            await ctx.send(f'The current signups are:\n{signups}')

    @commands.command()
    async def vote(self, ctx, voted: discord.Member):
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

        await ctx.send(f"{ctx.author.name} has voted for {Config.votes[ctx.author].name}.")  # TEST
        await self.bot.get_command("votecount").callback(ctx=ctx, in_channel_request=False, vote_change=voted)
        return

    @commands.command()
    async def unvote(self, ctx):
        if ctx.channel != Config.game_channel:
            await ctx.send("You can only vote in the game chat.")
            return
        if ctx.author in Config.votes:
            Config.prev_vote = (ctx.author, Config.votes.pop(ctx.author))  # TEST
            await ctx.send(f"{ctx.author.name} has unvoted.")
            await self.bot.get_command("votecount").callback(ctx=ctx, in_channel_request=False,
                                                        vote_change=Config.prev_vote[1], is_unvote=True)
        else:
            await ctx.send("You haven't voted yet.")
        return

    @commands.command()
    async def time(self, ctx):
        if Config.day_end_time is None:
            await ctx.send("The game hasn't started yet.")
        else:
            time_remaining = Config.day_end_time - t.time()
            if time_remaining <= 0:
                await ctx.send("The day has ended.")
            else:
                hours, rem = divmod(time_remaining, 3600)
                minutes, seconds = divmod(rem, 60)
                await ctx.send(
                    f"Time remaining: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")

    @commands.command()
    async def playerlist(self, ctx):
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
        await ctx.send(f"Alive players:\n{' '.join(alive_players)}\n\nDead players:\n{' '.join(dead_players)}")

def setup(bot):
    bot.add_cog(PlayerCommands(bot))
