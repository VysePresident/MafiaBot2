from bot import MafiaBot

bot_token = ''
try:
    from aso_key_file_name import mysterious_key_of_power
    print("Main key imported")
    bot_token = mysterious_key_of_power
except ImportError:
    try:
        from test_token import test_token
        bot_token = test_token
        print("Test bot key imported")
    except ImportError:
        bot_token = ''
        print("All imports failed.  Using blank key")

bot = MafiaBot(command_prefix="%", token=bot_token)

@bot.event
async def on_ready():

    await bot.load_extension("admin_commands")
    await bot.load_extension("player_commands")

    if bot.get_channel(1110103139065012244):
        channel = bot.get_channel(1110103139065012244)
        await channel.send('Bot is online!')
    print("Bot is online")

@bot.command()
async def reloadext(ctx):
    await bot.reload_extension("admin_commands")
    await bot.reload_extension("player_commands")

bot.run(bot_token)