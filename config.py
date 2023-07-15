import asyncio
from datetime import datetime
import collections


class Config():
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
    prev_vote = None
    current_vote = None  # Unused atm
    live_players = []
    vote_since_last_count = 0
    # start_time = datetime.now()  # Unused atm

    abstained_players = []

    # Post count collection
    post_counts = collections.defaultdict(lambda: collections.defaultdict(int))
