"""
Author: Geo
Date: July 29th, 2023

This module hosts the DatabaseManager class. This class handles setting up the database connection
and storing/retrieving info for functions in other modules.

Methods in this class take the form "db_functionName()" where functionName is equivalent to the
function/method name for which it is acting as a proxy between that function and the DB.
"""

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

    def connect(self):
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
        """else:
            print("Database connection CLOSED")
            self.cnx.close()"""

    def close(self):
        print(f"Attempting to close connection!")
        if self.cnx:
            self.cnx.close()
            self.cnx = None
            print("Connection closed!")
        print("No Connection to close!")

    # NOTES
    # Minimal thought on return values
    # Need to check if each configuration value is accurately stored
    # Need to check if players and votes are accurately fixed.
    # Need to check if end of phase is set to the right time.
    # You also used an async function in this class
    def setConfigurations(self):
        """Reset the configurations channel"""

        # Check connection
        if not self.cnx:
            self.connect()
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

        # Restore from DB only if active game exists
        if active_game and self.cnx:
            for (guild_id, host_id, signups_open, vote_channel_id, game_channel_id, phase_length_in_seconds, phase_end_time, phase_number, vote_count_number) in cursorConfig:
                # channel_info = (guild_id, host_id, vote_channel_id, game_channel_id)

                # Get the game and vote channels given guild_id
                Config.guild = discord.utils.get(self.bot.guilds, id=guild_id)
                if not Config.guild:
                    print("Guild not found!")
                Config.game_channel = discord.utils.get(Config.guild.channels, id=game_channel_id)
                if not Config.game_channel:
                    print("Game channel not found!")
                Config.vote_channel = discord.utils.get(Config.guild.channels, id=vote_channel_id)
                if not Config.vote_channel:
                    print("Vote channel not found!")
                Config.host = discord.utils.get(Config.guild.members, id=host_id)
                if not Config.host:
                    print("Host not found!")

                # Retrieve other configurations
                print("Storing channel_info")
                Config.signups_open = signups_open
                print(f"Set Config.signups_open: {Config.signups_open} signups_open: {signups_open}")
                Config.day_end_time = phase_end_time
                print(f"Set Config.day_end_time: {Config.day_end_time} phase_end_time: {phase_end_time}")
                Config.day_number = phase_number
                print(f"Set Config.day_number: {Config.day_number} phase_number: {phase_number}")
                Config.global_day_length = ((phase_length_in_seconds / 60) / 60) / 24
                print(f"Set Config.global_day_length: {Config.global_day_length} phase_length_in_seconds: {phase_length_in_seconds}")
                Config.vote_count_number = vote_count_number
                print(f"Set Config.vote_count_number: {Config.vote_count_number} vote_count_number: {vote_count_number}")

                seconds_remaining = phase_end_time - t.time()
                print(f"There are currently {seconds_remaining} seconds_remaining in the phase.")
                Config.day_end_task_object = self.bot.loop.create_task(self.end_day_after_delay(seconds_remaining))

            # Set up players and votes
            cursorPlayers = self.cnx.cursor(buffered=True)
            queryPlayers = (
                f"SELECT * FROM {self.database}.Players"
            )
            cursorPlayers.execute(queryPlayers)
            i = 0
            for index, (signup_number, player_id, vote_id, player_status) in enumerate(cursorPlayers, start=1):
                if index != signup_number:
                    print("UNEXPECTED BEHAVIOR! index != signup_number")
                member = discord.utils.get(Config.guild.members, id=player_id)
                voted = Config.NOT_VOTING
                if vote_id != Config.NOT_VOTING:
                    voted = discord.utils.get(Config.guild.members, id=vote_id)
                # member, status, signup_number, vote(defaults to not voting)
                player = Player(member, player_status, signup_number, voted)
                print(f"Adding player number {signup_number}: {player.member.display_name} to signup_list roster!")
                Config.signup_list.append(player.member)
                Config.players.append(player)
                # Log the vote and make sure it's stored correclty
                print(f"Player {player.member.display_name} voted for "
                      f"{voted.display_name if voted != Config.NOT_VOTING else voted}")
                Config.votes[player.member] = voted

            # return channel_info, player_info
            cursorConfig.close()
            cursorPlayers.close()
            return "SUCCESS"
        return "UNNEEDED"

    async def end_day_after_delay(self, phase_length_in_seconds):
        new_day_length = phase_length_in_seconds
        Config.day_end_time = t.time() + new_day_length
        try:
            await asyncio.sleep(new_day_length)
            alive_role = discord.utils.get(Config.game_channel.guild.roles, name="Alive")
            await Config.game_channel.set_permissions(alive_role, send_messages=False)
            await Config.game_channel.send("The day has ended due to time running out.")
            return
        except asyncio.CancelledError:
            print("Day phase time limit canceled!")

    def db_startsignup(self, guild_id, signups_open, game_host_id):
        """This function stores the host_id, guild_id, and signups_open state after signups are opened"""
        """This function is considered to 'create' the game.  It can only be opened once at a time."""
        # Create cursor and query
        query_start_signups = (
            f"INSERT INTO {self.database}.{Config.CONFIG_TABLE} (guild_id, signups_open, host_id) "
            f"VALUES (%s, %s, %s)"
        )
        try:
            with self.cnx.cursor() as cursor_start_signups:
                cursor_start_signups.execute(query_start_signups, (str(guild_id), signups_open, str(game_host_id)))
                self.cnx.commit()
            print("startsignup data stored!")
        except Exception as e:
            print(f"startsignup error occurred: {e}")
            self.cnx.rollback()

    def db_signup(self, signup_number, player_id, vote_id, status):
        """Store a player's info after they join."""
        vote = ''
        if vote_id == Config.NOT_VOTING:
            vote = None
        else:
            vote = vote_id
        if vote == '':
            print(f"ERROR db_forcesignup: vote == '' somehow")
        query_forcesignup = (
            f"INSERT INTO {self.database}.{Config.PLAYER_TABLE} (signup_number, player_id, vote_id, status)"
            f"VALUES (%s, %s, %s, %s)"
        )
        try:
            with self.cnx.cursor as cursor_forcesignup:
                cursor_forcesignup.execute(query_forcesignup, (signup_number, player_id, vote_id, status))
                self.cnx.commit()
                print("forcesignup data stored!")
        except Exception as e:
            print(f"forcesignup error occurred: {e}")
            self.cnx.rollback()

    def db_unforcesignup(self, signup_number, player_id, vote_id, status):
        """Remove a player from the Players table of the database"""




    def getQueryConfigurations(self):
        """This function should get the Configurations table"""
        return

    def getQueryPlayers(self):
        """This function should get the Players table"""
        return
