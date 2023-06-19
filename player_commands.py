import discord
from discord.ext import commands
import config

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def signup(self, ctx):
        # Your code here ...

def setup(bot):
    bot.add_cog(PlayerCommands(bot))
