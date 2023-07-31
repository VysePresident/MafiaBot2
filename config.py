"""
Author: Geo
Date: July 29th, 2023

This module contains all global variables used to store game settings, database settings, and frequently
used constants & methods for easy standardization.  This class is intended to be entirely static for the
time being.

In a future update, I will likely look into implementing the possibility of running multiple games. At
that point, each game will need its own instance of this class.
"""

import asyncio
from datetime import datetime
import collections


class Config:
    # Game Setup
    bot = None

    game_host = None  # Currently unused, but useful as a key. Might be useful for separating admin/host perms.
    guild = None  # Currently not used, may use as a key instead. Logically implies one game per guild.
    signups_open = False  # Pregame
    vote_channel = None
    game_channel = None
    global_day_length = 1  # Rename to "phase_length_in_seconds" and rework
    day_end_time = 1

    day_end_task_object = None

    # Game Status
    day_number = 0
    # signup_list = []  # Pre & Mid
    vote_count_number = 1
    votes = collections.OrderedDict()
    live_players = []
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
    NOT_VOTING = "not voting"  # Refers to a state in which a player either hasn't voted or has unvoted.
    LINE_BREAK = "-" * 40 + "\n"

    # Status & Alignment Framework: WIP doesn't currently account for extra Mafias.
    STATUS_ALIVE = "Alive"
    STATUS_DEAD = "Dead"
    STATUS_INACTIVE = "Inactive"
    STATUS_REPLACED = "Replaced"
    STATUS_MODKILLED = "Modkilled"  # For use when implementing penalizing modkill functionality.

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
        # Config.players_by_member[new_player.member] = new_player
        # Config.players_by_order[new_player.signup_number] = new_player

    # WIP - Assumes that the argument is a Player.
    @classmethod
    def removePlayer(self, player_to_remove):
        """Remove a player from the game - i.e. unsignup"""
        Config.players_by_member.pop(player_to_remove.member, None)
        Config.players_by_order.pop(player_to_remove.member, None)
    @classmethod
    def convertDaysToSeconds(self, days):
        return days * 24 * 60 * 60
    @classmethod
    def convertSecondsToDays(self, seconds):
        return ((seconds / 24) / 60) / 60

    @classmethod
    def organize_signup_list(cls, player=None, position=None):
        """Use this function to organize the list based on the entries in the database"""

    # WIP - Consider how resetting Config affects the database info.
    @classmethod
    def configReset(cls):
        """This function resets all the static values of the Config class back to their defaults"""
        Config.game_host = None  # Currently unused, but useful as a key. Might be useful for separating admin/host perms.
        Config.guild = None  # Currently not used, may use as a key instead. Logically implies one game per guild.
        Config.signups_open = False  # Pregame
        Config.vote_channel = None
        Config.game_channel = None
        Config.global_day_length = 1  # Rename to "phase_length_in_seconds" and rework
        Config.day_end_time = 1

        Config.day_end_task_object = None

        # Game Status
        Config.day_number = 0
        # signup_list = []  # Pre & Mid
        Config.vote_count_number = 1
        Config.votes.clear()
        Config.live_players = []  # Obsolete now that Player.status is a thing?
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
        Config.votes.clear()

    @classmethod
    def newDay(cls):
        Config.day_number += 1
        Config.vote_count_number = 1
        Config.votesReset()

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
