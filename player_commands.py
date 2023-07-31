"""
Author: Geo
Date: July 29th, 2023

This module is used for bot commands that any player can use.
"""

import discord
import time as t
from discord.ext import commands
from config import Config
from player import Player

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def signup(self, ctx):
        """This function allows a user to sign up for the game during the signups phase."""
        # DEBUG LOG
        print(f"Command signup: Author: {ctx.author.name}")

        if Config.signups_open:
            if ctx.author not in Config.signup_list:
                # Config.signup_list.append(ctx.author)
                Config.signup_list[ctx.author] = Player(ctx.author, Config.STATUS_INACTIVE, len(Config.signup_list) + 1)
                await ctx.send(f'Thank you for signing up, {ctx.author.display_name}!')
            else:
                await ctx.send(f'You have already signed up, {ctx.author.display_name}!')
        else:
            await ctx.send('Sign ups are currently closed.')

    @commands.command()
    async def unsignup(self, ctx):
        """This function allows a user to remove themselves from the sign-up list."""
        # DEBUG LOG
        print(f"Command unsignup: Author: {ctx.author.name}")
        if Config.signups_open:
            if ctx.author in Config.signup_list:
                # Config.signup_list.remove(ctx.author)
                player = Config.signup_list.pop(ctx.author)
                # await ctx.send(f'You have been removed from the sign up list, {ctx.author.display_name}!')
                await ctx.send(f'You have been removed from the sign up list, {player.displayPlayerName()}!')
            else:
                await ctx.send(f'You are not on the sign up list, {ctx.author.display_name}!')
        else:
            await ctx.send(f"Sign ups are currently closed.")

    @commands.command()
    async def signuplist(self, ctx):
        """This function allows a user to pull up the list of players who have signed up"""
        # DEBUG LOG
        print(f"Command signuplist: Author: {ctx.author.name}")
        if not Config.signup_list:
            await ctx.send('No one has signed up yet.')
        else:
            # signups = "\n".join([player_to_remove.name for player_to_remove in Config.signup_list])
            # signups = "\n".join([user.display_name for user in Config.signup_list])
            signups = "\n".join([f"{index + 1}\. {user.display_name}" for index, user in enumerate(Config.signup_list)])
            await ctx.send(f'There are currently {len(Config.signup_list)} signups:\n\n{signups}')

    @commands.command()
    async def vote(self, ctx, voted: discord.Member):
        """This function is used for one member to place their vote on another member."""
        # DEBUG LOG
        print(f'command vote: ctx.author: {ctx.author.name} and voted: {voted.name}')
        """if ctx.author not in Config.signup_list or voted not in Config.signup_list:
            await ctx.send("Either the voter or the voted player is not in the game.")
            return"""
        if ctx.author not in Config.signup_list:
            await ctx.send("The voter is not in the game.")
            return
        if voted not in Config.signup_list:
            await ctx.send("The voted player is not in the game.")
            return
        if ctx.author in Config.votes and Config.votes[ctx.author] == voted:
            await ctx.send("You've already voted for this player.")
            return
        if ctx.channel != Config.game_channel:
            await ctx.send("You can only vote in the game chat.")
            return

        voter = ctx.author
        prev_vote = ''
        # prev_vote = Config.signup_list[voter].vote
        current_vote = voted
        # No longer needed if Player object handles vote status.
        if ctx.author in Config.votes:
            print("Gate %vote - Change Vote")
            prev_vote = Config.votes.pop(ctx.author)
        else:
            print("Gate %vote - Wasn't Voting")
            prev_vote = Config.NOT_VOTING
        # Config.signup_list[voter].vote = voted  # WIP - Not using the vote attribute
        Config.votes[ctx.author] = voted
        # Make sure the stored info is very visibly accurate or inaccurate.
        # Config.votes[ctx.author] = Config.signup_list[voter].vote # WIP - Not using the vote attribute
        # if Config.signup_list[voter].vote != Config.votes[ctx.author] or Config.votes[ctx.author] != voted:
        #    print(f"VOTE COMMAND MAJOR ERROR! Config.signup_list[voter].vote: {Config.signup_list[voter].vote} "
        #          f"IS NOT THE SAME AS Config.votes[ctx.author]: {Config.votes[ctx.author]}")
        #    await ctx.send(f"THERE HAS BEEN AN ERROR IN RECORDING YOUR VOTE!  Your vote has been stored as both "
        #                   f"Player Object: {Config.signup_list[voter].vote} and dict: {Config.votes[ctx.author]}.")
        #    return

        # DEBUG LOGS:
        """if prev_vote != Config.NOT_VOTING and current_vote != Config.NOT_VOTING:
            print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
            print(f'Finishing vote - prev_vote: {prev_vote.name} current_vote: {current_vote.name} voter: {voter.name}')
        elif prev_vote == Config.NOT_VOTING:
            print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
            print(f'Finishing vote - prev_vote: {prev_vote} current_vote: {current_vote.name} voter: {voter.name}')
        else:
            print(f'Finishing command vote: ctx.author: {ctx.author.name} and voted: {Config.votes[ctx.author].name}')
            print(f'Finishing vote - prev_vote: {prev_vote.name} current_vote: {current_vote} voter: {voter.name}')"""

        # await ctx.send(f"{ctx.author.name} has voted for {Config.votes[ctx.author].name}.")
        await ctx.send(f"{ctx.author.display_name} has voted for {Config.votes[ctx.author].display_name}.")
        # await ctx.send(f"{ctx.author.display_name} has voted for {Config.votes[ctx.author].display_name}.")  # WIP - Not using the vote attribute
        await self.bot.votecount(self.bot, ctx, voter, prev_vote, current_vote)
        return

    @commands.command()
    async def unvote(self, ctx):
        """This function is used when a member wishes to remove their vote without replacing it."""
        # DEBUG LOG
        print(f'command unvote: ctx.author: {ctx.author.name} has unvoted {Config.votes[ctx.author]}')

        if ctx.channel != Config.game_channel:
            await ctx.send("You can only vote in the game chat.")
            return
        if ctx.author in Config.votes:
            prev_vote = Config.votes.pop(ctx.author)
            # Config.signup_list[ctx.author] = current_vote = Config.NOT_VOTING
            current_vote = Config.NOT_VOTING
            voter = ctx.author
            # await ctx.send(f"{ctx.author.name} has unvoted {prev_vote.name}.")
            await ctx.send(f"{ctx.author.display_name} has unvoted {prev_vote.display_name}.")
            # print(f"{Config.signup_list[ctx.author]} is currently {Config.signup_list[ctx.author].vote}")
            await self.bot.votecount(self.bot, ctx, voter, prev_vote, current_vote)
        else:
            await ctx.send("You haven't voted yet.")
        return

    @commands.command()
    async def time(self, ctx):
        # DEBUG
        print(f'command time: ctx.author: {ctx.author.name} used %time')

        if Config.day_end_time is None:
            await ctx.send("The game hasn't started yet.")
        else:
            time_remaining = Config.day_end_time - t.time()
            if time_remaining <= 0:
                print(f'RESULT: The day has ended.')
                await ctx.send("The day has ended.")
            else:
                hours, rem = divmod(time_remaining, 3600)
                minutes, seconds = divmod(rem, 60)
                # DEBUG LOG
                print(f'RESULT of {ctx.author.name} using %time: '
                      f'Time remaining: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.')

                await ctx.send(
                    f"Time remaining: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")

    @commands.command()
    async def playerlist(self, ctx):
        # DEBUG
        print(f'command playerlist: ctx.author: {ctx.author.name} used %playerlist')

        """alive_players = []
        dead_players = []
        for member in ctx.guild.members:
            if discord.utils.get(member.roles, name="Alive"):
                # alive_players.append(member.name)
                alive_players.append(member.display_name)
            elif discord.utils.get(member.roles, name="Dead"):
                # dead_players.append(member.name)
                dead_players.append(member.display_name)
        if not alive_players:
            alive_players.append("No players alive.")
        if not dead_players:
            dead_players.append("No players dead.")
        playerlist_string = "\n\n__**Alive Players**__\n" + '\n'.join(alive_players) + '\n'
        playerlist_string += "\n__**Dead Players**__\n" + '\n'.join(dead_players)
        print(f"This is result of {ctx.author.name} using playerlist: {playerlist_string}")"""
        alive_players = []
        dead_players = []
        index = 0
        for member, player in Config.player_list.items():
            print(f"This is member.name: {member.name} player.status: {player.status}")
            if player.status == Config.STATUS_ALIVE:
                index += 1
                print(f"Player is alive! This is index: {index}")
                # alive_players.append(f"{player.signup_number}. {member.display_name}")
                alive_players.append(f"{index}\. {member.display_name}")
                print(f"Appended: {member.display_name} at: {index}")
            if player.status == Config.STATUS_DEAD:
                index += 1
                print(f"Player is dead! This is index: {index}")
                # dead_players.append(f"{player.signup_number}. {member.display_name}")
                dead_players.append(f"{index}\. {member.display_name}")
                print(f"Appended: {member.display_name} at: {index}")
        # signups = "\n".join([f"{index + 1}. {user.display_name}" for index, user in enumerate(Config.signup_list)])
        playerlist_string = ''
        if len(alive_players) > 0:
            playerlist_string += "\n\n__**Alive Players**__\n\n" + '\n'.join(alive_players) + '\n'
        else:
            playerlist_string += "\n__**Alive Players**__\n" + '\n (None)'
        if len(dead_players) > 0:
            playerlist_string += "\n__**Dead Players**__\n\n" + '\n'.join(dead_players)
        else:
            playerlist_string += "\n__**Dead Players**__\n" + '\n (None)'
        await ctx.send(f"{playerlist_string}")


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))
