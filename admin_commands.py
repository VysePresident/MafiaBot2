import discord
from discord.ext import commands
import config

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.signup_list = []

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startsignup(self, ctx):
        global signups_open
        signups_open = True
        signup_list.clear()
        await ctx.send('Sign ups are open! Sign up for the game by doing %signup')

def setup(bot):
    bot.add_cog(AdminCommands(bot))
