import discord
import time as t
from discord.ext import commands
import asyncio
import collections
import re
import datetime

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

        vote_message = f'Day {Config.day_number + 1} votes will be displayed here. ' \
                       f'Required votes to eliminate a player: {len(Config.signup_list) // 2 + 1}'

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
        
        # Collect roles
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        if alive_role is None:
            alive_role = await ctx.guild.create_role(name="Alive")

        dead_role = discord.utils.get(ctx.guild.roles, name="Dead")
        if dead_role is None:
            dead_role = await ctx.guild.create_role(name="Dead")

        spec_role = discord.utils.get(ctx.guild.roles, name="Spectator")
        if spec_role is None:
            spec_role = await ctx.guild.create_role(name="Spectator")

        spoiled_role = discord.utils.get(ctx.guild.roles, name="Spoilers")
        if spoiled_role is None:
            spoiled_role = await ctx.guild.create_role(name="Spoilers")

        # Adjust channel permissions to end game state.
        game_category = Config.game_channel.category
        game_guild = Config.game_channel.guild
        game_category.overwrites.clear() # set_permissions(game_category, overwrite=None)

        await game_category.set_permissions(game_guild.default_role, view_channel=True, send_messages=False)

        pattern = r"\d+-.*fallout.*"
        for channel in game_category.channels:
            await channel.edit(sync_permissions=True)
            if re.match(pattern, channel.name):
                print("MISSION SUCCESS - Fallout matched")
                await channel.set_permissions(game_guild.default_role, send_messages=True)
                await channel.send(f"{alive_role.mention} {dead_role.mention} the game has ended"
                                   f" and all channels have now been locked!\n"
                                   f"You may discuss the results here!\n"
                                   f"Thank you for playing and we hope you had fun!")

        # Clear all roles:
        for member in ctx.guild.members:
            if alive_role in member.roles:
                await member.remove_roles(alive_role)
            if dead_role in member.roles:
                await member.remove_roles(dead_role)
            if spec_role in member.roles:
                await member.remove_roles(spec_role)
            if spoiled_role in member.roles:
                await member.remove_roles(spoiled_role)

        # Reset all config values
        ####
        Config.signups_open = False  # Pregame
        Config.vote_channel = None
        Config.game_channel = None
        Config.global_day_length = 1
        Config.day_end_time = 1

        Config.day_end_task_object = None

        # Game Status
        Config.day_number = 0
        Config.signup_list = []  # Pre & Mid
        Config.vote_count_number = 1
        Config.votes = collections.OrderedDict()
        Config.prev_vote = None
        Config.current_vote = None  # Unused atm
        Config.live_players = []
        Config.vote_since_last_count = 0
        # Config.start_time = datetime.now()  # Unused atm

        Config.abstained_players = []

        # Post count collection
        Config.post_counts = collections.defaultdict(lambda: collections.defaultdict(int))

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
        # await self.bot.kill(ctx, member)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changevotethread(self, ctx, new_vote_channel: discord.TextChannel):
        Config.vote_channel = new_vote_channel
        await ctx.send(f"The vote channel is now {Config.vote_channel}")
        await Config.vote_channel.send("This is now the vote channel")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changegamethread(self, ctx, new_game_channel: discord.TextChannel):
        Config.game_channel = new_game_channel
        await ctx.send(f"The game channel is now {Config.game_channel}")
        await Config.game_channel.send("This is now the game channel")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gamesetup(self, ctx, game_name):

        # Catch roles
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        dead_role = discord.utils.get(ctx.guild.roles, name="Dead")
        spec_role = discord.utils.get(ctx.guild.roles, name="Spectator")
        spoil_role = discord.utils.get(ctx.guild.roles, name="Spoilers")

        # Initiate title segments
        title_start = "GAME "
        current_game_number = None
        current_position_level = None
        title_break = ": "
        PERMISSION_DECREMENT = 1
        # PERMISSION_DECREMENT = .0000001

        # Find game number and prepare to rearrange categories
        list_of_categories_to_move = []
        guild_categories = ctx.guild.categories
        for guild_category in guild_categories:
            print(f"This is category name: {guild_category.name}")
            print(f"This is category position: {guild_category.position}")
            game_title = re.match(r"(?i)game\s(\d+)", guild_category.name)
            if game_title and current_game_number is None:
                game_number = game_title.group(1)
                current_game_number = str(int(game_number) + 1)
                current_position_level = int(guild_category.position - 1)
                # last_game_new_pos = guild_category.position + 1
                # print(f"This is last_game_new_pos: {last_game_new_pos}")
                list_of_categories_to_move.append(guild_category)
                print("MISSION SUCCESS!")
                print(f"MOVING TO BUMP LIST!")
                print(f"This is current_game_number: {current_game_number}")
                print(f"This is current_position_level: {current_position_level}")
                print(f"This is guild_category.position: {guild_category.position}")
            elif current_game_number is not None:
                print(f"MOVING TO BUMP LIST!")
                list_of_categories_to_move.append(guild_category)
            print("")

        # Create category
        category_name = title_start + current_game_number + title_break + game_name
        category = await ctx.guild.create_category(category_name, position=int(current_position_level))
        await category.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        list_of_categories_to_move.append(category)

        for guild_category in list_of_categories_to_move:
            await guild_category.edit(position=(int(guild_category.position + 1)))

        # Create channels
        channel_break = "-"
        # Main game channel.  Everyone can view, nobody can speak to start.
        channel_name = current_game_number + channel_break + "game-chat"
        game_channel = await category.create_text_channel(channel_name)
        await game_channel.set_permissions(ctx.guild.default_role, view_channel=True, send_messages=False)
        # await game_channel.set_permissions(alive_role, send_messages=True)
        await game_channel.set_permissions(dead_role, send_messages=False)

        # Playerlist channel - Everyone views, nobody speaks.
        channel_name = current_game_number + channel_break + "playerlist"
        playerlist_channel = await category.create_text_channel(channel_name)
        await playerlist_channel.set_permissions(ctx.guild.default_role, view_channel=True, send_messages=False)

        # Voting channel - Everyone views, nobody speaks.
        channel_name = current_game_number + channel_break + "vote-count"
        vote_channel = await category.create_text_channel(channel_name)
        await vote_channel.set_permissions(ctx.guild.default_role, view_channel=True, send_messages=False)

        # Scum channel. Only specific players can use/view.  Only spoilers can view.
        channel_name = current_game_number + channel_break + "mafia-chat"
        mafia_channel = await category.create_text_channel(channel_name)
        await mafia_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        await mafia_channel.set_permissions(spoil_role, view_channel=True, send_messages=False)

        # Spec chat - only spectators can see.
        channel_name = current_game_number + channel_break + "spec-chat"
        spec_channel = await category.create_text_channel(channel_name)
        await spec_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        await spec_channel.set_permissions(spec_role, view_channel=True, send_messages=False)

        # Mod thread - only spoiled can see.
        channel_name = current_game_number + channel_break + "mod-thread"
        mod_channel = await category.create_text_channel(channel_name)
        await mod_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        await mod_channel.set_permissions(spoil_role, view_channel=True, send_messages=False)

        # Spoiled chat - only spoiled can see.
        channel_name = current_game_number + channel_break + "spoiled-spec"
        spoiled_channel = await category.create_text_channel(channel_name)
        await spoiled_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        await spoiled_channel.set_permissions(spoil_role, view_channel=True, send_messages=False)

        # Fallout chat - nobody can see until %endgame.
        channel_name = current_game_number + channel_break + "fallout"
        fallout_channel = await category.create_text_channel(channel_name)
        await fallout_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changeday(self, ctx, day: int):
        Config.day_number = day
        await ctx.send(f"The new day is now {Config.day_number}")

    # BUG TESTING COMMAND **ONLY**
    """@commands.command()
    @commands.has_permissions(administrator=True)
    async def clearcat(self, ctx, entered_channel: discord.TextChannel):
        category = entered_channel.category
        for channel in category.channels:
            await channel.delete()
        await category.delete()
        await ctx.send(f"The category containing {entered_channel} and all internal channels have been deleted!")"""

    # BUG TESTING COMMAND **ONLY**
    """@commands.command()
    @commands.has_permissions(administrator=True)
    async def catpos(self, ctx):
        for category in ctx.guild.categories:
            print(f"This is category.name: {category.name}")
            print(f"This is category.position: {category.position}")
            print(f"---")
        print("\n")"""


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))

