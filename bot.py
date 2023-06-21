import discord
import os
from discord.ext import commands
import time as t
import asyncio
import collections
from datetime import datetime, timedelta

bot = commands.Bot(command_prefix="%", intents=discord.Intents.all())

# Game Setup
signups_open = False # Pregame
vote_channel = None
game_channel = None
global_day_length = 1
day_end_time = 1

# Game Status
day_number = 0
signup_list = [] # Pre & Mid
vote_count_number = 1
# votes = {}
votes = collections.OrderedDict()
prev_vote = None
live_players = []
vote_since_last_count = 0
start_time = datetime.now()

# Post count collection
post_counts = collections.defaultdict(lambda: collections.defaultdict(int))

@bot.event
async def on_ready():
    if (bot.get_channel(1110103139065012244)):
        channel = bot.get_channel(1110103139065012244)
        await channel.send('Bot is online!')
    else:
        print("Mustard")

@bot.command()
async def startsignup(ctx):
    global signups_open
    signups_open = True
    signup_list.clear()
    await ctx.send('Sign ups are open! Sign up for the game by doing %signup')
    
@bot.command()
@commands.has_permissions(administrator=True)
async def forcesignup(ctx, user: discord.Member):
    global signups_open
    if user not in signup_list:
        signup_list.append(user)
        await ctx.send(f'{user.name} has been signed up.')
    else:
        await ctx.send(f'{user.name} is already signed up.')

@bot.command()
@commands.has_permissions(administrator=True)
async def unforcesignup(ctx, user: discord.Member):
    global signups_open
    if user in signup_list:
        signup_list.remove(user)
        await ctx.send(f'{user.name} has been removed from the signup list.')
    else:
        await ctx.send(f'{user.name} is not on the signup list.')

@bot.command()
async def signup(ctx):
    global signups_open
    if signups_open:
        if ctx.author not in signup_list:
            signup_list.append(ctx.author)
            await ctx.send(f'Thank you for signing up, {ctx.author.name}!')
        else:
            await ctx.send(f'You have already signed up, {ctx.author.name}!')
    else:
        await ctx.send('Sign ups are currently closed.')
        
@bot.command()
async def unsignup(ctx):
    global signups_open
    if ctx.author in signup_list:
        signup_list.remove(ctx.author)
        await ctx.send(f'You have been removed from the sign up list, {ctx.author.name}!')
    else:
        await ctx.send(f'You are not on the sign up list, {ctx.author.name}!')

@bot.command()
async def signuplist(ctx):
    if not signup_list:
        await ctx.send('No one has signed up yet.')
    else:
        signups = "\n".join([user.name for user in signup_list])
        await ctx.send(f'The current signups are:\n{signups}')
        
@bot.command()
async def startgame(ctx, game_channel_param: discord.TextChannel, vote_channel_param: discord.TextChannel, day_length: int = 1):
    global signups_open, game_channel, vote_channel, global_day_length, live_players, votes
    global_day_length = day_length
    if not signups_open:
        await ctx.send('Signups are currently closed.')
        return
    if not signup_list:
        await ctx.send('No one has signed up yet.')
        return
    signups_open = False
    game_channel = game_channel_param
    vote_channel = vote_channel_param
    if game_channel is None or vote_channel is None:
        await ctx.send('One or both channels are incorrect.')
        return
    alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
    if alive_role is None:
        alive_role = await ctx.guild.create_role(name="Alive")
    for user in signup_list:
        member = ctx.guild.get_member(user.id)
        if member is not None:
            await member.add_roles(alive_role)
            live_players.append(member.name)
    game_players = "\n".join([user.mention for user in signup_list])
    await game_channel.send(f'The game has started with the following players:\n{game_players}')
    
    vote_message = await vote_channel.send(f'Day {day_number+1} votes will be displayed here. Required votes to eliminate a player: {len(signup_list)//2 + 1}')
    
    await newday.callback(ctx, day_length)

@bot.command()
async def vote(ctx, voted: discord.Member):
    global votes, game_channel, prev_vote
    if ctx.author not in signup_list or voted not in signup_list:
        await ctx.send("Either the voter or the voted player is not in the game.")
        return
    if ctx.author in votes and votes[ctx.author] == voted:
        await ctx.send("You've already voted for this player.")
        return
    if ctx.channel != game_channel:
        await ctx.send("You can only vote in the game chat.")
        return
    # votes[ctx.author] = voted

    # TEST
    if ctx.author in votes:
        prev_vote = (ctx.author, votes.pop(ctx.author))
    votes[ctx.author] = voted
    # END TEST

    # await ctx.send(f"{ctx.author.name} has voted for {voted.name}.")
    await ctx.send(f"{ctx.author.name} has voted for {votes[ctx.author].name}.") # TEST
    await bot.get_command("votecount").callback(ctx = ctx, in_channel_request=False)

@bot.command()
async def unvote(ctx):
    global votes, game_channel, prev_vote
    if ctx.channel != game_channel:
        await ctx.send("You can only vote in the game chat.")
        return
    if ctx.author in votes:
        # del votes[ctx.author]
        prev_vote = (ctx.author, votes.pop(ctx.author)) # TEST
        await ctx.send(f"{ctx.author.name} has unvoted.")
        await bot.get_command("votecount").callback(ctx = ctx, in_channel_request=False)
    # if ctx.channel != game_channel:
    #    await ctx.send("You can only vote in the game chat.")
    #    return
    else:
        await ctx.send("You haven't voted yet.")

# CORRECTED VOTECOUNT TEST
@bot.command()
async def votecount(ctx, in_channel_request=True):
    if in_channel_request is not True and in_channel_request is not False:
        await ctx.send("You specified the wrong number of parameters, foolish mortal!  Try again or taste my wrath!")
        return
    global day_number, vote_count_number, vote_channel, game_channel, prev_vote
    count = collections.OrderedDict()
    votes_required = len(signup_list)//2 + 1
    # Construct vote count for each player voted.  Should automatically be in order.
    for voter, voted in votes.items():
        if voted in count:
            """print("This is gate 1")
            print("This is count[voted]: ")
            print(count[voted])
            print("")"""
            count[voted].append(voter)
        else:
            count[voted] = []
            count[voted].append(voter)
            """print("This is gate 2")
            print("This is count[voted]: ")
            print(count[voted])
            print("")"""
    # Construct message string
    votecount_message = f"**Vote Count {day_number}.{vote_count_number}**\n\n"
    endDay = False
    for voted, voters in count.items():
        remaining_votes = votes_required - len(voters)  # The number of votes remaining for a lynch
        lynch_status = '**LYNCH**' if remaining_votes == 0 else f"L-{remaining_votes}"
        voters_str = ', '.join([voter.name for voter in voters])
        votecount_message += f"{voted.name}[{lynch_status}] - {voters_str}\n"
        if lynch_status == '**LYNCH**':
            endDay = True
    not_voting = [player for player in signup_list if player not in votes.keys()]
    votecount_message += f"\nNot Voting - {', '.join([player.name for player in not_voting])}"
    votecount_message += f"\n\n*With {len(signup_list)} alive, it takes {votes_required} to lynch.*"
    votecount_message += "\n" + "-" * 40
    if endDay:
        await bot.get_command("kill").callback(ctx, voted)
        votecount_message += f"\nKilling {voted.name}"
        alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
        await game_channel.set_permissions(alive_role, send_messages=False)
        await game_channel.send("The day has ended with a lynch.")
    if in_channel_request:
        await ctx.send(votecount_message)
    else:
        await vote_channel.send(votecount_message)
    vote_count_number += 1
    return


# OLD ATTEMPT
"""@bot.command()
async def votecount(ctx=None):
    global day_number, vote_count_number, vote_channel, game_channel, prev_votes
    count = collections.OrderedDict()
    votes_required = len(signup_list)//2 + 1
    for voter, vote_info in votes.items():
        # voted = vote_info['voted'] # Extract the user voted for
        voted = vote_info
        if voted in count:
            count[voted].append(voter)
        else:
            count[voted] = [voter]
    votecount_message = f"**Vote Count {day_number}.{vote_count_number}**\n\n"
    for voted, voters in count.items():
        remaining_votes = votes_required - len(voters)  # The number of votes remaining for a lynch
        lynch_status = '**LYNCH**' if remaining_votes == 0 else f"L-{remaining_votes}"
        voters_str = ', '.join([f"[{voter.name}]({votes[voter]['link']})" if prev_votes.get(voter) != votes[voter]['voted'] else voter.name for voter in voters])
        votecount_message += f"{voted.name}[{lynch_status}] - {voters_str}\n"
        if lynch_status == '**LYNCH**':
            await bot.get_command("kill").callback(ctx, voted)
            votecount_message += f"\nKilling {voted.name}"
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            await game_channel.set_permissions(alive_role, send_messages=False)
            await game_channel.send("The day has ended with a lynch.")
    not_voting = [player for player in signup_list if player not in votes.keys()]
    votecount_message += f"\nNot Voting - {', '.join([player.name for player in not_voting])}"
    votecount_message += f"\n\n*With {len(signup_list)} alive, it takes {votes_required} to lynch.*"
    votecount_message += "\n" + "-"*40
    if ctx:
        await ctx.send(votecount_message)
    else:
        await vote_channel.send(votecount_message)
    vote_count_number += 1

    # Update the prev_votes dictionary at the end
    prev_votes = {voter: {'voted': vote_info['voted']} for voter, vote_info in votes.items()}"""

@bot.command()
async def newday(ctx, day_length: int = 1):
    global day_number, vote_count_number, votes, day_end_time, global_day_length, vote_channel, game_channel
    day_length = global_day_length
    day_number += 1
    vote_count_number = 1
    votes = {}

    alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
    await game_channel.set_permissions(alive_role, send_messages=True)

    votecount_message = f"**Vote Count {day_number}.{vote_count_number}**\n\nNo votes yet."
    await vote_channel.send(votecount_message)

    await game_channel.send(f"Day {day_number} has begun. It will end in {day_length} days.")
    day_end_time = t.time() + day_length * 24 * 60 * 60
    bot.loop.create_task(end_day_after_delay(day_length))
    
async def end_day_after_delay(day_length):
    global game_channel
    await asyncio.sleep(day_length * 24 * 60 * 60)
    alive_role = discord.utils.get(game_channel.guild.roles, name="Alive")
    await game_channel.set_permissions(alive_role, send_messages=False)
    await game_channel.send("The day has ended due to time running out.")

@bot.command()
async def time(ctx):
    global day_end_time
    if day_end_time is None:
        await ctx.send("The game hasn't started yet.")
    else:
        time_remaining = day_end_time - t.time()
        if time_remaining <= 0:
            await ctx.send("The day has ended.")
        else:
            hours, rem = divmod(time_remaining, 3600)
            minutes, seconds = divmod(rem, 60)
            await ctx.send(f"Time remaining: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")
            
@bot.command()
async def endgame(ctx):
    global current_day
    global votes
    global global_day_length
    current_day = 0
    votes = {}
    global_day_length = 1
    await ctx.send("The game has ended.")
    
@bot.command()
async def kill(ctx, member: discord.Member):
    global live_players
    if member.name in live_players:
        live_players.remove(member.name)
        signup_list.remove(member)
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
        
@bot.command()
async def playerlist(ctx):
    alive_players = []
    dead_players = []
    for member in ctx.guild.members:
        if discord.utils.get(member.roles, name="Alive"):
            alive_players.append(member.name)
        elif discord.utils.get(member.roles, name="Dead"):
            dead_players.append(member.name)
    if not alive_players:
        alive_players.append("No players alive.")
    if not dead_players:
        dead_players.append("No players dead.")
    await ctx.send(f"Alive players:\n{' '.join(alive_players)}\n\nDead players:\n{' '.join(dead_players)}")

@bot.command()
async def roleinfo(ctx, *, role: str):
    role = role.lower()
    if role not in roles:
        await ctx.send('That role cannot be found. Try googling "(rolename) mafiascum wiki".')
    else:
        role_info = roles[role]
        await ctx.send(f'**{role.capitalize()}**\n{role_info["description"]}\n\n**Alignment:** {role_info["alignment"]}\n\n**Special Abilities:** {role_info["special_abilities"]}')

@bot.command()
async def rolelist(ctx):
    formatted_roles = [role.capitalize() for role in roles]
    await ctx.send("**Displaying normal roles:**\n" + '\n'.join(formatted_roles))
    
@bot.command()
@commands.has_permissions(administrator=True)
async def addplayer(ctx, new_player: discord.Member):
    global signup_list, live_players
    alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
    if new_player not in signup_list:
        signup_list.appent(new_player)
        await new_player.add_roles(alive_role)
        live_players.append(new_player.name)
        await ctx.send(f'{new_player.name} has been added to the game!')
    else:
        await ctx.send(f'{new_player.name} is already in the game!')

@bot.command()
@commands.has_permissions(administrator=True)
async def swapplayer(ctx, existing_player: discord.Member, new_player: discord.Member):
    global signup_list, live_players
    if existing_player in signup_list:
        if new_player not in signup_list:
            index = signup_list.index(existing_player)
            signup_list[index] = new_player
            if existing_player.name in live_players:
                live_players.remove(existing_player.name)
            live_players.remove(new_player.name)
            alive_role = discord.utils.get(ctx.guild.roles, name="Alive")
            await existing_player.remove_roles(alive_role)
            await new_player.add_roles(alive_role)
            await(f'{existing_player.name} has been replaced with {new_player.name}.')
        else:
            await(f'{new_player.name} is already in the game.')
    else:
        await ctx.send(f'{existing_player.name} is not in the game.')
        
async def changedaylength(ctx, *args):
    global global_day_length
    day_length_in_seconds = 0
    for arg in args:
        if arg[-1] == 'd':
            day_length_in_seconds += int(arg[:-1]) * 60 * 60 * 24
        elif arg[-1] == 'h':
            day_length_in_seconds += int(arg[:-1]) * 60 * 60
        elif arg[-1] == 'm':
            day_length_in_seconds += int(arg[:-1]) * 60
        else:
            await ctx.send(f'Invalid time format: {arg}. Will only accept these: "d/h/m".')
    global_day_length = day_length_in_seconds / (24*60*60)
    await ctx.send(f'The day length has been changed to {global_day_length} days.')
    
async def periodic_votecount_check():
    global vote_since_last_count
    while True:
        if vote_since_last_count >= 10:
            # Reset the counter
            vote_since_last_count = 0
            # Call the votecount method (assumes it takes no arguments, modify as needed)
            await votecount()
        # Sleep for 10 seconds before checking again
        await asyncio.sleep(10)
        
#bot.loop.create_task(periodic_votecount_check())



# Repository of Roles (RoR)
roles = {
    'alien': {
        'description': 'An Alien can "abduct" a target each night, making them immune to night actions, but incapable of performing actions themselves.',
        'alignment': 'Any',
        'special_abilities': 'An Aliens night action targets a player, attempting to prevent any night action made by that player, and any night action (other than the Aliens) targeting that player. (Factional kills are night actions, and are blocked the same way that any other night action would be.) The role therefore acts identically to a Combined Roleblocker Rolestopper. \n\nActions blocked by an Alien normally cannot succeed. However, actions that are specifically capable of piercing blocking effects, such as a Strongmans kill, will still take place. \n\nIf an action is blocked by an Alien, this has all the same consequences as if the action were blocked by a Roleblocker, i.e. X-Shot actions still lose a shot, investigative actions cannot (typically) see the blocked action, investigative roles will get no results (and if this leads to them not getting a results PM when they expected one, will get a no result PM telling them this). \n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Alien_(role)',
        },
    'ascetic': {
        'description': 'An Ascetic is a player who is immune to all actions at Night except kills; in effect, the player is permanently rolestopped.',
        'alignment': 'Any',
        'special_abilities': 'An Ascetic role cannot be targeted by anything other than a kill. A role attempting to target an Ascetic should be seen doing so by Trackers and Motion Detectors, even though they would not be seen if they were directly roleblocked. Investigative roles (Cops, Role Cops, Watchers, etc.) should receive "no result" if attempting to investigate an Ascetic role.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Ascetic',
        },
    'babysitter': {
        'description': 'A Babysitter is a role who can target a player at Night to protect them. However, if Babysitter is killed that night, both the Babysitter and its target will die.',
        'alignment': 'Town',
        'special_abilities': 'A Babysitter may target a player each night to protect them. That player will be protected from one kill aimed at that player directly. However, if a kill succeeds on the Babysitter (rather than the Babysitters target), the Babysitters target will die along with the Babysitter.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Babysitter',
        },
    'bodyguard': {
        'description': 'A Bodyguard is a role who can target a player at Night to protect them. However, if the protected player is supposed to be killed, the Bodyguard is killed instead ("taking the bullet" for them, as it were).\nBodyguard only protects from a single kill. If multiple people try to kill the Bodyguards target, both the Bodyguard and the protected player will die.\nBodyguard is usually Town. It makes little sense for there to be a Mafia Bodyguard, as they have no reason to target anyone except a scumpartner; and a Vigilante who finds that their kill resolved on a different scum than they expected can simply shoot their previous target again.',
        'alignment': 'Any',
        'special_abilities': 'A Bodyguard that protects their target from one kill is considered Normal on mafiascum.net. A Bodyguard cannot stop a Strongman from committing a kill, nor a Weak role from dying due to targeting anti-town. Protection would also fail if targeting a Macho or Ascetic role, although the Bodyguard should not be told if this happens, just like if they were blocked. Bodyguards do not redirect the kill, so a Tracker tracking the killer will still see the killer targeting the Bodyguards target.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Bodyguard',
        },
    'bulletproof': {
        'description': 'Bulletproof is a passive role that allows a player to avoid being killed at Night.',
        'alignment': 'Any',
        'special_abilities': 'The most common (and Normal) version of Bulletproof causes a player to be immune to any nightkill made by any faction; Vigilantes will not be able to kill the bulletproof player, and nor will a factional kill. It protects players even if multiple kills target them on the same night. It has no effect against eliminations.\n\nAs a passive role, Bulletproofing cannot be roleblocked (by a Normal Roleblocker; Bulletproofing is not immune to Theme roles designed to block passives). However, the protection is not absolute: roles which specifically pierce kill prevention, such as the Strongman, can kill a Bulletproof player.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Bulletproof',
        },
    'checker': {
        'description': 'A Checker is a player who can target a player, learning whether their action was a success. It has no direct effect on the targeted player; it thus serves as an investigation to determine whether something is interfering with the Checkers actions.',
        'alignment': 'Any',
        'special_abilities': 'Each night, a Checker may choose one other player to target. If the attempt to target the player succeeds, the Checker will be informed that it succeeded. As with most actions, a Checker action does nothing if blocked, if it targets an Ascetic player, etc., but the Checker will be able to determine that something went wrong from the lack of a result PM (the moderator sends a no result PM to let the Checker know that their action failed).\n\nExample Checker results include "You checked target" and "Your action failed, and you did not receive a result"; in other words, a Checker is in effect an investigative role that produces no useful information about the target.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Checker',
        },
    'commuter': {
        'description': 'The Commuter is a role that "leaves Town" each Night, thus making them ineligible to be targeted by Night actions. By extension, they cannot use any other Night actions they may have.\nBecause they cannot use Night actions, almost all Commuters are pro-Town.\nIt is worth noting that because in flavor it physically leaves the game for the Night instead of being protected somewhere in Town, Commuter is considered the ultimate in Untargetability, trumping even things like Strongman.',
        'alignment': 'Town',
        'special_abilities': 'Most Commuters cannot Commute each Night. Instead, they generally have Odd-Night or Even-Night modifiers attached.\n\nAlternatively, they may be X-Shot and need to choose if they want to Commute each Night.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Commuter',
        },
    'cop': {
        'description': 'A Cop (or in Werewolf flavour, Seer) is a role that has the ability to investigate players at Night to discern their alignment.',
        'alignment': 'Any',
        'special_abilities': 'The standard, Normal, variation of a Cop can investigate one player each Night; the target is not informed of the investigation. This Cop variant will return results of the form "Town" or "Not Town" (regardless of whether it is named "Cop" or "Seer"; both names are acceptable in a Normal); it cannot distinguish between players who belong to different anti-town and third-party factions.\n\nThe results will be "reliable", i.e. guaranteed to be accurate unless some other players power role interferes with the investigation. If the action is blocked entirely (e.g. by a Roleblocker or due to investigating an Ascetic player), the Cop will get a no result PM (which is distinct from the "Town" and "Not Town" results). However, some roles which interfere with Cop results (such as Miller) will outright produce misleading results (e.g. a Cop will get a "Not Town" result on a Town Miller); interference from a deceptive role is the only way in which the standard variant of a Cop can produce incorrect or misleading results.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Cop',
        },
    'deputy': {
        'description': 'A Deputy is a flavor name for a Backup Cop. Once a Cop has died, the Deputy will become an ordinary Cop (the flavor logic being that the Deputy steps up to replace the deceased Cop). The Deputy may or may not be self-aware (if not, they will receive a Vanilla Townie Role PM). Occasionally a self-aware Deputy is called a Retired Cop.\nThis role does not necessarily make any guarantee about the existence of a Cop in the setup to begin with. If there is no Cop, this role is effectively a Named Townie. On the other hand, if there are multiple Cops in the setup, the Deputy will traditionally inherit the sanity of the first deceased Cop.\nThis role is virtually always pro-Town.\nThis version of Deputy, and only this version of Deputy, is considered Normal on mafiascum.net.',
        'alignment': 'Town',
        'special_abilities': 'Mafiascum Link: https://wiki.mafiascum.net/index.php?title=Deputy',
        },
    'detective': {
        'description': 'A Detective is an investigative role that determines whether a player has killed another player, either on the night it is used or on a previous night.\nThe differences from Gunsmith and Rolecop, which are somewhat related roles, are mostly in connection with how it interacts with groupscum; a member of a scumgroup may have the ability to kill, but prefer to allow one of their allies to kill instead. The role is also rather related to the Follower, who can also detect a kill, but only on the night that the Follower is following; a Detective can see kills on previous nights too, but cannot see actions other than kills.\nThe opposite of this role, detecting players who have unused kills, is a Psychologist.\nThe standard version of a Detective can only see kills intentionally performed using active abilities: the factional kill, a Vigilante shot, or the like.',
        'alignment': 'Town',
        'special_abilities': 'The Detective is a valid Normal Town role to be used in Normal Games.\n\nIn a Normal Game, a Detective may choose to investigate each night. Only three results can be obtained from this investigation: Negative, Positive, or No Result. This investigation resolves after any killing abilities in the Night phase.\n\nA negative result is returned from players that have never attempted to kill another player (including players who cannot kill, and players who can kill but chose not to).\n\nA positive result is returned from players that have actively killed another player, or attempted to kill another player but failed. This would include a Vigilante or a mafia member, but would not include players who could cause a player to die indirectly as a result of their action, such as a Babysitter or a Weak role.\n\nAs usual, No Result is returned if the Detectives own action was blocked, e.g. by a Roleblocker or by an Ascetic modifier on their target.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Detective',
        },
    'doctor': {
        'description': 'A Doctor protects players from being killed overnight. Each Doctor protection cancels out one kill.',
        'alignment': 'Any',
        'special_abilities': 'Each night, a Doctor chooses a player to protect. The standard (and only Normal) version of a Doctor cannot target themself. If a player is protected, they become immune to one kill performed by normal means (e.g. a Mafia or Werewolf factional kill, a Vigilante shot, or a Serial Killers inherent kill can all be prevented by a Doctor).\n\nIf a player is targeted by multiple kills, a single Doctor will not be enough to save them; a number of Doctor protections equal to the number of kills is required. Additionally, some special types of death, such as those caused by a Strongmans kill or by a Weak role backfiring, cannot be stopped by Doctor protection; and of course, if the Doctors action itself fails as a consequence of a Roleblocker or comparable role, it will not protect its target. Additionally, a Doctors protection will have no effect on a Macho player.\n\nAs with most roles, Doctors do not have any inherent knowledge of whether their role has operated or not; if the Doctors target survives, the Doctor cannot tell whether their target wasnt targeted for a kill, or whether they were killed but saved; likewise, if a Doctor is roleblocked, they wont be told that this is the case (unless some other players role tells them).\n\nIn Mafia hands, the Doctor role has an additional, unrelated effect: a Mafia Doctor kills without the use of a gun, and thus a Gunsmith will not see a gun when investigating a Mafia Doctor. (This effect does not occur if a Mafia member gains access to a Doctor action via some other means, e.g. a Jack of All Trades role.)\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Doctor',
        },
    'enabler': {
        'description': 'An Enabler has no active abilities, but must stay alive to allow another player to use their abilities. An Enabler is linked to a specific role; if the Enabler dies, all players who have that role will lose it.',
        'alignment': 'Any',
        'special_abilities': 'An Enabler is linked to a specific role (such as Doctor), not types of role (such as protective); the Normal version of an Enabler is self-aware (and knows which role they enable). When the Enabler dies, all players lose the role that they are linked to, e.g. the death of a Doctor Enabler will cause every Doctor in the game (and every JOATs Doctor ability) to become useless.\n\nThere is no requirement that the role being Enabled actually exists within the game.\n\nEnabler is a modular role similar to Finder. Cop Enabler and Doctor Enabler are valid roles but Enabler isnt. However, a Doctor Enabler is not a Doctor since Enabler is not considered a modifier (and thus wont allow Nurses to back up or show up as not having a gun if Mafia-aligned to Gunsmiths).\n\nhttps://wiki.mafiascum.net/index.php?title=Enabler',
        },
    'encryptor': {
        'description': 'An Encryptor is a role that allows people who can converse with it to talk during the Day phase. This is used in games where private communication is normally restricted to the Night phase.',
        'alignment': 'Any',
        'special_abilities': 'Any private topics containing an Encryptor have daytalk. This is even the case if an Encryptor ends up in a private topic by accident (e.g. if a town-aligned player neighbourises a Mafia Encryptor, the resulting neighbourhood will have daytalk until the Encryptor dies). Encryptors can be of any alignment.\n\nIn Normal Games on mafiascum.net, Mafia do not need an Encryptor to have daytalk, but if they have it without an Encryptor it needs to be announced beforehand.\n\nhttps://wiki.mafiascum.net/index.php?title=Encryptor',
        },
    'finder': {
        'description': 'A [role]-Finder, or Finder, is a investigative role that learns whether someone is a specific power role or not. For example, a Cop-Finder has results of "Cop" and "Not Cop". Modifiers and other parts of roles are not considered, so a Cop-Finder will get results of "Cop" on a Cop, a Macho Cop, or a Fruit Vendor Cop.',
        'alignment': 'Any',
        'special_abilities': 'Mafiascum Link: https://wiki.mafiascum.net/index.php?title=Finder',
        },
    'follower': {
        'description': 'The Follower is an informative role that can target a player at Night and learn what form of action they took that Night (investigation, protection, killing, etc), but not who they targeted.\nFollower can be of either alignment.',
        'alignment': 'Any',
        'special_abilities': 'Mafiascum Link: https://wiki.mafiascum.net/index.php?title=Follower',
        },
    'friendly neighbor': {
        'description': 'A Friendly Neighbor can target a player at Night to tell them that they are Town. The target will receive a message saying that the Friendly Neighbor is Town. This role does nothing else - the Friendly Neighbor does not know the alignment of the person who got the message.\nFriendly Neighbor bears no association with the Neighbor role.\nFriendly Neighbor is necessarily Town-aligned.',
        'alignment': 'Town',
        'special_abilities': 'Town-aligned Friendly Neighbor is considered Normal on mafiascum.net. Messages sent on behalf of a Friendly Neighbor must be identical.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Friendly_Neighbor',
        },
    'fruit vendor': {
        'description': 'A Fruit Vendor is a role that may hand out fruit to a player at night. The player they choose is informed that they received a piece of fruit.',
        'alignment': 'Any',
        'special_abilities': 'A Fruit Vendor will hand out a piece of fruit to a player at night. The player that they target is informed that they received a piece of fruit (but not who sent it to them). The fruit has no effect, other than informing the recipient that it exists.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Fruit_Vendor',
        },
    'goon': {
        'description': 'A Mafia Goon is a member of the Mafia who has no abilities beyond the regular Mafia factional abilities. Basically Marino.',
        'alignment': 'Mafia, Werewolf',
        'special_abilities': 'A Mafia Goon is a vanilla member of the Mafia. This means that they have all the abilities that a Mafia member would normally possess, but no abilities beyond that. In most games, these abilities include knowledge of who the other Mafia members are, the ability to communicate with them overNight (and sometimes during the Day too), and the ability to kill one player each night as long as no other Mafia member is performing the kill.\n\nIf a Goon is scanned by a Role Cop or similar role, the Role Cop will receive a "vanilla" result (not "Goon"). Likewise, Mafia Goons show as vanilla to a Vanilla Cop, can be affected by Simple roles but not Complex roles, and so on.\n\nA Goon inherently cannot be given any role modifiers or any additional roles whilst remaining a Goon – that would, by definition, make them not vanilla. For example, modifying a Mafia Goon to be Bulletproof would produce a Bulletproof Mafioso, not a "Bulletproof Mafia Goon"; the latter name is self-contradictory.\n\nIn a Normal game, there is no way for a Goons role to change. However, Goons are not inherently resistant to becoming non-vanilla; role-changing roles like Inventor can grant Goons extra actions as easily as they could grant actions to anyone else.\n\nMafiascum link: https://wiki.mafiascum.net/index.php?title=Goon',
        },
    'gunsmith': {
        'description': 'The Gunsmith is an information role that can target a player at Night to learn if they have a gun in flavor. Members of the Mafia (that are not Doctors), Cops, FBI Agents, Vigilantes, other Gunsmiths, Paranoid Gun Owners, etc. all have guns in traditional flavor. Notably, Serial Killers and Doctors do not have guns.\nGunsmiths are usually, but not necessarily, pro-Town. They are considered somewhat weaker than standard Cops and are usually included in setups where they can get positive results on players who are not Mafia-aligned.\nFor more information, see Cop and Flavor Cop.',
        'alignment': 'Any',
        'special_abilities': 'Mafiascum Link: https://wiki.mafiascum.net/index.php?title=Gunsmith',
        },
    'hider': {
        'description': 'The name "Hider" describes a set of closely related roles. Each of them are active roles in which the user flavourfully "hides behind" the target of their night choice, typically making the user less vulnerable to actions used directly on them, but more vulnerable to their target and people attacking their target. However, the details vary by version.',
        'alignment': 'Any',
        'special_abilities': 'The Normal version of the Hider is one of the simplest: the Hider, when they use their ability, cannot be killed by actions targeted at them; however, if their target dies as a result of an active killing action (e.g. a factional kill or Vigilante shot), the Hider will also die.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Hider',
        },
    'informed': {
        'description': 'An Informed player is a player who is given additional information about the setup at the start of the game (in the Role PM), most commonly the identity of another townie or the existence of a particular power role.',
        'alignment': 'Any',
        'special_abilities': 'This role gives the player information about the setup (pregame, or with timing determined by a role modifier), and is considered Normal on mafiascum.net provided the information given is objective and accurate. The information can be any information about the setup, but should be non-random with regards to what player-slot is being referred to. For example, if someone is to be told that a player is town, it should be noted in the setup specification that the player they are told is town is a randomly chosen vanilla townie, or a specific power role, and not just a randomly chosen town player.\n\nInformed roles should flip with only their role name, and not any private information; an Informed role is effectively an investigative role whose investigation happens passively and automatically, with the actual information being the "investigation result". An Informed Townie should therefore flip simply as "Informed Townie" (with a redacted role PM, if role PMs are included in flips). Similarly, a Rolecop would only see "Informed", and would not get to see the information itself.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Informed',
        },
    'innocent child': {
        'description': 'An Innocent Child is a player who can be mod-confirmed as Town-aligned.\nObviously, Innocent Child is always Town.',
        'alignment': 'Town',
        'special_abilities': 'Innocent Child is considered Normal on mafiascum.net. Usually, the confirm-upon-request version is used, although the other variations are acceptable.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Innocent_Child',
        },
    'inspector': {
        'description': 'An Inspector is an investigative role that targets a player each night, and will learn if the other player was targeted by another action or not. It is an easily confounded variation of a Watcher - they only learn if someone has been targeted or not, like the second half of the Motion Detector.',
        'alignment': 'Any',
        'special_abilities': 'Each Night, an Inspector may choose a player to inspect. If their action succeeds, they will know if their target has been targeted by anyone else or not. Actions taken by a Ninja are ignored for this purpose, and the Inspector will produce the same results as if the Ninjas actions did not occur.\n\nInspectors will only know if their target was targeted by someone else or not, they will not know who or what targeted their target.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Inspector',
        },
    'jack of all trades': {
        'description': 'The Jack-of-all-trades, commonly abbreviated JOAT, is a role with several one-shot night abilities - typically abilities centered around investigating, protecting and killing. The Jack-of-all-trades may use whichever ability they want on a specific Night, but can use each one only once. This role has been seen as both Town and Mafia.\nThe "standard" JOAT is considered to be a one-shot Cop, one-shot Doctor, one-shot Vig, and one-shot Roleblocker. However, this exact model is uncommon in practice.\nThe Werewolf-flavored equivalent to JOAT is Witch. The Grand Vizier is similar except its abilities are not one-shot.',
        'alignment': 'Any',
        'special_abilities': 'As long as all of its one-shot component abilities are Normal, Jack of All Trades is considered Normal on mafiascum.net. It is officially an alias for a hybrid role consisting of multiple 1-shot roles. For example, Jack of All Trades (Cop, Doctor) and 1-shot Cop 1-shot Doctor are the same exact role.\n\nJack of All Trades is a modular role, however in an unusual case for a modular role a JOATs abilities actually count as being their base role.\n\nA Jack of All Trades must have at least two abilities.\n\nA JOAT should flip with all their abilities shown.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Jack-of-all-trades',
        },
    'jailkeeper': {
        'description': 'A Jailkeeper (or Jailer)s Night Action is one that protects its target from kills, but also Roleblocks its target. Unlike Doctor, Jailkeepers protection extends to stopping every kill that would resolve on the target by default.\nBecause it is a combination Doctor and Roleblocker, Jailkeeper has a myriad of uses while not allowing broken combinations or exactly confirming anyone as Town or scum. Thus, it has risen to prominence as a very popular power role.\nBecause it is a Roleblocker, Jailkeeper is never allowed to self-target.\nThis role is a non-bastard version of Cynical Doctor.',
        'alignment': 'Any',
        'special_abilities': 'A Jailkeeper that simultaneously blocks and protects their target is considered Normal on mafiascum.net, provided that any mutual blocking scenarios are planned for during review. Any role that receives results (such as Tracker or Watcher) but is blocked as a result of being targeted by a Jailkeeper should receive a "no result" message, rather than told their target didnt go anywhere or nobody visited their target. A Jailkeeper cannot stop a Strongman from committing a kill (regardless of who they target), and does not prevent other players from targeting their target with non-killing actions (e.g. if a Watcher and Jailkeeper target the same player, the Watcher will see the Jailkeepers action).\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Jailkeeper',
        },
    'macho': {
        'description': 'Macho is a role modifier that prevents players from being protected from kills in any way.\nThe modifier was first developed as a way to neutralise Follow the Cop strategies that exist in Cop/Doctor set-ups, preventing the Cop from gaining the Doctors protection. Macho Cop is still the most common role associated with this modifier, but other roles have used it for balance and design reasons.',
        'alignment': 'Any',
        'special_abilities': 'This role modifier is considered Normal on mafiascum.net. It negates the effects of any roles that would prevent it from death such as a Doctor or Bodyguard protecting it, although both would still be seen as having visited a Macho role.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Macho',
        },
    'mafia': {
        'description': 'This article describes the in-game faction Mafia, which gives its name to the Game of Mafia (if youre looking for information about the game, rather than the faction, follow that link).',
        'alignment': 'Mafia',
        'special_abilities': 'The Mafia faction is one of the two major factions in a typical game of Mafia (their main opponents are the Town). The Mafia faction is an informed minority; the Mafia are small in numbers compared to the Town, but are given additional information and abilities to compensate.\n\nThe standard version of a Mafia faction has three factional abilities, in addition to the abilities that would be available to any player in the game.\n\n- This role was too long and went over Discords character limit, so Ive simply cleared this. If you wish to view the role just look at the Mafiascum page.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Mafia',
        },
    'mailman': {
        'description': 'A Mailman (or Courier or Messenger) is a role that can send a message to other players at Night, via the moderator.',
        'alignment': 'Any',
        'special_abilities': 'As their Night Choice, a Mailman chooses a message to send, and a player to send it to. At the end of the Night, the moderator will then send the message to the player in question. There is no word limit on the message, but it must be a single message.\n\nMailman messages should be formatted in such a way as to make it clear that the message comes from a Mailman and is not mod-confirmed information. However, the author should not be confirmed by the moderator either (its legal for a player to claim an identity in the message, but also to lie about their identity in the message).\n\nMessenger is an official alias for Mailman. You may call this role Messenger in Normal Games in any context.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Mailman',
        },
    'mason': {
        'description': 'Masons are a group of players who can speak to each other privately and know that everyone in their group is not a member of the Mafia.',
        'alignment': 'Not-Mafia',
        'special_abilities': 'The Mason role has generated a fair amount of controversy and a few offshoots. Be sure you ask the moderator what precisely it means to be a Mason, as all of the below have been known to simply be called "Mason".\n\nMasons are fully confirmed to not be members of the Mafia. However, in Theme or Open games, this confirmation does not always apply to other anti-town alignments; sometimes a Werewolf will be allowed into a masonry, even though the Mafia are absolutely excluded.\n\nA Monk is a faction-flipped version of a Mason, giving absolutely confirmation that there are no Werewolves in the monastery, but potentially allowing the possibility of Mafia.\n\nDespite the name "Mason" implying an absolute confirmation that the members are not Mafia-aligned, some moderators have been known to put Mafia members into a masonry anyway, with the role only implying a high confidence in the alignment of the masonry members (more than with a Neighbour). It may be worth asking the moderator how absolute the confirmation provided by a masonry is meant to be. (In an extreme case, if the game is advertised as bastard mod, the odds of scum in the masonry is probably rather higher than 50:50!)\n\nThe term for players who know each other to be Town but are unable to speak to each other privately is Best Friends, though this has fallen into disuse.\n\nTo contrast, the standard term for players who do not know each others alignments but can speak to each other privately is Neighbors. (This means that a Mason is effectively an Informed Neighbor.)\n\nThere is nothing sacred about the Masons being forced to talk at Night only; allowing Masons to speak at all times raises their effectiveness somewhat.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Mason',
        },
    'miller': {
        'description': 'A Miller (sometimes called an Outsider) is a role or role modifier such that the player passively returns an unfavorable result (i.e. Guilty) if investigated by a Cop.\nFor obvious reasons, standard Millers are Town.',
        'alignment': 'Town',
        'special_abilities': 'Some moderators take the "passive guilt" concept to the point where Millers also investigate unfavorably to other roles (e.g. Gunsmith); this can be given a name like Universal Miller, although just plain "Miller" is also seen. Alternatively, specialized Millers can be created specifically for investigative roles other than Cop; for example, a Track Miller would always be seen, by a Tracker, as targeting the player that the Mafia (or whatever the "main" anti-Town faction in that game is) had attempted to kill.\n\nSometimes, a Miller may be unaware of their Miller state -- that part of their role is hidden from them. This is used in some Open setups (like C9++) to prevent the Miller from functioning like a Named Townie. An unaware Miller in a closed setup is sometimes considered bastardly, though.\n\nA rather controversial twist is the Death Miller, whose alignment is shown as "Mafia" by the Moderator upon death. This has been argued and discussed in Ethics Threads as a source of distrust in the Moderator, which most people feel should not be tolerated. Thus, the Death Miller is a particularly scarcely-used role even in bastard mod games.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Miller',
        },
    'motion detector': {
        'description': 'The Motion Detector, sometimes known as a variant of Reporter, is an informative role that can target a player at Night and learn if any actions were performed by or on that player, but not what the actions were or who else they involved.\nMotion Detectors can be of either alignment.',
        'alignment': 'Any',
        'special_abilities': 'A Motion Detector is considered Normal on mafiascum.net. A Motion Detector should receive the same result if they see an action being performed by their target as they would if they see an action being performed on their target (and the same if they see both). If their target is Ascetic or targeted by a Rolestopper, they should receive a "No Result" pm, the same as if theyd been blocked themselves. A Motion Detector would not see a Ninja performing a kill.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Motion_Detector',
        },
    'neapolitan': {
        'description': 'A Neapolitan is an informative role that can check one player per night to see whether or not they are a Vanilla Townie.\nWhile Neapolitans have utility for both Town and Mafia, they are more commonly assigned to Town.\nThe Neapolitan was created by Ether as a buff to the Vanilla Cop for Normal Games.',
        'alignment': 'Any',
        'special_abilities': 'A Neapolitan investigates a player to determine whether or not they are a Vanilla Townie. A Vanilla Townie will return a result of "target is a Vanilla Townie"; other players will give a result of "target is not a Vanilla Townie". If the action fails (e.g. due to a roleblocker), the result will be "Your action failed, and you did not receive a result".\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Neapolitan',
        },
    'neighbor': {
        'description': 'Neighbors are players that can speak to each other. Unlike Masons, there is no guarantee made of any Neighbors alignment. It is up to the moderators discretion whether they can only speak at night, or at any time.\nIn addition, Neighbors have been known to possess other power roles, or even have powers that belong to the group as a whole.\nSee also Neighborizer.',
        'alignment': 'Any',
        'special_abilities': 'Neighbors, regardless of when they are allowed to speak to each other, are considered Normal on mafiascum.net. A list of current members should be kept in the OP for neighborhood threads; if a moderator neglects to do this, players may ask the moderator what players are in a neighborhood. Under the current Normal guidelines, there are no restrictions on combining power roles, and Neighbors are no exception to this; in fact, Neighbors were exceptionally allowed to have additional power roles even under former rulesets in which combining power roles was disallowed.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Neighbor',
        },
    'neighborizer': {
        'description': 'A Neighborizer is a player who can target other players at Night to recruit them into a Neighborhood. They may begin speaking to each other at the end of the Night, or at the beginning of the next Night - it depends on whether the moderator allows the Neighbors to speak during the Day.\nNeighborizers are most often pro-Town. They usually do not have any Neighbors at the beginning of the game.',
        'alignment': 'Any',
        'special_abilities': 'A Neighborizer without any Neighbors at the start of the game is considered Normal on mafiascum.net. Any players added to a Neighborhood are added at the start of the next day, regardless of whether the Neighborizer lives or not, and their Role Name is not changed.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Neighborizer',
        },
    'nurse': {
        'description': 'Nurse is the flavor name for a Backup Doctor. Once a Doctor has died, the Nurse will become an ordinary Doctor. The Nurse may or may not be self-aware (if not, it will receive a Vanilla Townie Role PM).\nThis role makes no guarantee about the existence of a Doctor in the setup to begin with. If there is no Doctor, then this role is functionally a Named Townie at best. On the other hand, in a game with multiple Doctors, the Nurse will generally inherit the sanity or other quirks of the Doctor who died first.\nThis role is pro-Town most of the time.\nThe self-aware version of Nurse (receives a Nurse or Backup Doctor Role PM), and only this self-aware version of Nurse, is considered Normal on mafiascum.net.',
        'alignment': 'Any',
        'special_abilities': 'An older variant of Nurse also specifies that the Nurses protection has a lower chance of succeeding. Some variations on that run with that concept alone instead of requiring a Doctor to die before the Nurse can protect.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Nurse',
        },
    'psychologist': {
        'description': 'The Psychologist is an investigative role that determines a players ability to kill. It does however have a drawback: if a player has already killed, the Psychologist can no longer discern whether this player is capable of doing so.',
        'alignment': 'Town',
        'special_abilities': 'A Psychologist can investigate one player for unused kills each night. Only three results can be obtained from this investigation: Negative, Positive, or no result. This investigation resolves after any killing abilities in the Night phase.\n- A negative result is returned from players that are unable to actively kill another player, or on a player that has already killed.\n- A positive result is returned from players that can choose to kill, but have not done so.\n- The "no result" result is returned as a result of the action failing as a consequence of another role (e.g. a Roleblocker or Ascetic) interfering with it.\nRoles like Paranoid Gun Owner, who have passive kills, give negative results because they have no active kill. Likewise, a Mafia Traitor has no kill and thus will produce a negative result; a Vigilante will produce a positive result before it makes its first kill.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Psychologist',
        },
    'reporter': {
        'description': 'Reporter is a role that is an easily confounded variation of a Tracker. They only learn if someone has acted or not, like the first half of the Motion Detector.',
        'alignment': 'Any',
        'special_abilities': 'Each Night, a Reporter may choose a player to find out if they are home. If their action succeeds, they will know if their target has acted or not. Actions taken by a Ninja are ignored for this purpose, and the Reporter will produce the same results as if the Ninjas actions did not occur.\n\nReporters will only know if their target acted or not, they will not know how they acted.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Reporter',
        },
    'role cop': {
        'description': 'A Role Cop is an investigative role that learns the role of its target, e.g. "Cop", "Doctor", "Roleblocker", etc.. There is no indication of the targets alignment; if a Mafia Goon or Vanilla Townie is investigated, they return "Vanilla". Role Cops are actually a somewhat popular Mafia role, but have also been seen aligned with the Town.',
        'alignment': 'Any',
        'special_abilities': 'The Role Cops ability will let them learn their targets personal (i.e. not factional) abilities, in the form of a role name (or full role PM in the case where the role name would be nonstandard or unfamiliar). However, any alignment details and factional abilities are hidden; the Role Cop will see town-aligned and scum-aligned versions of the same role as identical. This is done by removing any faction-related and win-condition-related information from the role name (and role PM, if necessary) before posting it; "Town Roleblocker" and "Mafia Roleblocker" would just become "Roleblocker", and in a full role PM, the win condition, factional abilities, information about teammates, etc. would all be removed.\n\nVanilla players have role names that vary by faction; a Role Cop scanning these will get "Vanilla" as the response, again anonymising the win condition. Thus, a Mafia Goon or a Serial Killer should give the same result as a Vanilla Townie (unless they have extra abilities). The Role Cop sees the players role as of the start of the game; thus, in the case of an X-Shot role, the Role Cop would be told how many shots the role started with, not how many shots currently remain. Role Cops have no special ability to pierce protections against investigations, or role blocks; thus, trying to investigate an Ascetic role would return a failure message like "Your action failed, and you did not get a result".\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Role_Cop',
        },
    'role watcher': {
        'description': 'A Role Watcher is an investigative role that can target a player and learn what roles targeted that player. Role Watchers see roles, not actions, so if a Loyal Cop targets the person the Role Watcher targeted the Role Watcher will see that a Loyal Cop targeted the Role Watchers target; If a Doctor Fruit Vendor protected someone, this role would say that a doctor fruit vendor targeted them, but would not be able to tell whether they were protected or vended to. If multiple of the same role target the Role Watchers target, they will see each duplicated role. If a Vanilla player targets the Role Watchers target (possible with the factional kill), the Role Watcher will see that they were targeted by a Vanilla.',
        'alignment': 'Any',
        'special_abilities': 'A Role Watcher that learns what roles a player was targeted by during the night is considered Normal on mafiascum.net. If a Role Watcher is somehow blocked from their action (by Roleblocker, Jailkeeper, Rolestopper, Ascetic, or Commuter), they should receive a "No Result" pm, rather than a "did not see anything" pm. A Role Watcher would not see a Ninja committing a kill, however, and would receive a "did not see anything" pm in that case.\n\nA Role Watchers action can fail due to, e.g., a Roleblocker targeting them or an attempt to watch an Ascetic target; in these cases, the Role Watcher will be aware that their action has failed, and will receive a no result PM. This result should be clearly distinct from the result obtained when successfully role watching a player, but with no other actions on that player to role watch; a "no result" result leaves it unclear who if anyone targeted the Role Watchers target, whereas a "no actions" result guarantees that nobody else (other than a possible Ninja) targeted the Role Watchers target.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Role_Watcher',
        },
    'roleblocker': {
        'description': 'A Roleblocker chooses one player per Night to block from performing their night action. The targets night action will not be performed -- that is, the Roleblocker blocks the targets role from working. The role is very commonly seen as part of the Mafia, but can also be useful for the Town.',
        'alignment': 'Any',
        'special_abilities': 'A Roleblocker prevents their target using active roles (such as Cop investigations and Doctor protections). Passive abilities, such as a Bulletproof players kill immunity or a Masons ability to privately talk, are not affected. More simply - if the player has to submit an action to the moderator, a Roleblocker can block it.\n\nWhen an X-Shot role is blocked, the shot is not refunded; the player still counts as having "paid for" their role use, but the actual role is otherwise considered to not have happened (so, e.g., Trackers and Watchers will not be able to see the blocked role being used). The blocked player will not normally be told that they have been blocked (unless they used an investigative role and thus were expecting a results PM, in which case the moderator will let them know that their action failed). The blocked player will never receive misleading results, e.g. a blocked Tracker will get a result like "Your action failed, and you did not receive a result", and never something like "Your target went nowhere".\n\nA Roleblocker is trumped by roles that prevent someone being targeted at all - for example, a Roleblocker cannot block roles such as Ascetic or Commuter. A Strongman specifically pierces Roleblocker protection. Roleblocks can themselves be blocked; thus, for example, a Roleblocker cannot block someone who is under Rolestopper protection.\n\nThere is no consensus as to what happens when multiple roleblockers try to roleblock each other – the result will depend on the action resolution scheme in use. In Normal games, any potential such scenarios must be planned for during review (and doing so is a good idea in other games too).\n\nBy default, players cannot perform two actions at once, which is often an issue for a Mafia Roleblocker if they end up as the last remaining member of their faction. (This default can be changed using the Multitasking modifier.)',
        },
    'rolestopper': {
        'description': 'A Rolestopper is a role that can target a player to stop all other Night actions from affecting them in any way. This is something like the inverse of a Roleblocker. A Rolestopper effectively turns their target into an Ascetic Bulletproof for that night.\nRolestoppers can be of any alignment.',
        'alignment': 'Any',
        'special_abilities': 'Rolestoppers are considered Normal on mafiascum.net. A Rolestopper cannot block a Strongman from committing a kill, but blocks all other roles from targeting the same person as them. An investigative role targeting the same player as a Rolestopper should be given a "No Result" pm.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Rolestopper',
        },
    'security guard': {
        'description': 'A Security Guard is a role that may notify a player of whoever else targeted them. In effect, they are a Watcher that gives their results to their target.',
        'alignment': 'Any',
        'special_abilities': 'Each Night, a Security Guard may notify a player of whoever else targeted them. If their action succeeds, the Security Guards target will be given a list of other players whose night actions had the same target as the Security Guards targets. The list should make it clear it comes from a Security Guard. Actions taken by a Ninja are ignored for this purpose, and the Security Guard will give the same results as if the Ninjas actions did not occur.\n\nIf a Security Guards action fails, the Security Guards target will not get a results PM at all. This is different from the result a Security Guards target would get if the Security Guard was the only one to target them.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Security_Guard',
        },
    'serial killer': {
        'description': 'A Serial Killer is a player whose goal is to be the last player alive. They are aligned with themselves (meaning they have no allies) and have a factional kill at Night like the Mafia. Depending on the flavor, SKs may also be called Cannibals, Psychopaths, or Arsonists (note that Arsonist has since grown to describe a unique role).',
        'alignment': 'Serial Killer',
        'special_abilities': 'The Normal variant of a Serial Killer is as a self-aligned third party with no additional powers, other than a night kill. Other roles or modifiers can be added, however, but they are considered separate roles that are part of the role name and need to be shown when the SK flips.\n\nA Serial Killers kill is considered factional, so if investigated by a Role Cop or Vanilla Cop, SKs (with no further powers) should return a "Vanilla" result. Serial Killers traditionally kill with knives, so show up as not having a gun to a Gunsmith investigation - note that all deaths should still have the same generic Kill Flavor.\n\nThe presence of a Serial Killer can often keep a game going even at numbers that would normally lead another faction to win immediately (e.g. 1 Town, 1 Mafia, 1 Serial Killer going into the Night). As a general guideline, if a Serial Killer is still alive, the game should not be called over unless the Serial Killer has won or some groupscum faction controls more than half the votes in the game.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Serial_Killer',
        },
    'shield': {
        'description': 'A Shield is a role that may intercept a kill. If a Shield targets someone performing a kill, the Shield will instead take the kill.\nShield is usually Town. It makes little sense for there to be a Mafia Shield, as they have no reason to target anyone except a potential Vigilante; and a Vigilante who finds that their kill resolved on a different scum than they expected can simply shoot their previous target again.',
        'alignment': 'Any',
        'special_abilities': 'A Shield blocks their targets kill and dies instead of their targets target. A Shield cannot stop a Strongman from committing a kill, nor a Weak role from dying due to targeting anti-town.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Shield',
        },
    'strongman': {
        'description': 'Strongman is a role modifier that signifies that any kills performed by this player cannot be blocked by any means - neither by Bulletproof, nor by Doctor or other protective roles, nor by Roleblocks. It is, however, trumped by roles that prevent the victim from being targeted at all, namely Commuter and, in some open setups, Hider.\nStrongman is usually X-Shot. It is usually scum-aligned, but has been seen on Town Vigilantes as well (where the overall role is called Juggernaut).',
        'alignment': 'Any',
        'special_abilities': 'A Mafia or Serial Killer aligned Strongman is considered Normal on mafiascum.net. A Strongman cannot be stopped from performing a kill, unless their target has commuted. A Bodyguard would essentially be stopped from protecting against a kill and would not die.\n\nUnstoppable is an official alias for Strongman. You may call this role Unstoppable in Normal Games in any context.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Strongman',
        },
    'townie': {
        'description': 'A Townie (also known as Citizen, Townsperson, Villager, etc.) is a player with the Town Win Condition. The name suggests that the player has no extraordinary abilities (sometimes "Vanilla Townie", abbreviated as VT, is used to remove the ambiguity).',
        'alignment': 'Town',
        'special_abilities': 'The Town win condition is to eliminate all members of anti-town factions, most notably the Mafia, whilst retaining at least one living player (a Townie can win while dead as long as an ally survives to defeat the Towns enemies). The Town faction as a whole has no special abilities to work towards this; its only advantage is its numbers, typically outnumbering all other factions put together. Its members post and vote like anyone else during the Day, and cannot act at Night without the help of power roles.\n\n"Townie" is a role designation for a pro-Town role that has no active ability. Some passive roles, when given to a member of the Town, are typically named by modifying the name "Townie"; examples include the Ascetic Townie, Bulletproof Townie, and Informed Townie.\n\nThe colloquial name for a blank townie and the term used in Normal games is "Vanilla Townie" (i.e. just a vanilla Townie). Townie, Townsperson, Citizen are also permitted. A game cannot be considered Normal unless there is at least one VT-equivalent role in the game. A sample of a Vanilla Townie role PM must be provided in one of the opening posts of a Normal Game.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Townie',
        },
    'tracker': {
        'description': 'A Tracker is an investigative role that can target a player at Night and learn who, if anybody, that player targeted the same night (but not the action the player performed).',
        'alignment': 'Any',
        'special_abilities': 'Each Night, a Tracker can choose a player to track. At the end of the Night, they will learn who (if anyone) that player targeted. Actions performed by a Ninja do not show up on a Tracker report. Actions that did not occur because their user was roleblocked are considered to not have happened for tracking purposes, and do not show up on a Tracker report either; however, actions were blocked because their target was immune to actions (e.g. because the target was rolestopped or Ascetic) can be seen on a Tracker report.\n\nIf a Trackers action itself fails, it does not produce any results; the Tracker will get a "no result" PM. If the action succeeds, this produces a result that is clearly distinguishable from a "no result" PM (even if no actions were observed by the successful track); for example, a Tracker who is roleblocked might get a PM "Your action failed, and you did not receive a result", whereas a Tracker who tracks a Vanilla Townie might get a result of "Target did not target anybody last night".\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Tracker',
        },
    'traffic analyst': {
        'description': 'A Traffic Analyst is capable of checking whether or not a player is capable of private communication.',
        'alignment': 'Any',
        'special_abilities': 'A Traffic Analyst is an investigative role; its night choice is to choose a player, and the analyst will learn whether or not there are any players that that player can legally communicate with outside the game thread. (The identity of the people that the target can communicate with is not learned, nor is the content of the communications.)\n\nNote that merely having access to a private topic is not necessarily enough to be able to communicate; there will have to be a second living player in the private topic in question to communicate with. To be precise, the role will give a "can communicate" result on a player who shares a private topic with another living player, and also on roles that can use active roles to relay messages via the moderator (such as Mailman); and a "cannot communicate" result on anyone else. (In particular, a Neighborizer will give a "cannot communicate" result unless they have another living player in their private topic.)\n\nAs usual for investigative roles, there are three possible results, with no result being given if the Traffic Analysts action is blocked (this is a clearly distinct result from "cannot communicate").\n\nIn most action resolution methods (including Natural Action Resolution, which is used in Normals), this action will resolve later in the night than any kills; this means that if a player is killed overNight, that player will not show as being in a private topic on Traffic Analyst checks that night. (So for example, if one of a pair of Neighbors is nightkilled, a Traffic Analyst action used on the same night will return "cannot communicate".)\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Traffic_Analyst',
        },
    'traitor': {
        'description': 'A Traitor is a member of the Mafia who is separate from the main contingent of the faction. Because it is not a member of the main contingent, it is not capable of talking to the other Mafiosi and cannot perform the factional kill. Beyond this simple definition, the implementation of Traitor varies wildly between games.\nThis role is necessarily Mafia-aligned.',
        'alignment': 'Not-Town',
        'special_abilities': 'These are a few of the ways that Traitor has been implemented.\n- The Traitor may or may not know who is in the Mafia to begin with. If not, Traitor is basically intended to act like a "bad Townie" - whereas "good Townies" try to find scum, "bad Townies" hinder the Town from finding the scum without necessarily knowing who they are. However, it is considerably more common for the Traitor to know who the scum are.\n- On occasion the Traitor is only told who one of the scum is.\n- The Traitor may give negative results to Cops (that is, they show up like Townies would). This hearkens back to the earliest interpretation of the Traitor, called the Mafia Spy.\n- The Mafia Spy shows up as Town to Cops, but the Mafia can "call them back" at any time to make them full members of the Mafia at any time. (Obviously, the Mafia would know that the Mafia Spy exists.)\n- Some moderators allow for Mafia teams to kill their Traitors with the factional kill. Other times, the Traitor is immune to kills from their Mafia (in which case if the Mafia tries to kill them there is no kill that Night). Still other times, if the Mafia attempts to kill their Traitor the Traitor is instead recruited into the Mafia, allowing it to talk to the rest of the faction and perform the factional kill. All of these have been seen regularly.\n- If the Mafia can potentially kill their Traitor, they are sometimes told that a Traitor exists in the game. This forces the scum to hunt for their own Traitor in hopes of learning who NOT to kill at Night.\n- Some Traitors, particularly those that cannot be recruited into the main faction, are compensated by being granted extra powers. For instance, the Mafia Traitor may also be the teams Roleblocker.\n- Some Traitors lose if the main Mafia group is wiped out, even if they are still alive.\n- Some Traitors inherit the ability to nightkill if the rest of the scum are dead.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Traitor',
        },
    'universal backup': {
        'description': 'A Universal Backup is a player who inherits the ability of the first allied power role to die; as its name suggests, it is effectively a Backup that is not locked to backing up one particular role.',
        'alignment': 'Any',
        'special_abilities': 'Being a Universal Backup does not initially give a player any powers. However, as soon as a non-vanilla player belonging to the same faction as the Universal Backup dies, the Universal Backup becomes a copy of that player (losing their Universal Backup ability); they gain that players role, including any modifiers it has.\n\nIf the dying player had an X-Shot role, was a Jack of All Trades, or had a similar restriction on how often they could use their abilities, the spent abilities do not recharge when the Universal Backup inherits them; the Universal Backup will be told which shots were missing, and will not be able to use them themself. A Universal Backup does not, however, learn any information about how the inherited role was used; e.g. they wont know what targets it was used on, and wont learn any results that it gained.\n\nThe Normal version of a Universal Backup is self-aware, just like any other role in a Normal.\n\nIn a game where multiple kills are possible in a night, it is possible for multiple power roles to die in the same night; in this case, the Universal Backup inherits only one of them, and some decision will need to be made pre-game about which power role will be gained. When this problem has arisen in Normal games in the past, the usual ruling has been that the Universal Backup gains the role of the player who was killed by the Mafias factional kill.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Universal_Backup',
        },
    'vanilla cop': {
        'description': 'A Vanilla Cop is a lower-powered version of a Role Cop, as an investigative role that sees role information but not alignment information. The drawback is that the exact role is not specified – only whether or not a power role exists at all.',
        'alignment': 'Any',
        'special_abilities': 'A Vanilla Cops night action investigates players to see whether or not they are a vanilla of their faction. Vanilla Townies and Mafia Goons will return a "vanilla" result, as will Serial Killers who have no special abilities beyond their kill (i.e. no investigation immunity, bulletproofing, etc.). Any other player will return a "not vanilla" result.\n\nAs usual for investigative roles, there are three possible results: "vanilla", "not vanilla", and no result (which should be clearly distinct from a "not vanilla" result). The last of these occurs if the Vanilla Cops action fails, e.g. due to being roleblocked or trying to scan an Ascetic player.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Vanilla_Cop',
        },
    'vigilante': {
        'description': 'A Vigilante is a Townie who can kill a player at Night.\nUsing traditional flavors, Vigilantes share the "shot" kill flavor with the Mafia. Thus, their kills are indistinguishable from those of the Mafia in this case.\nWhile a few moderators prefer to defy meta and use Mafia Vigilantes to allow multiple scumkills from a single faction, the vast majority of Vigilantes are Town.',
        'alignment': 'Town',
        'special_abilities': 'There is no consensus as to whether "Vig" is pronounced with a hard "g" or like "Vidge". The easiest solution to this problem is to pronounce it however you like, but never try to make a pun out of "Vig" or try to verbally say it to others, unless you know how they pronounce the term.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Vigilante',
        },
    'visionary': {
        'description': 'A Visionary is a role that may grant a player visions of the other actions (protection, investigation, etc) that targeted them. In effect, they are a Voyeur that gives their results to their target.',
        'alignment': 'Any',
        'special_abilities': 'Each Night, a Visionary may notify a player of the types of actions that targeted them (other than the Visionarys action) according to Natural Action Resolution/Normal Game. If their action succeeds, the Visionarys target will be given a list of the types of actions that targeted them (except for the Visionarys action). The list should make it clear it comes from a Visionary. Actions taken by a Ninja are ignored for this purpose, and the Visionary will give the same results as if the Ninjas actions did not occur.\n\nIf a Visionarys action fails, the Visionarys target will not get a results PM at all. This is different from the result a Visionarys target would get if the Visionary was the only one to target them.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Visionary',
        },
    'visitor': {
        'description': 'A Visitor is a role that may visit a player each night. This action can be viewed by any Follower variant among other roles, but the action itself will have no effect upon its target.',
        'alignment': 'Any',
        'special_abilities': 'Visitor is a valid Normal role for any alignment. In a Normal Game, a Visitor may visit a player each night, but this will have no effect beyond visiting that player.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Visitor',
        },
    'voyeur': {
        'description': 'The Voyeur is an informative role that can target a player at night and learn what was done to them that night (protection, investigation, etc), but not who did it.\nVoyeurs can be of any alignment.',
        'alignment': 'Any',
        'special_abilities': 'A Voyeur is considered Normal on mafiascum.net, as long as it gives the results according to Natural Action Resolution/Normal Game. If a Voyeur is somehow blocked from their action (by Roleblocker, Jailkeeper, Rolestopper, Ascetic, or Commuter), they should receive a "No Result" pm, rather than a "did not see anything" pm. A Voyeur would not see a Ninja committing a kill, however, and would receive a "did not see anything" pm in that case.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Voyeur',
        },
    'watcher': {
        'description': 'A Watcher is an investigative role that targets a player each night, and will learn which other players performed Night actions on the same target. (They do not learn about the nature of those actions, only the user.)',
        'alignment': 'Any',
        'special_abilities': 'Each Night, a Watcher may choose a player to watch. If their action succeeds, they will be given a list of other players whose night actions had the same target as the Watchers. (In other words, the Watcher will learn about who targeted their target.) Actions taken by a Ninja are ignored for this purpose, and the Watcher will produce the same results as if the Ninjas actions did not occur.\n\nA Watchers action can fail due to, e.g., a Roleblocker targeting them or an attempt to watch an Ascetic target; in these cases, the Watcher will be aware that their action has failed, and will receive a no result PM. This result should be clearly distinct from the result obtained when successfully watching a player, but with no other actions on that player to watch; a "no result" result leaves it unclear who if anyone targeted the Watchers target, whereas a "no actions" result guarantees that nobody else (other than a possible Ninja) targeted the Watchers target.\n\nMafiascum Link: https://wiki.mafiascum.net/index.php?title=Watcher',
        },
    'werewolf': {
        'description': 'In Werewolf-themed games, a Werewolf is the equivalent of a Mafioso in Mafia-flavored games. Notably, some games have included Mafia and Werewolves as opposing anti-Town factions.\n\nOn particularly rare occasions, Werewolf has also been seen as a Cultafia role.',
        'alignment': 'Not-Town',
        'special_abilities': 'Mafiascum Link: https://wiki.mafiascum.net/index.php?title=Werewolf_(Role)',
        }
    }

# Repository of Modifiers

# TEST BOT KEY!
bot.run('')
