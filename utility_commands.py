import discord
from discord.ext import commands
import config

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(1110103139065012244)
        await channel.send('Bot is online!')

def setup(bot):
    bot.add_cog(Events(bot))
