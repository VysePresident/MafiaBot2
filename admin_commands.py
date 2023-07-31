"""
Author: Geo
Date: July 29th, 2023

This module is used for admin and dev bot commands.  Dev commands should all be commented out before the
bot goes live.  In the future, I would like to move those to their own module.
"""

import discord
import time as t
from discord.ext import commands
import asyncio
import collections
import re
from player import Player
from db import DatabaseManager

from config import Config


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startsignup(self, ctx):
        print(f"Command startsignup: Author: {ctx.author.name} Initial State: {Config.signups_open}")

        Config.signups_open = True
        Config.signup_list.clear()
        print(f"startsignup Result: Author: {ctx.author.name} Final State: {Config.signups_open}")
        await ctx.send('Sign ups are open! Sign up for the game by doing %signup')

        # DB - Store host, guild, signups_open state
        # Config.dbManager.db_startsignup(ctx.guild.id, Config.signups_open, game_host_id=ctx.author.id)
        return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def forcesignup(self, ctx, user: discord.Member):
        """This function adds a user from the sign-up list during signups."""
        # DEBUG LOG
        print(f"command forcesignup. Author: {ctx.author.name} Target: {user.name}")
        if Config.signups_open:
            if user not in Config.signup_list:
                # Create a player object - integrate this more closely into the code in the future.
                new_player = Player(user, Config.STATUS_INACTIVE, None)
                Config.appendPlayer(new_player)
                # Make sure the final location gives correct result.
                await ctx.send(f'{Config.signup_list[new_player.member].displayPlayerName()} has been signed up.')
                # Config.dbManager.db_signup(new_player.signup_number, new_player.id, new_player.vote, new_player.status)
                return
            else:
                await ctx.send(f'{user.display_name} is already signed up.')
                return
        else:
            await ctx.send('Sign ups are currently closed.')

    # WIP - Come back to this and ensure player can be removed by signup number as well as member.
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unforcesignup(self, ctx, player_to_remove: discord.Member):
        """This function removes a user from the sign-up list during signups."""
        # DEBUG LOG
        if Config.signups_open:
            print(f'Command unforcesignup. Author: {ctx.author.name} Target: {player_to_remove.name}')

            """if player_to_remove in Config.signup_list:
                Config.signup_list = [player for player in Config.signup_list if player.member != player_to_remove]
                await ctx.send(f'{player_to_remove.display_name} has been removed from the signup list.')"""
            if player_to_remove in Config.signup_list:
                removed_player = Config.signup_list.pop(player_to_remove)
                await ctx.send(f'{removed_player.displayPlayerName()} has been removed from the signup list.')
            else:
                await ctx.send(f'{player_to_remove.display_name} is not on the signup list.')
            return
        else:
            await ctx.send(f"Sign ups are currently closed.")
            return

    # WIP - When it adds a player to live_players, instead make sure it's given "Config.ALIVE_STATUS" instead.
    # WIP - The mentions should probably work since they get the keys.
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startgame(self, ctx, game_channel_param: discord.TextChannel, vote_channel_param: discord.TextChannel,
                        day_length: int = 1):
        # DEBUG LOG
        print(f'Command startgame: Author: {ctx.author.name} game_ch: {game_channel_param} vc: {vote_channel_param} '
              f'day_length: {day_length}')

        Config.global_day_length = day_length
        if not Config.signups_open:
            print(f'startgame failed - signups closed')
            await ctx.send('Signups are currently closed.')
            return
        if not Config.signup_list:
            print(f'startgame failed - signups empty')
            await ctx.send('No one has signed up yet.')
            return
        Config.signups_open = False
        Config.game_channel = game_channel_param
        Config.vote_channel = vote_channel_param
        if Config.game_channel is None or Config.vote_channel is None:
            await ctx.send('One or both channels are incorrect.')
            return
        """alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        if alive_role is None:
            alive_role = await ctx.guild.create_role(name="Alive")"""
        # WIP - Set up the signup_order for storage in the database. Might not be necessary tbh.
        signup_order = 1
        for user in Config.signup_list:
            # Config.signup_list[user].status = Config.STATUS_ALIVE
            print(f"This is user: {user.display_name} This is status: {Config.signup_list[user].status}")
            # Config.signup_list[user].signup_number = signup_order
            # signup_order += 1
            member = ctx.guild.get_member(user.id)  # Confirm member is still in server
            if member is not None:
                await Config.signup_list[member].activate()
                print(f"NEW: This is user: {user.display_name} This is status: {Config.signup_list[user].status}")
                # await member.add_roles(alive_role)
                ### Config.live_players.append(member.name)
                # Config.signup_list[member].status = Config.STATUS_ALIVE
                # Config.player_list[member] = Config.signup_list[member]
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
        print(f"Command newday Author {ctx.author.name}")
        day_length = Config.global_day_length
        Config.newDay()
        """Config.day_number += 1
        Config.vote_count_number = 1
        # Config.votes = {}
        Config.votesReset()"""

        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        await Config.game_channel.set_permissions(alive_role, send_messages=True)

        votecount_message = f"**Vote Count {Config.day_number}.0**\n\nNo votes yet."
        votecount_message += "\n" + (40 * "-")
        day_start_vote_msg = await Config.vote_channel.send(votecount_message)
        await day_start_vote_msg.pin()

        day_start_msg = await Config.game_channel.send(f"Day {Config.day_number} has begun. It will end in {day_length} days.")
        await day_start_msg.pin()

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
            print("Day phase time limit canceled!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def endgame(self, ctx):
        print(f"Command endgame: Author: {ctx.author.name}")
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
        game_category.overwrites.clear()  # set_permissions(game_category, overwrite=None)

        await game_category.set_permissions(game_guild.default_role, view_channel=True, send_messages=False)

        pattern = r"\d+-.*fallout.*"
        for channel in game_category.channels:
            await channel.edit(sync_permissions=True)
            if re.match(pattern, channel.name):
                print("MISSION SUCCESS - Fallout matched")
                await channel.set_permissions(game_guild.default_role, send_messages=True)
                fallout_msg = await channel.send(f"{alive_role.mention} {dead_role.mention} the game has ended"
                                   f" and all channels have now been locked!\n"
                                   f"You may discuss the results here!\n"
                                   f"Thank you for playing and we hope you had fun!")
                await fallout_msg.pin()

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
        Config.configReset()
        ####
        """Config.signups_open = False  # Pregame
        Config.vote_channel = None
        Config.game_channel = None
        Config.global_day_length = 1
        Config.day_end_time = 1

        Config.day_end_task_object = None

        # Game Status
        Config.day_number = 0
        Config.signup_list.clear()  # Pre & Mid
        Config.vote_count_number = 1
        Config.votes = collections.OrderedDict()
        Config.live_players = []
        Config.vote_since_last_count = 0
        # Config.start_time = datetime.now()  # Unused atm

        Config.abstained_players = []

        # Post count collection
        Config.post_counts = collections.defaultdict(lambda: collections.defaultdict(int))"""

        await ctx.send("The game has ended.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addplayer(self, ctx, new_member: discord.Member):
        """Add a new player mid-game"""
        print(f'Command addplayer: Author: {ctx.author.name} new_player: {new_member.name}')
        if Config.signups_open:
            ctx.send("Signups are still open! Use %signup or %forcesignup instead.")
            return
        if new_member not in Config.signup_list:
            print("ADDING MEMBER!")
            new_player = Player(new_member, Config.STATUS_ALIVE)
            Config.signup_list[new_member] = new_player
            await new_player.activate()
            await ctx.send(f'{new_player.displayPlayerName()} has been added to the game!')

            # alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            # await new_player.member.add_roles(alive_role)
            # Config.signup_list[new_member] = new_player
            # Config.live_players.append(new_player.displayPlayerName())  # Obsolete Debugging Code?  # UNNECESSARY DUE TO Player.Status
            # await ctx.send(f'{new_player.displayPlayerName()} has been added to the game!')
            """Config.signup_list.append(new_player)
            await new_player.add_roles(alive_role)
            Config.live_players.append(new_player.name)
            await ctx.send(f'{new_player.display_name} has been added to the game!')"""
        else:
            await ctx.send(f'{new_member.display_name} is already in the game!')

    # WIP - Check the signup index & Config.live_players
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def swapplayer(self, ctx, existing_player: discord.Member, new_player: discord.Member):
        """This function is used to swap one player out with another when the game is active"""
        # DEBUG LOG
        print(f'Command swapplayer: Author: {ctx.author.name} existing_player: {existing_player.name} '
              f'new_player: {new_player.name}')

        if not Config.signups_open:
            # if existing_player in Config.signup_list and existing_player.name in Config.live_players:
            if existing_player in Config.signup_list and Config.signup_list[existing_player].status == Config.STATUS_ALIVE:
                if new_player not in Config.player_list:
                    Config.signup_list[existing_player].status = Config.STATUS_REPLACED
                    new_player_object = Player(new_player, Config.STATUS_ALIVE)
                    new_signup_list = list(Config.signup_list.items())
                    for index, (member, player) in enumerate(new_signup_list):
                        if member == existing_player:
                            del new_signup_list[index]
                            new_signup_list.insert(index, (new_player, new_player_object))
                            break
                    """new_player_list = list(Config.player_list.items())
                    for index, (member, player) in enumerate(new_player_list):
                        if member == existing_player:
                            print(f"Playerlist member found!")
                            del new_player_list[index]
                            new_player_list.insert(index, (new_player, new_player_object))
                            break"""

                    Config.signup_list = collections.OrderedDict(new_signup_list)
                    Config.player_list[new_player] = Config.signup_list[new_player]
                    alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
                    await existing_player.remove_roles(alive_role)
                    await new_player_object.member.add_roles(alive_role)
                    """signup_index = Config.signup_list.index(existing_player)
                    # $ Config.signup_list[signup_index] = new_player
                    Config.signup_list[signup_index] = Player(new_player, Config.STATUS_ALIVE, len(Config.signup_list) + 1)
                    playerlist_index = Config.live_players.index(existing_player.name)
                    Config.live_players[playerlist_index] = new_player.name
                    alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
                    await existing_player.remove_roles(alive_role)
                    await new_player.add_roles(alive_role)
                    # await ctx.send(f'{existing_player.name} has been replaced with {new_player.name}.')"""
                    await ctx.send(f'{existing_player.display_name} has been replaced with {new_player.display_name}.')
                else:
                    await ctx.send(f'{new_player.display_name} is already in the game.')
                    if Config.player_list[new_player].status == Config.STATUS_DEAD:
                        await ctx.send(f'Note that replacing a dead player back into the game is not supported. '
                                       f'If you wish to do this anyway, use %modkill existing_player and %addplayer '
                                       f'new_player.')
            else:
                await ctx.send(f'{existing_player.display_name} is not in the game.')
        else:
            await ctx.send(f"The game hasn't started yet!  Use %forcesignup or %unforcesignup instead")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changedaylength(self, ctx, *args):
        print(f"Command changedaylength Author {ctx.author.name}")
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

    # Adjust to make this a wrapper around the "kill" function later.
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def modkill(self, ctx, member: discord.Member):
        print(f"Command modkill Author: {ctx.author.name} Target {member.name}")
        # if member.name in Config.live_players:
        if member in Config.signup_list and Config.signup_list[member].status == Config.STATUS_ALIVE:
            print("Member is in Config.signup_list and has status Config.STATUS_ALIVE")
            prev_vote, current_vote, voter = await Config.signup_list[member].kill()  # Player.kill()
            # Config.signup_list[member].kill()  # Player.kill()
            # if prev_vote:
            #     await self.bot.votecount(self.bot, ctx, voter, prev_vote, current_vote)
            # print(f"!!!KILL SANITY CHECK!!!: {member.name} should receive DEAD role")  # Add dead role in kill() if good
            # await ctx.send(
            #    f"{member.display_name} has been removed from the game. NOTE: Dead role must be added manually for now")
        else:
            await ctx.send(f"{member.display_name} is not in the game or already removed.")
            """# Config.live_players.remove(member.name)
            # Config.signup_list.remove(member)
            # Config.signup_list.pop(member)
            # killed_player = Config.signup_list[member]
            killed_player = Config.signup_list.pop(member)
            killed_player.status = Config.STATUS_DEAD
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            dead_role = discord.utils.get(ctx.guild.roles, name="Dead")
            if dead_role is None:
                dead_role = await ctx.guild.create_role(name="Dead")
            if alive_role in member.roles:
                await member.remove_roles(alive_role)
            if dead_role not in member.roles:
                # Perform unvote operation - adjust to use the unvote function in the future.
                if member in Config.votes:
                    prev_vote = Config.votes.pop(member)
                    current_vote = Config.NOT_VOTING
                    voter = member
                    await ctx.send(f"{ctx.author.display_name} has unvoted {prev_vote.display_name}.")
                    await self.bot.votecount(self.bot, ctx, voter, prev_vote, current_vote)
                print(f"!!!KILL SANITY CHECK!!!: {member.name} should receive DEAD role")
                # await member.add_roles(dead_role)  # Add this back in the future if it works fine.
            await ctx.send(f"{member.display_name} has been removed from the game. NOTE: Dead role must be added manually for now")"""
        """else:
            await ctx.send(f"{member.display_name} is not in the game or already removed.")"""
        # await self.bot.kill(ctx, member)  # WIP - Configure modkill() and kill() to just use the same function

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changevotethread(self, ctx, new_vote_channel: discord.TextChannel):
        print(f"Command changevotethread Author: {ctx.author.name}")
        Config.vote_channel = new_vote_channel
        await ctx.send(f"The vote channel is now {Config.vote_channel}")
        await Config.vote_channel.send("This is now the vote channel")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changegamethread(self, ctx, new_game_channel: discord.TextChannel):
        print(f"Command changegamethread Author: {ctx.author.name}")
        Config.game_channel = new_game_channel
        await ctx.send(f"The game channel is now {Config.game_channel}")
        await Config.game_channel.send("This is now the game channel")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gamesetup(self, ctx, game_name):
        print(f"Command gamesetup: Author: {ctx.author.name} Game_Name: {game_name}")

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
        print(f"Command changeday Author: {ctx.author.name} Day: {day}")
        Config.day_number = day
        Config.vote_count_number = 1
        await ctx.send(f"The new day is now {Config.day_number}")

    # BUG TESTING COMMAND **ONLY**
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def liveplayers(self, ctx):
        print(f"Command liveplayers Author: {ctx.author.name}")
        await ctx.send("This is live_players:\n\n " + '\n'.join(Config.live_players))

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
