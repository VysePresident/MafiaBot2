# MafiaBot

Bot made for Discord, runs in Python, uses SparkedHost.us as the host.

# FEATURES TO ADD:

-Track number of posts made in 24 hour intervals - w/ command for all users or just an individual user

-Set posting limit in game thread per arbitrary time period (Default is 24 hours) w/ command to see how many posts left per user. (Going overboard should probably result in a slow mode role instead of locking you out?) 

----POSTING RESTRICTION SHOULD BE ADDED/REMOVED AT ARBITRARY TIME IF MOD SETS IT TO DO SO.

-Automate user post search in game thread somehow?

-The %changedaylength() command should be possible to adjust in d/h/m simultaneously.  It should only use integer values.

-Post a votecount in game chat every 10 votes

-Use the End of Day Timer

-Link vote-post in game chat to the votecount that results.

-Generate Original Playerlist and Update playerlist Alive/Dead automatically.

-<u>The code should be broken entirely into cogs which are loaded into the bot via extension, allowing the bot to be changed at runtime</u> - The main.py file should have no code except the extensions!  (And possibly include empty extensions based on what we're intended to fill out later.)

-The bot should be able to host multiple different games simultaneously.  Look into "Sharding"?

-The bot should be able to track edits/deletions efficiently only from players with the "ALIVE" role in the game_thread.  

-Track post counts and create a command that lists the number of posts from each user in the past **24 hours** (we can also allow the mod to adjust this time later).

-Add a prod command possibly?  Consider user convenience when making it, but also the necessity of V/LA (Legitimate absences with proper notification) and players who won't be picked up by the warning system that nonetheless deserve a prod.

-AMBITIOUS/UNKNOWN - Create a "settings & configurations" webpage that opens on the user's localhost and allows them to adjust the game's configurations manually.  Will be useful for setting up full games and other advanced properties later on.  (I.e. Do you want your votecount in a thread, maybe.  If we have to go with that lol)

-AMBITIOUS - Implement Role PMs and game-running functionality.  (Significant endevor, will need to be plotted out in more detail later.  I would like to combine this with the webpage idea if possible, because I think that's a more convenient interface.)

-Store current game info in a database so that it persists even after the bot is turned off and then back on.

# BUGS (Bunny):

-(Logged IN-GAME July 10th, 2023) - The "CHANGE" section of the vote count is not accurate.  I believe it is failing to account for voting using name instead of tag.  Likely the "config.py" variable "prev_vote" isn't being updated correctly.

-(Logged July 8th, 2023) - But would lead to some disappointments. I feel like inviting at random is non-ideal, but if you make friends there 

-(Logged July 8th, 2023) - The "votecount" function/command code is currently really chaotic and ugly.  It ought to be streamlined and some of the functionality should be placed into smaller functions

-(Logged July 8th, 2023) - The %gamesetup command triggers rate-limiting constantly.  This lasts for ~10 seconds in the test server but can last 1-5 minutes in the actual Mafia server.  This is a serious problem and needs to be optimized somehow. 

-(Logged July 8th, 2023) - The %endgame command checks *every* player in the server.  Is there a way to optimize it? Keep in mind that mods will add and remove roles from people arbitrarily on occassion so it really does need to track *every* instance of the roles (Alive, Dead, Spectator, Spoiler), not just those created by the game.

-Bot can't handle underscores and certain usernames.

-Are all moderater commands admin only? (No - %kill needs some work) 

-(Logged 6/25/23) When adding player to game, vote count should note the changed requirements to lynch

-Logged(6/28/23) Need to completely remove time (and send an appropriate message) when thread ends.  Very minor.

# IN-TESTING-PHASE:
1) Features, changes, bug-fixes that need testing when bot is free:

GEO (July 8 2023) Listed:

[implemented] - In-game lynch status message that follows a vote or unvote now also links to the votecount for ease of players exploring the vote history.
[implemented] - %signuplist now shows the number of people playing.

# COMPLETED:

[implemented] - Allow changes to day length when day is active
*(needs more testing, likely will need to make a 2nd day_length int that gets reverted after a day)*

[implemented] - Allow player swaps mid-game


GEO (June 27 2023) Listed:

[implemented] - Set up a category with standard channels and permissions for a new game including: 
1) game-thread (All can see, alive can't post to start but can be enabled when Day starts.) 
2) playerlist thread 
3) vote-count thread (visible to everyone, no posting perms)
4) mafia-chat (hidden - mod will update perms manually as per norm.)
5) mod-thread (hidden)
6) fallout thread
7) spec chat thread


GEO (June 26 2023) Listed:

[implemented] Clean up roles (Alive, Dead, Spec, Spoiled) after game ends.  Should be its own function, which is called when %endgame is called.

[implemented] - Moderator should be able to change the vote-count thread.

[implemented] - Moderator should be able to change the game thread.

[bugfix] - Playerlist is not cleared when using %endgame

GEO (June 26 2023) Listed:

[implemented] Fixed bug where changedaylength command would not change the length of the current day.

GEO (June 25 2023) Listed:

[implemented] Bot now uses dashes for the "start of day" count consistent with all other vote counts.

[implemented] Requesting a votecount in-thread no longer increments the number.


GEO (June 21 2023) Listed:

[implemented] - The bot currently reacts to all unvotes with a message as if the unvoter were not voting anyone to begin with.  It still correctly removes the vote at least.

[implemented] - When bot reports "User has voted for Aso" add "Aso is now L-1" or whatever count is relevent.

[implemented] - Bot does not post final vote count when lynch is achieved.

[implemented] - Bold the votecount change

[implemented] - Link the votecount to the message of vote

[implemented] - Bot doesn't track the order of which votes are placed




