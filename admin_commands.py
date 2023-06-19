import discord
from discord.ext import commands
import config

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startsignup(self, ctx):
        # Your code here ...

def setup(bot):
    bot.add_cog(AdminCommands(bot))
