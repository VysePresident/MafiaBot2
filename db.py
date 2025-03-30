"""
Author: Geo
Date: July 29th, 2023

This module hosts the DatabaseManager class. This class handles setting up the database connection
and storing/retrieving info for functions in other modules.

Methods in this class take the form "db_functionName()" where functionName is equivalent to the
function/method name for which it is acting as a proxy between that function and the DB.
"""
import collections
import datetime

import discord
import mysql.connector
from mysql.connector import errorcode
from config import Config
import time as t
from player import Player
import asyncio


class DatabaseManager:
    def __init__(self, user, password, host, database, bot):
        self.user = user
        self.password = password
        self.host = host
        self.database = database

        self.cnx = None
        self.bot = bot

    async def connect(self):
        try:
            self.cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=3306,
                database=self.database
                )
            print("DATABASE CONNECTED!")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your username or passwword")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("The database does not exist")
            else:
                print(f"This is err: {err}")

    async def close(self):
        print(f"Attempting to close connection!")
        if self.cnx:
            self.cnx.close()
            self.cnx = None
            print("Connection closed!")
        else:
            print("No Connection to close!")

    async def setConfigurations(self):
        """Reset the configurations channel"""

        # Check connection
        if not self.cnx:
            print(f"No connection found! Connecting inside setConfigurations.")
            await self.connect()
        if not self.cnx:
            print(f"No connection information provided.")
            return "FAILURE"

        cursorConfig = self.cnx.cursor(buffered=True)
        queryConfig = (
            f"SELECT * FROM {self.database}.Configurations"
        )

        # Check if an active game exists - Assumption is that 0 rows = inactive and 1 row = active
        active_game = None
        cursorConfig.execute(queryConfig)
        if cursorConfig.rowcount < 1:
            active_game = False
            print("NO GAME STORED!")
        elif cursorConfig.rowcount > 1:
            active_game = False
            print("ERROR!  MORE THAN ONE GAME STORED!")
        else:
            active_game = True
            print("GAME FOUND! LOADING DATA NOW")

        channel_info = None
        player_info = []

        # Restore from DB only if active game exists - NOTE: This is way too long. It is very silly. Fix later.
        if active_game and self.cnx:
            for (guild_id, guild_name, host_id, host_name, signups_open, game_open, vote_channel_id, vote_channel_name,
                 game_channel_id, game_channel_name, player_list_channel_id, player_list_channel_name,
                 playerlist_original_msg_id, playerlist_updated_msg_id, global_day_length_in_seconds, day_end_time,
                 day_number, vote_count_number) in cursorConfig:

                # Get the game and vote channels given guild_id
                Config.guild = discord.utils.get(self.bot.guilds, id=int(guild_id))
                if not Config.guild:
                    print("Guild not found!")
                Config.host = discord.utils.get(Config.guild.members, id=int(host_id))
                if not Config.host:
                    print("Host not found!")

                # Retrieve other configurations
                print("Storing channel_info")
                Config.signups_open = True if signups_open else False
                print(f"Set Config.signups_open: {Config.signups_open} signups_open: {signups_open}")

                Config.game_open = True if game_open else False
                print(f"Set Config.game_open: {Config.game_open} game_open: {game_open}")

                if game_open:
                    print("Open Game Found!")
                    Config.game_channel = discord.utils.get(Config.guild.channels, id=int(game_channel_id))
                    if not Config.game_channel:
                        print("Game channel not found!")
                    Config.vote_channel = discord.utils.get(Config.guild.channels, id=int(vote_channel_id))
                    if not Config.vote_channel:
                        print("Vote channel not found!")
                    if player_list_channel_id:
                        Config.playerlist_channel = discord.utils.get(Config.guild.channels,
                                                                      id=int(player_list_channel_id))
                        if playerlist_original_msg_id:
                            Config.original_playerlist_message_object = \
                                await Config.playerlist_channel.fetch_message(int(playerlist_original_msg_id))
                        if playerlist_updated_msg_id:
                            Config.playerlist_message_object = \
                                await Config.playerlist_channel.fetch_message(int(playerlist_updated_msg_id))

                    # Set this up
                    time_left_in_phase = (day_end_time - datetime.datetime.now()).total_seconds()
                    # Config.day_end_task_object = self.bot.loop.create_task(
                    #     Config.end_day_after_delay(time_left_in_phase))

                    Config.day_number = day_number
                    # print(f"Set Config.day_number: {Config.day_number} phase_number: {day_number}")

                    Config.global_day_length = ((global_day_length_in_seconds / 60) / 60) / 24
                    # print(f"Set Config.global_day_length: {Config.global_day_length} phase_length_in_seconds:"
                    #       f" {global_day_length_in_seconds}")

                    Config.vote_count_number = vote_count_number
                    # print(f"Set Config.vote_count_number: {Config.vote_count_number} vote_count_number:"
                    #       f" {vote_count_number}")

                # Set up players and votes
                cursorPlayers = self.cnx.cursor(buffered=True)
                queryPlayers = (
                    f"SELECT * FROM {self.database}.Players"
                )
                cursorPlayers.execute(queryPlayers)
                i = 0
                votes = {}
                player_list = {}
                signup_list = {}
                for index, (player_id, player_name, player_status, sign_up_date, replacement_id, vote_id, vote_name,
                            vote_date) in enumerate(cursorPlayers, start=1):
                    # Debugging code - add back?
                    """if index != signup_number:
                        print("UNEXPECTED BEHAVIOR! index != signup_number")"""
                    member = discord.utils.get(Config.guild.members, id=int(player_id))
                    voted = Config.NOT_VOTING
                    if vote_id != Config.NOT_VOTING:
                        if vote_id is None and game_open:
                            print(f"Could not load {member.display_name}'s vote - target not found in guild.")
                        else:
                            voted = discord.utils.get(Config.guild.members, id=int(vote_id))

                    player = Player(member, player_status)
                    # print(f"Adding player number {index}: {player.member.display_name} to player_list roster!")
                    player_list[sign_up_date] = (member, player)
                    if player_status == Config.STATUS_ALIVE or player_status == Config.STATUS_INACTIVE:
                        # print(f"Player  {index}: {player.member.display_name} to player_list roster!")
                        signup_list[sign_up_date] = (member, player)

                    # Log the vote and make sure it's stored correctly
                    # print(f"Player {player.member.display_name} voted for "
                    #       f"{voted.display_name if voted != Config.NOT_VOTING else voted}")
                    if voted != Config.NOT_VOTING:
                        Config.votes[player.member] = voted
                        votes[vote_date] = (member, voted)

                # Construct Config.signup_list and Config.player_list
                sorted_player_list = sorted(player_list)
                Config.player_list = collections.OrderedDict((player_list[key][0], player_list[key][1]) for key in
                                                             sorted_player_list)
                Config.signup_list = collections.OrderedDict((player_list[key][0], player_list[key][1]) for key in
                                                             sorted_player_list if player_list[key][1].status ==
                                                             Config.STATUS_ALIVE or player_list[key][1].status ==
                                                             Config.STATUS_INACTIVE)

                # Construct votecount info
                sorted_votes_keys = sorted(votes.keys())
                Config.votes = collections.OrderedDict((votes[key][0], votes[key][1]) for key in sorted_votes_keys if
                                                       votes[key][1] != Config.NOT_VOTING)
                cursorConfig.close()
                cursorPlayers.close()
            return "SUCCESS"
        return "UNNEEDED"

    def db_startsignup(self, guild, signups_open, game_open, game_host):
        """This function stores the host_id, guild_id, and signups_open state after signups are opened"""
        """This function is considered to 'create' the game.  It can only be opened once at a time."""
        # Create cursor and query
        query_start_signups = (
            f"INSERT INTO {self.database}.{Config.CONFIG_TABLE} (guild_id, guild_name, signups_open, game_open, "
            f"host_id, host_name) "
            f"VALUES (%s, %s, %s, %s, %s, %s) "
            f"ON DUPLICATE KEY UPDATE signups_open = VALUES(signups_open), game_open = VALUES(game_open), host_id = VALUES(host_id);"
        )
        try:
            with self.cnx.cursor() as cursor_start_signups:
                cursor_start_signups.execute(query_start_signups, (str(guild.id), guild.name, signups_open, game_open,
                                                                   str(game_host.id), game_host.name))
                print("startsignup commit")
                self.cnx.commit()
            print("startsignup data stored!")
        except Exception as e:
            print(f"db_startsignup error occurred: {e}")
            self.cnx.rollback()

    def db_signup(self, member, status):
        """Store a player's info after they join."""
        vote_name = Config.NOT_VOTING
        vote_id = Config.NOT_VOTING
        replacement_id = None

        query_signup = (
            f"INSERT INTO {self.database}.{Config.PLAYER_TABLE} (player_id, player_name, player_status, sign_up_date, "
            f"replacement_id, vote_id, vote_name)"
            f"VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        try:
            with self.cnx.cursor() as cursor_forcesignup:
                cursor_forcesignup.execute(query_signup, (str(member.id), member.name, status, datetime.datetime.now(),
                                                          replacement_id, str(vote_id), vote_name))
                self.cnx.commit()
                print("signup data stored!")
        except Exception as e:
            print(f"signup error occurred: {e}")
            self.cnx.rollback()

    def db_unsignup(self, member):
        """Remove a player from the Players table of the database"""
        query_unsignup = (
            f"DELETE FROM {self.database}.{Config.PLAYER_TABLE} "
            f"WHERE player_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_unsignup:
                cursor_unsignup.execute(query_unsignup, (str(member.id),))
                self.cnx.commit()
                print("unsignup data removed!")
        except Exception as e:
            print(f"unsignup error occurred: {e}")
            self.cnx.rollback()

    def db_startgame(self, game_channel, vote_channel, day_length):
        """This function stores information related to the admin_commands.py method 'startgame'"""
        phase_length_in_seconds = Config.convertDaysToSeconds(day_length)
        query_startgame = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET signups_open =  %s, game_open = %s, vote_channel_id = %s, vote_channel_name = %s, "
            f"game_channel_id = %s, game_channel_name = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_startgame:
                print(f"Config.signups_open {Config.signups_open} Config.game_open: {Config.game_open}")
                print(f"Config.str(vote_channel.id) {str(vote_channel.id)} str(game_channel.id): {str(game_channel.id)}")
                print(f"str(Config.guild.id): {str(Config.guild.id)}")
                cursor_startgame.execute(query_startgame, (Config.signups_open, Config.game_open, str(vote_channel.id),
                                                           vote_channel.name, str(game_channel.id), game_channel.name,
                                                           str(Config.guild.id)))
                self.cnx.commit()
                print("startgame data stored!")
        except Exception as e:
            print(f"startgame error occurred: {e}")
            self.cnx.rollback()

    def db_newday(self, global_day_length_in_seconds, vote_count_number, day_number):
        """This function stores information from the newDay() method split between Config and admin_commands.py"""

        # phase_end_datetime = datetime.datetime.now() + datetime.timedelta(seconds=phase_end_time)
        query_newday = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET global_day_length_in_seconds = %s, vote_count_number = %s, day_number = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_newday:
                cursor_newday.execute(query_newday, (global_day_length_in_seconds, vote_count_number, day_number,
                                                     str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_newday data updated successfully!")
        except Exception as e:
            print(f"db_newday error occurred: {e}")
            self.cnx.rollback()

    def db_vote(self, voter, vote_target):
        """This function stores information from placing a vote"""
        print("Entered db_vote")
        query_vote = (
            f"UPDATE {self.database}.{Config.PLAYER_TABLE} "
            f"SET vote_id = %s, vote_name = %s, vote_date = %s"
            f"WHERE player_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_vote:
                cursor_vote.execute(query_vote, (str(vote_target.id), vote_target.name,
                                                 datetime.datetime.now(), str(voter.id)))
                self.cnx.commit()
                print("db_vote updated successfully.")
        except Exception as e:
            print(f"db_vote error occurred: {e}")
            self.cnx.rollback()

    def db_unvote(self, member):
        """This function stores information from removing a vote"""
        query_unvote = (
            f"UPDATE {self.database}.{Config.PLAYER_TABLE} "
            f"SET vote_id = %s, vote_name = %s, vote_date = NULL "
            f"WHERE player_id = %s "
        )
        try:
            with self.cnx.cursor() as cursor_unvote:
                cursor_unvote.execute(query_unvote, (str(Config.NOT_VOTING), Config.NOT_VOTING, str(member.id)))
                self.cnx.commit()
                print("Changed unvote info in DB")
        except Exception as e:
            print(f"db_unvote error occurred: {e}")
            self.cnx.rollback()

    def db_playerStatusUpdate(self, member, player_status, new_member=None):
        """This function stores information from the Player.activate() method & other status updates"""
        query_status_update = (
            f"UPDATE {self.database}.{Config.PLAYER_TABLE} "
            f"SET player_status = %s, replacement_id = %s "
            f"WHERE player_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_status_update:
                cursor_status_update.execute(query_status_update,
                                             (player_status, None if new_member is None else str(new_member.id),
                                              str(member.id)))
                self.cnx.commit()
                print("db_playerStatusUpdate stored data successfully!")
        except Exception as e:
            print(f"db_playerStatusUpdate error: {e}")
            self.cnx.rollback()

    def db_end_day_after_delay(self, day_length_in_seconds):
        """This function takes the day end time in seconds & stores a DATETIME in DB to act as deadline"""
        print(f"\n\nStarting db_end_day_after_delay NOW")
        deadline = datetime.datetime.now() + datetime.timedelta(seconds=day_length_in_seconds)
        print(f"This is deadline: {deadline}")
        query_end_day_after_delay = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET day_end_time = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_end_day_after_delay:
                cursor_end_day_after_delay.execute(query_end_day_after_delay, (deadline, Config.guild.id))
                self.cnx.commit()
                print(f"db_end_day_after_delay updated successfully")
        except Exception as e:
            print(f"db_end_day_after_delay error: {e}")
            self.cnx.rollback()

    def db_kill(self, member):
        """This function is used to remove a player from the game. Info is still stored for future reference."""
        query_kill = (
            f"UPDATE {self.database}.{Config.PLAYER_TABLE} "
            f"SET vote_id = %s, player_status = %s, vote_name = %s"
            f"WHERE player_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_kill:
                cursor_kill.execute(query_kill, (Config.NOT_VOTING, Config.STATUS_DEAD, Config.NOT_VOTING,
                                                 member.id))
                self.cnx.commit()
                print(f"db_kill executed successfully!")
        except Exception as e:
            print(f"db_kill error: {e}")
            self.cnx.rollback()

    def db_endgame(self):
        """This function handles removing the game from the database after it ends."""
        query_endgame_configurations = (
            f"DELETE FROM {self.database}.{Config.CONFIG_TABLE} "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_endgame:
                cursor_endgame.execute(query_endgame_configurations, (Config.guild.id,))
                self.cnx.commit()
                print(f"db_endgame success")
        except Exception as e:
            print(f"db_endgame error: {e}")
            self.cnx.rollback()

        query_endgame_players = (
            f"DELETE FROM {self.database}.{Config.PLAYER_TABLE} "
        )
        try:
            with self.cnx.cursor() as cursor_endgame:
                cursor_endgame.execute(query_endgame_players)
                self.cnx.commit()
                print(f"db_endgame success")
        except Exception as e:
            print(f"db_endgame error: {e}")
            self.cnx.rollback()

    def db_addplayer(self, new_member):
        """This function handles adding a new player to the game"""
        self.db_signup(new_member, Config.STATUS_ALIVE)
        # self.db_playerStatusUpdate(new_member, Config.STATUS_ALIVE)

    def db_swapplayer(self, existing_member, new_member):
        """This functions handles swapping out an old member for a new member"""
        self.db_playerStatusUpdate(existing_member, Config.STATUS_REPLACED, new_member)
        self.db_addplayer(new_member)

    def db_changegamethread(self, new_game_thread):
        """This function is used to swap the game text channel to another text channel"""
        print("db_changegamethread called")
        query_change_game_thread = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET game_channel_id = %s, game_channel_name = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_change_game_thread:
                cursor_change_game_thread.execute(query_change_game_thread, (str(new_game_thread.id),
                                                                             new_game_thread.name,
                                                                             str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_changegamethread success!")
        except Exception as e:
            print(f"db_changegamethread error: {e}")
            self.cnx.rollback()

    def db_changevotethread(self, new_vote_thread):
        """This function is used to swap the game text channel to another text channel"""
        print("db_changevotethread called")
        query_change_vote_thread = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET vote_channel_id = %s, vote_channel_name = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_change_vote_thread:
                cursor_change_vote_thread.execute(query_change_vote_thread, (str(new_vote_thread.id),
                                                                             new_vote_thread.name,
                                                                             str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_changevotethread success!")
        except Exception as e:
            print(f"db_changevotethread error: {e}")
            self.cnx.rollback()

    def db_changeplayerlistthread(self, new_playerlist_thread):
        """This function is used to swap the game text channel to another text channel"""
        print("db_changeplayerlistthread called")
        query_change_playerlist_thread = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET playerlist_channel_id = %s, playerlist_channel_name = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_change_game_thread:
                cursor_change_game_thread.execute(query_change_playerlist_thread, (str(new_playerlist_thread.id),
                                                                             new_playerlist_thread.name,
                                                                             str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_changeplayerlistthread success!")
        except Exception as e:
            print(f"db_changeplayerlistthread error: {e}")
            self.cnx.rollback()

    def db_original_playerlist_message(self, message: discord.Message):
        """This function takes a message representing the original playerlist and stores the message id"""
        query_original_playerlist_messsge = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET playerlist_original_msg_id = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_original_playerlist_messsge:
                cursor_original_playerlist_messsge.execute(query_original_playerlist_messsge,
                                                           (str(message.id), str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_changeplayerlistthread success!")
        except Exception as e:
            print(f"db_changeplayerlistthread error: {e}")

    def db_updated_playerlist_message(self, message: discord.Message):
        """This function takes a message representing the original playerlist and stores the message id"""
        print("db_updated_playerlist_message called")
        query_updated_playerlist_message = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET playerlist_updated_msg_id = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_original_playerlist_messsge:
                cursor_original_playerlist_messsge.execute(query_updated_playerlist_message,
                                                           (str(message.id), str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_updated_playerlist_message success!")
        except Exception as e:
            print(f"db_updated_playerlist_message error: {e}")

    def db_changeday(self, new_day_number):
        """This function is used to change the current day"""
        print("db_changeday called")
        query_db_change_day = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET day_number = %s, vote_count_number = 1 "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_change_day:
                cursor_change_day.execute(query_db_change_day, (new_day_number, str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_changeday success!")
        except Exception as e:
            print(f"db_changeday error: {e}")
            self.cnx.rollback()

    def db_votecount(self):
        """This method handles updating the votecount number when votecount is called"""
        print("db_votecount called")
        query_vote_count = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET vote_count_number = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_vote_count:
                cursor_vote_count.execute(query_vote_count, (Config.vote_count_number, str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_votecount success!")
        except Exception as e:
            print(f"db_votecount error: {e}")
            self.cnx.rollback()

    def db_changedaylength(self, new_day_length):
        """This function is used to change the Config.global_day_length setting in the database."""
        print("db_changedaylength called")
        query_change_day_length = (
            f"UPDATE {self.database}.{Config.CONFIG_TABLE} "
            f"SET global_day_length_in_seconds = %s "
            f"WHERE guild_id = %s"
        )
        try:
            with self.cnx.cursor() as cursor_change_day_length:
                cursor_change_day_length.execute(query_change_day_length, (new_day_length, str(Config.guild.id)))
                self.cnx.commit()
                print(f"db_changedaylength success!")
        except Exception as e:
            print(f"db_changedaylength error: {e}")
            self.cnx.rollback()

    "==============================================================================================="
    "============================Non-Functional WIP Code Below======================================"
    "==============================================================================================="


    def getQueryConfigurations(self):
        """This function should get all rows in the Configurations table"""
        return

    def getQueryPlayers(self):
        """This function should get all rows in the Players table"""
        return
