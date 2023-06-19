from player_commands import perform_player_action
from admin_commands import perform_admin_action
from utility_commands import get_time, get_date
from settings import initialize_settings

bot = commands.Bot(command_prefix="%", intents=discord.Intents.all())
bot.remove_command('help')

bot.load_extension("player_commands")
bot.load_extension("admin_commands")
bot.load_extension("utility_commands")
bot.load_extension("helper_functions")
bot.load_extension("settings")

if __name__ == "__main__":
    bot.run(MTExMDA5NjEwNDEwMTUzMTc0OA.GJLsEp.jLmTauJrCUZQ8uH4LJkEs0tDSLVLXC9Q9nb7mE)
