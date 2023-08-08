"""
Author: Geo
Date: July 29th, 2023

This module contains all global variables used to store game settings, database settings, and frequently
used constants & methods for easy standardization.  This class is intended to be entirely static for the
time being.

In a future update, I will likely look into implementing the possibility of running multiple games. At
that point, each game will need its own instance of this class.
"""

import discord
import asyncio
from datetime import datetime
import collections
import time as t


class Config:
    # Game Setup
    bot = None

    game_host = None
    guild = None  # Primary key for a game in DB currently.
    signups_open = False  # Pregame
    game_open = False

    vote_channel = None
    game_channel = None
    playerlist_channel = None
    playerlist_message_object = None
    original_playerlist_message_object = None

    global_day_length = 1  # Rename to "phase_length_in_seconds" and rework
    day_end_time = 1
    day_end_task_object = None

    # Game Status
    day_number = 0
    vote_count_number = 1
    votes = collections.OrderedDict()
    vote_since_last_count = 0  # seems to be unused.
    # start_time = datetime.now()  # Unused atm

    signup_list = collections.OrderedDict()
    player_list = collections.OrderedDict()

    abstained_players = []

    # Post count related stuff
    post_counts = collections.defaultdict(lambda: collections.defaultdict(int))
    posts_per_24_hours_threshold = None  # WIP for use in tracking post activity
    posts_per_phase_threshold = None  # WIP for use in tracking post activity

    # Database info
    dbManager = None
    username = None
    password = None
    db_host = None
    database = None

    CONFIG_TABLE = "Configurations"
    PLAYER_TABLE = "Players"

    # CONSTANTS:
    NOT_VOTING = "not voting"  # Refers to a state in which a player either hasn't voted or has unvoted. 32 char max.
    LINE_BREAK = "-" * 40 + "\n"

    # Status & Alignment Framework: WIP doesn't currently account for extra Mafias.
    STATUS_ALIVE = "Alive"
    STATUS_DEAD = "Dead"
    STATUS_INACTIVE = "Inactive"
    STATUS_REPLACED = "Replaced"
    STATUS_MODKILLED = "Modkilled"  # For use when implementing penalizing modkill functionality.
    NO_REPLACEMENT = "No Replacement"

    ALIGNMENT_TOWN = "Town"
    ALIGNMENT_MAFIA = "Mafia"
    ALIGNMENT_3RD_PARTY = "3rd Party"

    # Discord Roles: WIP
    ALIVE_ROLE = "Alive"
    DEAD_ROLE = "Dead"
    SPECTATOR_ROLE = "Spectator"
    SPOILER_ROLE = "Spoilers"

    # WIP - Assumes that the argument is a Player.
    @classmethod
    def appendPlayer(self, new_player):
        """Add a player to the game - i.e. signup"""
        Config.signup_list[new_player.member] = new_player

    @classmethod
    def convertDaysToSeconds(self, days):
        return int(days * 24 * 60 * 60)

    @classmethod
    def convertSecondsToDays(self, seconds):
        return ((seconds / 24) / 60) / 60

    @classmethod
    async def end_day_after_delay(cls, day_length_in_seconds):
        Config.day_end_time = t.time() + day_length_in_seconds
        Config.dbManager.db_end_day_after_delay(day_length_in_seconds)
        try:
            await asyncio.sleep(day_length_in_seconds)
            alive_role = discord.utils.get(Config.game_channel.guild.roles, name="Alive")
            await Config.game_channel.set_permissions(alive_role, send_messages=False)
            await Config.game_channel.send("The day has ended due to time running out.")
            return
        except asyncio.CancelledError:
            print("Day phase time limit canceled!")

    # WIP - Consider how resetting Config affects the database info.
    @classmethod
    def configReset(cls):
        """This function resets all the static values of the Config class back to their defaults"""
        if Config.day_end_task_object:
            Config.day_end_task_object.cancel()

        Config.game_host = None
        Config.guild = None  # Primary key for the game, currently.
        Config.signups_open = False  # Pregame
        Config.game_open = False
        Config.vote_channel = None
        Config.game_channel = None
        Config.player_channel = None

        Config.global_day_length = 1  # Rename to "phase_length_in_seconds" and rework
        Config.day_end_time = 1  # Time in days - rework to time in seconds
        Config.day_end_task_object = None

        # Game Status
        Config.day_number = 0
        Config.vote_count_number = 1
        Config.votes.clear()
        Config.vote_since_last_count = 0  # seems to be unused.
        # start_time = datetime.now()  # Unused atm

        Config.signup_list = collections.OrderedDict()
        Config.player_list = collections.OrderedDict()

        Config.abstained_players = []

        # Post count related stuff
        Config.post_counts = collections.defaultdict(lambda: collections.defaultdict(int))
        Config.posts_per_24_hours_threshold = None  # WIP for use in tracking post activity
        Config.posts_per_phase_threshold = None  # WIP for use in tracking post activity

    @classmethod
    def votesReset(cls):
        for member in Config.votes.keys():
            Config.dbManager.db_unvote(member)
        Config.votes.clear()
        # WIP - Database should clear the votes.

    """@classmethod
    def newDay(cls):
        Config.day_number += 1
        Config.vote_count_number = 1
        Config.votesReset()
        return Config.day_number, Config.vote_count_number,"""

    @classmethod
    def configReport(cls):
        print(f"This is Config.game_host: {Config.game_host.name}" if Config.game_host else f"This is Config.game_host: {Config.game_host}")
        print(f"This is Config.guild: {Config.guild.name}" if Config.guild else f"This is Config.guild: {Config.guild}")
        print(f"This is Config.signups_open: {Config.signups_open}")
        print(f"This is Config.vote_channel: {Config.vote_channel.name}" if Config.vote_channel else f"This is Config.vote_channel: {Config.vote_channel}")
        print(f"This is Config.game_channel: {Config.game_channel.name}" if Config.game_channel else f"This is Config.game_channel: {Config.game_channel}")

        print(f"This is Config.global_day_length: {Config.global_day_length}")
        print(f"This is Config.day_end_time: {Config.day_end_time}")
        print(f"This is Config.day_number: {Config.day_number}")
        print(f"This is Config.vote_count_number: {Config.vote_count_number}")
        print(f"This is Config.votes: {key} VOTE: '{value}'" for key, value in Config.votes.items())
        return

    @classmethod
    async def playerChannelUpdate(cls):
        """This method will be used to update the player list based on Config.player_list"""
        print("Calling Config.playerChannelUpdate() method")
        if not Config.game_open:
            print("No open game found!")
            return
        if not Config.playerlist_channel:
            print("No playerlist channel found!")
            return
        if not Config.original_playerlist_message_object:
            print("Creating Original playerlist message!")
            Config.original_playerlist_message_object =\
                await Config.playerlist_channel.send(Config.constructOriginalPlayerlistMessage())
            Config.dbManager.db_original_playerlist_message(Config.original_playerlist_message_object)
        if not Config.playerlist_message_object:
            print("Creating Updated playerlist message!")
            Config.playerlist_message_object = await Config.playerlist_channel.send(Config.updatePlayerlistMessage())
            Config.dbManager.db_updated_playerlist_message(Config.playerlist_message_object)
        else:
            print("Editing Updated playerlist message!")
            new_content = Config.updatePlayerlistMessage()
            await Config.playerlist_message_object.edit(content=new_content)

    @classmethod
    def constructOriginalPlayerlistMessage(cls):
        """This function constructs the original player list and stores it as an object in Config."""
        """Currently, replaced out people are not accounted for."""
        print("Helper command 'constructOriginalPlayerlistMessage' called")
        if not Config.game_open:
            print("No open game found!")
            return
        if not Config.playerlist_channel:
            print("No playerlist channel found!")
            return
        index = 0
        original_playerlist_message = ''
        original_playerlist_message += "**Original Playerlist:**" + "\n\n"
        for index, (member, player_data) in enumerate(Config.player_list.items(), start=1):
            if player_data.status != Config.STATUS_REPLACED:
                original_playerlist_message += f"{index}\. {member.display_name}" + "\n"
        return original_playerlist_message

    @classmethod
    def updatePlayerlistMessage(cls):
        """This helper function constructs the message to be posted in the playerlist channel"""
        if not Config.game_open:
            print("ERROR! No open game found!")
            return
        if not Config.playerlist_channel:
            print("ERROR! No playerlist channel found!")
            return
        updated_playerlist_message = ''
        print(f'method updatePlayerlistMessage called')
        if Config.game_open:
            alive_players = []
            dead_players = []
            index = 0
            for member, player in Config.player_list.items():
                print(f"This is member.name: {member.name} player.status: {player.status}")
                if player.status == Config.STATUS_ALIVE:
                    index += 1
                    print(f"Player is alive! This is index: {index}")
                    alive_players.append(f"{index}\. {member.display_name}")
                    print(f"Appended: {member.display_name} at: {index}")
                if player.status == Config.STATUS_DEAD:
                    index += 1
                    print(f"Player is dead! This is index: {index}")
                    dead_players.append(f"{index}\. {member.display_name}")
                    print(f"Appended: {member.display_name} at: {index}")

            playerlist_string = ''
            if len(alive_players) > 0:
                playerlist_string += "\n\n__**Alive Players**__\n\n" + '\n'.join(alive_players) + '\n'
            else:
                playerlist_string += "\n__**Alive Players**__\n" + '\n (None)'
            if len(dead_players) > 0:
                playerlist_string += "\n__**Dead Players**__\n\n" + '\n'.join(dead_players)
            else:
                playerlist_string += "\n__**Dead Players**__\n" + '\n (None)'
            return playerlist_string

    "==============================================================================================="
    "============================Non-Functional WIP Code Below======================================"
    "==============================================================================================="

    # WIP - Non-functional - Assumes that the argument is a Player.
    @classmethod
    def removePlayer(self, player_to_remove):
        """Remove a player from the game - i.e. unsignup"""
        Config.players_by_member.pop(player_to_remove.member, None)
        Config.players_by_order.pop(player_to_remove.member, None)