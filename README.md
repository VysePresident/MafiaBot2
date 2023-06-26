# MafiaBot

Bot made for Discord, runs in Python, uses SparkedHost.us as the host.

# FEATURES TO ADD:

-Track number of posts made in 24 hour intervals - w/ command for all users or just an individual user

-Set posting limit in game thread per arbitrary time period (Default is 24 hours) w/ command to see how many posts left per user. (Going overboard should probably result in a slow mode role instead of locking you out?) 

----POSTING RESTRICTION SHOULD BE ADDED/REMOVED AT ARBITRARY TIME IF MOD SETS IT TO DO SO.

-Set up a category with standard channels and permissions for a new game including: 
1) game-thread (All can see, alive can't post to start but can be enabled when Day starts.) 
2) playerlist thread 
3) vote-count thread (visible to everyone, no posting perms)
4) mafia-chat (hidden - mod will update perms manually as per norm.)
5) mod-thread (hidden)
6) fallout thread
7) spec chat thread

-Automate user post search in game thread somehow?

-Clean up roles (Alive, Dead, Spec, Spoiled) after game ends.  Should be its own function, which is called when %endgame is called.

# BUGS (Bunny):

-The bot does not reset back to Day Phase 1 after the game ends and a new game starts.  Observe that ⁠33-vote-count starts on Day 2.

-The bot ended Day early once - I suspect that this occured at the time the new Day I started after skelet replaced in would have ended. 

-Bot can't handle underscores and certain usernames.

-Day end methods interfere with each other, needs a lot of debugging

-Are all moderater commands admin only? (No) 

-(Logged 6/25/23) - Playerlist is not cleared when using %endgame

-(Logged 6/25/23) When adding player to game, vote count should note the changed requirements to lynch

# IN-TESTING-PHASE:
1) Features, changes, need testing when bot is free:

[implemented] - Post a votecount in game chat every 10 votes

[implemented] - Allow changes to day length when day is active
*(needs more testing, likely will need to make a 2nd day_length int that gets reverted after a day)*

[implemented] - Allow player swaps mid-game

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

# COMPLETED:

