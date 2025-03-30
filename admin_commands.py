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

from config import Config


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startsignup(self, ctx):
        print(f"Command startsignup: Author: {ctx.author.name} Initial State: {Config.signups_open}")
        if Config.signups_open:
            await ctx.send("Signups are already open.")
            return
        if not Config.game_open:
            Config.configReset()
            Config.game_host = ctx.author
            Config.guild = ctx.guild
            Config.signups_open = True
            Config.signup_list.clear()
            print(f"startsignup Result: Author: {ctx.author.name} Final State: {Config.signups_open}")
            await ctx.send('Sign ups are open! Sign up for the game by doing %signup')

            # DB - Store host, guild, signups_open state, game_open state
            Config.dbManager.db_startsignup(ctx.guild, Config.signups_open, Config.game_open, Config.game_host)
        else:
            await ctx.send('Game is ongoing! Signups cannot be opened until the game is closed with %endgame or '
                           '%closegame!')
            print(f"startsignup Result: Author: {ctx.author.name} Final State: {Config.signups_open}")

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
                new_player = Player(user, Config.STATUS_INACTIVE)
                Config.appendPlayer(new_player)
                # Make sure the final location gives correct result.
                Config.dbManager.db_signup(user, new_player.status)
                await ctx.send(f'{Config.signup_list[new_player.member].displayPlayerName()} has been signed up.')
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
        print(f'Command unforcesignup. Author: {ctx.author.name} Target: {player_to_remove.name}')
        if Config.signups_open:
            if player_to_remove in Config.signup_list:
                removed_player = Config.signup_list.pop(player_to_remove)
                print(f"{player_to_remove.display_name} has been removed!")

                Config.dbManager.db_unsignup(player_to_remove)

                await ctx.send(f'{removed_player.displayPlayerName()} has been removed from the signup list.')
            else:
                await ctx.send(f'{player_to_remove.display_name} is not on the signup list.')
            return
        else:
            await ctx.send(f"Sign ups are currently closed.")
            return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startgame(self, ctx, game_channel_param: discord.TextChannel, vote_channel_param: discord.TextChannel,
                        day_length: int = 1, playerlist_channel_param: discord.TextChannel = None):
        # DEBUG LOG
        print(f'Command startgame: Author: {ctx.author.name} game_ch: {game_channel_param} vc: {vote_channel_param} '
              f'day_length: {day_length}')

        Config.global_day_length = day_length
        if Config.game_open:
            print(f'startgame failed - game already active')
            await ctx.send('This command cannot be used while a game is already active!')
        if not Config.signups_open:
            print(f'startgame failed - signups closed')
            await ctx.send('Signups are currently closed.')
            return
        if not Config.signup_list:
            print(f'startgame failed - signups empty')
            await ctx.send('No one has signed up yet.')
            return
        Config.signups_open = False
        Config.game_open = True
        Config.game_channel = game_channel_param
        Config.vote_channel = vote_channel_param
        if Config.game_channel is None or Config.vote_channel is None:
            await ctx.send('One or both channels are incorrect.')
            return
        for user in Config.signup_list:
            # print(f"This is user: {user.display_name} This is status: {Config.signup_list[user].status}")
            member = ctx.guild.get_member(user.id)  # Confirm member is still in server
            if member is not None:
                await Config.signup_list[member].activate()
                print(f"NEW: This is user: {user.display_name} This is status: {Config.signup_list[user].status}")

        game_players = "\n".join([user.mention for user in Config.signup_list])
        await Config.game_channel.send(f'The game has started with the following players:\n{game_players}')

        vote_message = f'Day {Config.day_number + 1} votes will be displayed here. ' \
                       f'Required votes to eliminate a player: {len(Config.signup_list) // 2 + 1}'

        await Config.vote_channel.send(vote_message)

        Config.dbManager.db_startgame(Config.game_channel, Config.vote_channel, Config.global_day_length)

        if playerlist_channel_param:
            await self.changeplayerlistthread(playerlist_channel_param)
        else:
            await ctx.send(f"You did not choose to set the optional playerlist channel at the end of the command! "
                     f"If you would like to set a playerlist to automatically update, use the comamnd:"
                     f"```"
                     f"%changeplayerlistthread"
                     f"```")

        await self.newday(ctx, day_length)
        return

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def newday(self, ctx, day_length: int = 1):
        if Config.game_open:
            print(f"Command newday Author {ctx.author.name}")
            day_length = Config.global_day_length

            Config.day_number += 1
            Config.vote_count_number = 1
            Config.votesReset()

            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            await Config.game_channel.set_permissions(alive_role, send_messages=True)

            votecount_message = f"**Vote Count {Config.day_number}.0**" + "\n\n"
            votecount_message += self.bot.createVoteCountMessage({}, None, None, None)[0] + "\n"
            votecount_message += self.bot.findNotVoting() + "\n"
            votecount_message += self.bot.playersNeededToLynch()
            votecount_message += (40 * "-")
            day_start_vote_msg = await Config.vote_channel.send(votecount_message)
            try:
                await day_start_vote_msg.pin()
            except discord.HTTPException as e:
                await Config.vote_channel.send("There are too many pinned messages in this channel to pin this message")

            day_start_msg = \
                await Config.game_channel.send(f"Day {Config.day_number} has begun. It will end in {day_length} days.")

            try:
                await day_start_msg.pin()
            except discord.HTTPException as e:
                await Config.game_channel.send("There are too many pinned messages in this channel to pin this message")

            Config.day_end_time = t.time() + Config.convertDaysToSeconds(day_length)  # WIP - day_length should already be in seconds

            # Config.day_end_task_object = self.bot.loop.create_task(self.end_day_after_delay(day_length))
            Config.day_end_task_object = self.bot.loop.create_task(Config.end_day_after_delay(Config.convertDaysToSeconds(day_length)))

            # How do I store day end date?  Let's do it in the
            Config.dbManager.db_newday(Config.convertDaysToSeconds(Config.global_day_length),
                             Config.vote_count_number, Config.day_number)
            return
        else:
            await ctx.send("No open game found!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def endgame(self, ctx):
        if Config.game_open:
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
                    try:
                        await fallout_msg.pin()
                    except discord.HTTPException as e:
                        await channel.send("There are too many pinned messages in this channel to pin this message")
                        print("There are too many pinned messages in this channel to pin this message")

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

            # Reset database and all config values
            Config.dbManager.db_endgame()
            Config.configReset()

            await ctx.send("The game has ended.")
        else:
            await ctx.send("No open game found!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def closegame_noreveal(self, ctx):
        if Config.game_open:
            print(f"Command closegame: ctx.author.name: {ctx.author.name}")
            if Config.game_open:
                Config.dbManager.db_endgame()
                Config.configReset()
                await ctx.send("The game has ended. Any reveals must be done manually.")
            else:
                await ctx.send("There is no open game to close!")
        else:
            await ctx.send("No open game found!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addplayer(self, ctx, new_member: discord.Member):
        """Add a new player mid-game"""
        print(f'Command addplayer: Author: {ctx.author.name} new_player: {new_member.name}')
        if Config.signups_open:
            await ctx.send("The game hasn't started yet! Use %forcesignup or %unforcesignup instead")
            return
        if not Config.game_open:
            await ctx.send("No open game found!")
            return
        if new_member not in Config.signup_list:
            print("ADDING MEMBER!")
            new_player = Player(new_member, Config.STATUS_ALIVE)
            Config.signup_list[new_member] = new_player

            Config.dbManager.db_addplayer(new_member)

            await new_player.activate()
            await ctx.send(f'{new_player.displayPlayerName()} has been added to the game!')
        else:
            await ctx.send(f'{new_member.display_name} is already in the game!')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def swapplayer(self, ctx, existing_player: discord.Member, new_player: discord.Member):
        """This function is used to swap one player out with another when the game is active"""
        # DEBUG LOG
        print(f'Command swapplayer: Author: {ctx.author.name} existing_player: {existing_player.name} '
              f'new_player: {new_player.name}')
        if Config.signups_open:
            await ctx.send("The game hasn't started yet! Use %forcesignup or %unforcesignup instead")
            return
        if Config.game_open:
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

                    Config.signup_list = collections.OrderedDict(new_signup_list)
                    Config.player_list[new_player] = Config.signup_list[new_player]
                    alive_role = discord.utils.get(ctx.guild.roles, name="Alive")

                    Config.dbManager.db_swapplayer(existing_player, new_player)

                    await existing_player.remove_roles(alive_role)
                    await new_player_object.member.add_roles(alive_role)
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
            await ctx.send(f"The game hasn't started yet!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changedaylength(self, ctx, *args):
        print(f"Command changedaylength Author {ctx.author.name}")
        if Config.game_open:
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
                    return
            Config.global_day_length = day_length_in_seconds / (24 * 60 * 60)

            Config.dbManager.db_changedaylength(day_length_in_seconds)

            Config.day_end_task_object.cancel()
            Config.day_end_task_object = self.bot.loop.create_task(Config.end_day_after_delay(day_length_in_seconds))

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
        else:
            await ctx.send("No open game found!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def modkill(self, ctx, member: discord.Member):
        if Config.game_open:
            print(f"Command modkill Author: {ctx.author.name} Target {member.name}")
            if member in Config.signup_list and Config.signup_list[member].status == Config.STATUS_ALIVE:
                print("Member is in Config.signup_list and has status Config.STATUS_ALIVE")
                prev_vote, current_vote, voter = await Config.signup_list[member].kill()  # Player.kill()
                if prev_vote is not None:
                    await self.bot.votecount(self.bot, ctx, voter, prev_vote, current_vote)

            else:
                print("Member was either not in the signup list or didn't have the alive status.")
                await ctx.send(f"{member.display_name} is not in the game or already removed.")
        else:
            await ctx.send("No open game found!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changevotethread(self, ctx, new_vote_channel: discord.TextChannel):
        if Config.game_open:
            print(f"Command changevotethread Author: {ctx.author.name}")
            Config.vote_channel = new_vote_channel

            Config.dbManager.db_changevotethread(new_vote_channel)

            await ctx.send(f"The vote channel is now {Config.vote_channel}")
            await Config.vote_channel.send("This is now the vote channel")
        else:
            await ctx.send("No open game found!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changegamethread(self, ctx, new_game_channel: discord.TextChannel):
        if Config.game_open:
            print(f"Command changegamethread Author: {ctx.author.name}")
            Config.game_channel = new_game_channel

            Config.dbManager.db_changegamethread(new_game_channel)

            await ctx.send(f"The game channel is now {Config.game_channel}")
            await Config.game_channel.send("This is now the game channel")
        else:
            await ctx.send("No open game found!")

    async def changeplayerlistthread(self, new_playerlist_channel: discord.TextChannel):
        """This method changes or sets the playerlist channel"""
        if Config.game_open:
            print(f"changeplayerlistthread called - new_playerlist_channel: {new_playerlist_channel.name}")
            Config.playerlist_channel = new_playerlist_channel

            Config.dbManager.db_changeplayerlistthread(new_playerlist_channel)

            # await ctx.send(f"The playerlist channel is now {Config.playerlist_channel}")
            await Config.playerChannelUpdate()
            Config.dbManager.db_changeplayerlistthread(new_playerlist_channel)
        else:
            print("No open game found!")
            # await ctx.send("No open game found!")

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
        await spec_channel.set_permissions(spec_role, view_channel=True, send_messages=True)

        # Mod thread - only spoiled can see.
        channel_name = current_game_number + channel_break + "mod-thread"
        mod_channel = await category.create_text_channel(channel_name)
        await mod_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        await mod_channel.set_permissions(spoil_role, view_channel=True, send_messages=False)

        # Spoiled chat - only spoiled can see.
        channel_name = current_game_number + channel_break + "spoiled-spec"
        spoiled_channel = await category.create_text_channel(channel_name)
        await spoiled_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
        await spoiled_channel.set_permissions(spoil_role, view_channel=True, send_messages=True)

        # Fallout chat - nobody can see until %endgame.
        channel_name = current_game_number + channel_break + "fallout"
        fallout_channel = await category.create_text_channel(channel_name)
        await fallout_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def changeday(self, ctx, day: int):
        if Config.game_open:
            print(f"Command changeday Author: {ctx.author.name} Day: {day}")
            Config.day_number = day
            Config.vote_count_number = 1

            Config.dbManager.db_changeday(Config.day_number)

            await ctx.send(f"The new day is now {Config.day_number}")
        else:
            await ctx.send("No open game found!")

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
