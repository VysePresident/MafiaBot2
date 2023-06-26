import discord
import time as t
from discord.ext import commands
import asyncio

from config import Config


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.config = config

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startsignup(self, ctx):
        # global signups_open, signup_list
        Config.signups_open = True
        print("This is signups_open in startsignup(): " + str(Config.signups_open))
        Config.signup_list.clear()
        await ctx.send('Sign ups are open! Sign up for the game by doing %signup')
        return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def forcesignup(self, ctx, user: discord.Member):
        print("This is signups_open in forcesignup(): " + str(Config.signups_open))
        if user not in Config.signup_list:
            Config.signup_list.append(user)
            await ctx.send(f'{user.name} has been signed up.')
        else:
            await ctx.send(f'{user.name} is already signed up.')
        return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def bugTest(self, ctx):
        print("This is signups_open in bugTest(): " + str(Config.signups_open))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unforcesignup(self, ctx, user: discord.Member):
        # global signups_open
        print("This is signups_open in unforcesignup(): " + str(Config.signups_open))
        if user in Config.signup_list:
            Config.signup_list.remove(user)
            await ctx.send(f'{user.name} has been removed from the signup list.')
        else:
            await ctx.send(f'{user.name} is not on the signup list.')
        return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startgame(self, ctx, game_channel_param: discord.TextChannel, vote_channel_param: discord.TextChannel,
                        day_length: int = 1):
        Config.global_day_length = day_length
        # Test Debugging
        print("This is signups_open in startgame(): " + str(Config.signups_open))
        if not Config.signups_open:
            await ctx.send('Signups are currently closed.')
            return
        if not Config.signup_list:
            await ctx.send('No one has signed up yet.')
            return
        Config.signups_open = False
        Config.game_channel = game_channel_param
        Config.vote_channel = vote_channel_param
        if Config.game_channel is None or Config.vote_channel is None:
            await ctx.send('One or both channels are incorrect.')
            return
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        if alive_role is None:
            alive_role = await ctx.guild.create_role(name="Alive")
        for user in Config.signup_list:
            member = ctx.guild.get_member(user.id)
            if member is not None:
                await member.add_roles(alive_role)
                Config.live_players.append(member.name)
        game_players = "\n".join([user.mention for user in Config.signup_list])
        await Config.game_channel.send(f'The game has started with the following players:\n{game_players}')

        vote_message = f'Day {Config.day_number + 1} votes will be displayed here. Required votes to eliminate a player: {len(Config.signup_list) // 2 + 1}'

        await Config.vote_channel.send(vote_message)

        await self.newday(ctx, day_length)
        return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def newday(self, ctx, day_length: int = 1):
        day_length = Config.global_day_length
        Config.day_number += 1
        Config.vote_count_number = 1
        Config.votes = {}
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        await Config.game_channel.set_permissions(alive_role, send_messages=True)

        votecount_message = f"**Vote Count {Config.day_number}.{Config.vote_count_number}**\n\nNo votes yet."
        votecount_message += "\n" + (40 * "-")
        await Config.vote_channel.send(votecount_message)

        await Config.game_channel.send(f"Day {Config.day_number} has begun. It will end in {day_length} days.")
        Config.day_end_time = t.time() + day_length * 24 * 60 * 60
        Config.day_end_task_object = self.bot.loop.create_task(self.end_day_after_delay(day_length))
        return

    async def end_day_after_delay(self, day_length):
        new_day_length = day_length * 24 * 60 * 60
        Config.day_end_time = t.time() + new_day_length
        try:
            await asyncio.sleep(new_day_length)
            alive_role = discord.utils.get(Config.game_channel.guild.roles, name="Alive")
            await Config.game_channel.set_permissions(alive_role, send_messages=False)
            await Config.game_channel.send("The day has ended due to time running out.")
            return
        except asyncio.CancelledError:
            print("We cancelled original day phase time limit!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def endgame(self, ctx):
        # current_day = 0  # Unnecessary code?
        Config.votes = {}
        Config.global_day_length = 1
        await ctx.send("The game has ended.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addplayer(self, ctx, new_player: discord.Member):
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        if new_player not in Config.signup_list:
            Config.signup_list.append(new_player)
            await new_player.add_roles(alive_role)
            Config.live_players.append(new_player.name)
            await ctx.send(f'{new_player.name} has been added to the game!')
        else:
            await ctx.send(f'{new_player.name} is already in the game!')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def swapplayer(self, ctx, existing_player: discord.Member, new_player: discord.Member):
        if existing_player in Config.signup_list:
            if new_player not in Config.signup_list:
                index = Config.signup_list.index(existing_player)
                Config.signup_list[index] = new_player
                if existing_player.name in Config.live_players:
                    Config.live_players.remove(existing_player.name)
                Config.live_players.remove(new_player.name)
                alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
                await existing_player.remove_roles(alive_role)
                await new_player.add_roles(alive_role)
                await ctx.send(f'{existing_player.name} has been replaced with {new_player.name}.')
            else:
                await ctx.send(f'{new_player.name} is already in the game.')
        else:
            await ctx.send(f'{existing_player.name} is not in the game.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changedaylength(self, ctx, *args):
        day_length_in_seconds = 0
        for arg in args:
            if arg[-1] == 'd':
                day_length_in_seconds += int(arg[:-1]) * 60 * 60 * 24
            elif arg[-1] == 'h':
                day_length_in_seconds += int(arg[:-1]) * 60 * 60
            elif arg[-1] == 'm':
                day_length_in_seconds += int(arg[:-1]) * 60
            else:
                await ctx.send(f'Invalid time format: {arg}. Will only accept one of these at end of cmd: "d/h/m".')
        Config.global_day_length = day_length_in_seconds / (24 * 60 * 60)
        Config.day_end_task_object.cancel()
        Config.day_end_task_object = self.bot.loop.create_task(self.end_day_after_delay(Config.global_day_length))

        new_day_length = Config.global_day_length * 24 * 60 * 60
        new_day_end_time = t.time() + new_day_length
        time_remaining = new_day_end_time - t.time()  # Config.day_end_time - t.time()
        if time_remaining <= 0:
            await ctx.send("The day has ended.")
        else:
            hours, rem = divmod(time_remaining, 3600)
            minutes, seconds = divmod(rem, 60)
            await ctx.send(
                f"Time remaining: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")

        # await ctx.send(f'The day length has been changed to {Config.global_day_length} days.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def modkill(self, ctx, member: discord.Member):
        await self.bot.kill(ctx, member)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
