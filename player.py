"""
Author: Geo
Date: July 29th, 2023

This module is used to host the Player class, which stores Player information. Currently, it only tracks
a limited number of features, including vote, status, and member.  In the future, it should also track
role info, alignment, and post count to assist the corresponding future modules we hope to add.
"""


import discord
from config import Config


class Player:
    def __init__(self, member: discord.Member, status, signup_number=None, vote=Config.NOT_VOTING):
        self.member = member  # Store Discord Info
        self.status = status  # Is the player Alive/Dead/Inactive/Replaced/Modkilled?  Inactive = signups before game.
        # self.vote = vote  # Storing vote seems unnecessary at present time.
        self.signup_number = signup_number  # For use when kicking a player who has left the server.

        # WIP - Toggleable configurations
        self.give_spoilers_on_death = False  # WIP - Allow as an optional configuration in the future.

        # Currently unused - for use in helping mods check for prods & for post limiting
        self.total_posts = 0  # Track the total posts of the player_to_remove over the course of the game - low use
        self.recent_posts = 0  # Track the posts of the player_to_remove within a set time period - typically 24 IRL hours.
        self.phase_posts = 0  # Track the posts of the player_to_remove within the Day Phase.

        # Currently unused - for use when automating flips.
        self._role = None
        self._alignment = None

    # WIP - Non-functional
    def unvote(self):
        """Better place to store unvote function?"""

    # WIP - function to kill the player. To replace bot's kill(). Admin modkill() should be a wrapper to call this.
    async def kill(self):
        """This function is intended to remove a player from the game while the game is active"""
        print(f"player.kill has been called on {self.member.display_name}")
        print(f"Member {self.member.display_name} has status: {self.status}")
        if self.member in Config.signup_list and self.status == Config.STATUS_ALIVE:
            Config.signup_list.pop(self.member)

            # Set Roles
            alive_role = discord.utils.get(Config.game_channel.guild.roles, name="Alive")
            dead_role = discord.utils.get(Config.game_channel.guild.roles, name="Dead")
            if dead_role is None:
                dead_role = await Config.game_channel.guild.create_role(name="Dead")
            if alive_role in self.member.roles:
                await self.member.remove_roles(alive_role)

            # Unvote:
            prev_vote = None
            current_vote = None
            voter = None
            if self.member in Config.votes:
                prev_vote = Config.votes.pop(self.member)
                current_vote = Config.NOT_VOTING
                voter = self.member
                await Config.game_channel.send(f"{self.member.display_name} has unvoted {prev_vote.display_name}.")

            # Finish the kill
            Config.dbManager.db_kill(self.member)

            self.status = Config.STATUS_DEAD
            if dead_role not in self.member.roles:
                print(f"!!!KILL SANITY CHECK!!!: {self.member.name} should receive DEAD role")
                # await member.add_roles(dead_role)  # To be added back later
            await Config.game_channel.send(
                f"{self.member.display_name} has been removed from the game. "
                f"NOTE: Dead role must be added manually for now")

            return prev_vote, current_vote, voter

    def display(self):
        """This function displays members attributes"""

        print(f"this is self.member.display_name: {self.member.display_name}")
        print(f"this is self.status: {self.member.status}")
        print(f"this is self.signup_number: {self.singup_number}")
        print(f"this is self.vote.display_name: {self.vote.display_name}")

    def displayPlayerName(self):
        """This function returns the player member's display_name"""
        return self.member.display_name

    # WIP - Used when adding a player to the game. Status/Role = Alive & add to Config.player_list
    async def activate(self):
        """The player is placed into the game."""
        self.status = Config.STATUS_ALIVE

        alive_role = discord.utils.get(Config.game_channel.guild.roles, name="Alive")
        if alive_role is None:
            alive_role = await Config.game_channel.guild.create_role(name="Alive")
        await self.member.add_roles(alive_role)

        Config.player_list[self.member] = Config.signup_list[self.member]

        Config.dbManager.db_playerStatusUpdate(self.member, self.status)
        return

    "==============================================================================================="
    "============================Non-Functional WIP Code Below======================================"
    "==============================================================================================="

    # WIP - Non-functional
    def modkill(self):
        """A harsher version of a regular kill."""
        """Player becomes Survivor and is considered to have lost the game."""
        self.vote = None  # remove vote
        self.status = Config.STATUS_DEAD  # Set status to Dead
        self._role = "Survivor"
        self._alignment = Config.ALIGNMENT_3RD_PARTY

    # WIP - Non-functional
    def setRole(self, roleName):
        """Set a player's role & alingnment  Might expand to setting Spec/Spoiler privileges"""

    # WIP - Non-functional
    def rateLimitPosts(self, target):

        """Set member's server role to one affected by slow mode"""
        """Note that this only works when we have safeguards preventing deletion of others' posts"""
        """Discord is stupid and won't give perms to bypass slow mode directly"""
        """You either have manage message permissions or nothing at all."""

    # WIP - Non-functional
    def sendRolePm(self):
        """Send the player_to_remove's role PM to them privately.  Should be accessible with a command"""

    # WIP - Non-functional
    def confirmRolePM(self, role, alignment):
        """Require the player_to_remove to confirm their role and alignment to the bot"""

    # WIP - Non-functional
    def roleReveal(self):
        """When the player_to_remove dies, reveal their role.  May also be accessed directly by Innocent Child?"""
        # I'm concerned that allowing an Innocent Child direct access might lead to removing niche gambits.

    # WIP - Non-functional
    def flipRole(self):
        """Reveal the player's role and alignment.  Should be called by a %flip @player_to_remove command"""

    # WIP - Non-functional
    def giveThread(self):
        """Allow a member to create a private thread for their thoughts"""
        """Disinclined to implement this, but leaving it in the structure for now"""
        """The bot would need to police against @ing people in some way."""