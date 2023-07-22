import asyncio
from datetime import datetime
import collections


class Config:
    # Game Setup
    signups_open = False  # Pregame
    vote_channel = None
    game_channel = None
    global_day_length = 1
    day_end_time = 1

    day_end_task_object = None

    # Game Status
    day_number = 0
    signup_list = []  # Pre & Mid
    vote_count_number = 1
    votes = collections.OrderedDict()
    live_players = []
    vote_since_last_count = 0
    # start_time = datetime.now()  # Unused atm

    abstained_players = []

    # Post count related stuff
    post_counts = collections.defaultdict(lambda: collections.defaultdict(int))
    posts_per_24_hours_threshold = None  # WIP for use in tracking post activity
    posts_per_phase_threshold = None  # WIP for use in tracking post activity

    # CONSTANTS:
    NOT_VOTING = "not voting"  # Refers to a state in which a player either hasn't voted or has unvoted.
    LINE_BREAK = "-" * 40 + "\n"

    # Status & Alignment Framework: WIP doesn't currently account for extra Mafias.
    STATUS_ALIVE = "Alive"
    STATUS_DEAD = "Dead"
    STATUS_REPLACED = "Replaced"
    ALIGNMENT_TOWN = "Town"
    ALIGNMENT_MAFIA = "Mafia"
    ALIGNMENT_3RD_PARTY = "3rd Party"

    # Discord Roles: WIP
    ALIVE_ROLE = "Alive"
    DEAD_ROLE = "Dead"
    SPECTATOR_ROLE = "Spectator"
    SPOILER_ROLE = "Spoilers"
