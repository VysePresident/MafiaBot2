import discord
from discord.ext import commands
import time as t
import asyncio
import collections

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

bot = commands.Bot(command_prefix="%", intents=discord.Intents.all())

# Import Config and Cogs. These are added in the on_ready() event listener.

from config import Config

from admin_commands import AdminCommands
admin_commands = AdminCommands(bot)

from player_commands import PlayerCommands
player_commands = PlayerCommands(bot)

@bot.event
async def on_ready():
    await bot.add_cog(admin_commands)
    await bot.add_cog(player_commands)

    if bot.get_channel(1110103139065012244):
        channel = bot.get_channel(1110103139065012244)
        await channel.send('Bot is online!')
    else:
        print("Mustard")

@bot.command()
async def votecount(ctx, in_channel_request=True, vote_change=None):
    if in_channel_request is not True and in_channel_request is not False:
        await ctx.send("You specified the wrong number of parameters, foolish mortal!  Try again or taste my wrath!")
        return
    count = collections.OrderedDict()
    votes_required = len(Config.signup_list)//2 + 1

    # Construct vote count for each player voted.  Should automatically be in order.
    for voter, voted in Config.votes.items():
        if voted in count:
            count[voted].append(voter)
        else:
            count[voted] = []
            count[voted].append(voter)

    # Construct message string
    votecount_message = f"**Vote Count {Config.day_number}.{Config.vote_count_number} - **{ctx.message.jump_url}\n\n"
    endDay = False
    for voted, voters in count.items():
        remaining_votes = votes_required - len(voters)  # The number of votes remaining for a lynch
        lynch_status = '**LYNCH**' if remaining_votes == 0 else f"L-{remaining_votes}"
        voters_str = ', '.join([voter.name if voter is not Config.prev_vote[0] else f'**{voter.name}**' for voter in voters])
        votecount_message += f"{voted.name}[{lynch_status}] - {voters_str}\n"
        if lynch_status == '**LYNCH**':
            endDay = True
        if voted is vote_change:
            await Config.game_channel.send(f"{voted.name} is {lynch_status}")
    not_voting = [player for player in Config.signup_list if player not in Config.votes.keys()]
    if len(not_voting) > 0:
        votecount_message += f"\nNot Voting - {', '.join([player.name if player is not Config.prev_vote[0] else f'**{player.name}**' for player in not_voting])}"
    else:
        votecount_message += f"\nNot Voting - (None)"
    if isinstance(Config.prev_vote[1], str):
        votecount_message += f"\n\n__Change__: *{Config.prev_vote[0].name} switched from {Config.prev_vote[1]} to {voted.name}*"
    else:
        votecount_message += f"\n\n__Change__: *{Config.prev_vote[0].name} switched from {Config.prev_vote[1].name} to {voted.name}*"
    votecount_message += f"\n\n*With {len(Config.signup_list)} alive, it takes {votes_required} to lynch.*"
    votecount_message += "\n" + "-" * 40
    if endDay:
        # await bot.get_command("kill").callback(ctx, voted)
        await kill(ctx, voted)
        votecount_message += f"\n\n**{voted.name} has been removed from the game**"
        votecount_message += f"\n\n**Night {Config.day_number+1} begins now!**"
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        await Config.game_channel.set_permissions(alive_role, send_messages=False)
        await Config.game_channel.send("The day has ended with a lynch.")
    if in_channel_request:
        await ctx.send(votecount_message)
    else:
        await Config.vote_channel.send(votecount_message)
    if vote_change is not None and vote_change not in count:
        await Config.game_channel.send(f"{vote_change.name} has zero votes")
    if in_channel_request:
        Config.vote_count_number += 1
    return


@commands.command()
# @commands.has_permissions(Administrator=True)
async def kill(ctx, member: discord.Member):
    if member.name in Config.live_players:
        Config.live_players.remove(member.name)
        Config.signup_list.remove(member)
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        dead_role = discord.utils.get(ctx.guild.roles, name="Dead")
        if dead_role is None:
            dead_role = await ctx.guild.create_role(name="Dead")
        if alive_role in member.roles:
            await member.remove_roles(alive_role)
        if dead_role not in member.roles:
            await member.add_roles(dead_role)
        await ctx.send(f"{member.name} has been removed from the game.")
    else:
        await ctx.send(f"{member.name} is not in the game or already removed.")

# ROLE RELATED COMMAND
"""@bot.command()
async def roleinfo(ctx, *, role: str):
    role = role.lower()
    if role not in roles:
        await ctx.send('That role cannot be found. Try googling "(rolename) mafiascum wiki".')
    else:
        role_info = roles[role]
        await ctx.send(f'**{role.capitalize()}**\n{role_info["description"]}\n\n**Alignment:** {role_info["alignment"]}\n\n**Special Abilities:** {role_info["special_abilities"]}')
"""

# ROLE RELATED COMMAND
"""
@bot.command()
async def rolelist(ctx):
    formatted_roles = [role.capitalize() for role in roles]
    await ctx.send("**Displaying normal roles:**\n" + '\n'.join(formatted_roles))
"""

"""
@bot.command()
@commands.has_permissions(administrator=True)
async def addplayer(ctx, new_player: discord.Member):
    alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
    if new_player not in Config.signup_list:
        Config.signup_list.append(new_player)
        await new_player.add_roles(alive_role)
        Config.live_players.append(new_player.name)
        await ctx.send(f'{new_player.name} has been added to the game!')
    else:
        await ctx.send(f'{new_player.name} is already in the game!')
"""

# Command is not used yet.  Review later.
"""
async def periodic_votecount_check():
    while True:
        if Config.vote_since_last_count >= 10:
            # Reset the counter
            Config.vote_since_last_count = 0
            # Call the votecount method (assumes it takes no arguments, modify as needed)
            await votecount()
        # Sleep for 10 seconds before checking again
        await asyncio.sleep(10)
"""

#bot.loop.create_task(periodic_votecount_check())

# TEST BOT KEY!
bot.run(bot_token)



"""from player_commands import perform_player_action
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
    bot.run(MTExMDA5NjEwNDEwMTUzMTc0OA.GJLsEp.jLmTauJrCUZQ8uH4LJkEs0tDSLVLXC9Q9nb7mE)"""
