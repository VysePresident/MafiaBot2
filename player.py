import discord
from config import Config

class Player:
    def __init__(self, member: discord.Member, status):
        self.member = member  # Store Discord Info
        self.name = member.name  # Stores member name as a backup when killing a player who has left the server.
        self.status = status  # Is the player Alive or Dead?
        self.vote = None  # This might not be worth using - it's more convenient having a dictionary for the VC.
        self.give_spoilers_on_death = False  # WIP - Allow as an optional configuration in the future.

        # Currently unused - for use in helping mods check for prods & for post limiting
        self.total_posts = 0  # Track the total posts of the user over the course of the game - low use
        self.recent_posts = 0  # Track the posts of the user within a set time period - typically 24 IRL hours.
        self.phase_posts = 0  # Track the posts of the user within the Day Phase.

        # Currently unused - for use when automating flips.
        self._role = None
        self._alignment = None

    def activate(self):
        """The player is placed into the game."""
        self.vote = None  # remove vote if it exists.
        self.status = Config.STATUS_ALIVE  # Set status to Alive
        self.setRole(self._status)

    def kill(self):
        """The player receives the Dead role and can no longer interact with the game"""
        self.vote = None  # remove vote
        self.status = Config.STATUS_DEAD  # Set status to Dead
        # if self.give_spoilers = True, give the Spoilers role on Death.  # To be added later

    def modkill(self):
        """A harsher version of a regular kill."""
        """Player becomes Survivor and is considered to have lost the game."""
        self._vote = None  # remove vote
        self._status = Config.STATUS_DEAD  # Set status to Dead
        self._role = "Survivor"
        self._alignment = Config.ALIGNMENT_3RD_PARTY

    # WIP
    def setRole(self, roleName):
        """Set a player's role & alingnment  Might expand to setting Spec/Spoiler privileges"""

    # WIP
    def rateLimitPosts(self, target):

        """Set member's server role to one affected by slow mode"""
        """Note that this only works when we have safeguards preventing deletion of others' posts"""
        """Discord is stupid and won't give perms to bypass slow mode directly"""
        """You either have manage message permissions or nothing at all."""

    # WIP
    def sendRolePm(self):
        """Send the user's role PM to them privately.  Should be accessible with a command"""

    # WIP
    def confirmRolePM(self, role, alignment):
        """Require the user to confirm their role and alignment to the bot"""

    # WIP
    def roleReveal(self):
        """When the user dies, reveal their role.  May also be accessed directly by Innocent Child?"""
        # I'm concerned that allowing an Innocent Child direct access might lead to removing niche gambits.

    # WIP
    def flipRole(self):
        """Reveal the player's role and alignment.  Should be called by a %flip @user command"""

    # WIP
    def giveThread(self):
        """Allow a member to create a private thread for their thoughts"""
        """Disinclined to implement this, but leaving it in the structure for now"""
        """The bot would need to police against @ing people in some way."""