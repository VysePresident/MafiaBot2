from datetime import datetime
import collections

signups_open = False
signup_list = []
vote_channel = None
game_channel = None
day_number = 0
vote_count_number = 1
votes = {} 
day_end_time = None
global_day_length = 1
live_players = []
vote_since_last_count = 0
start_time = datetime.now()
abstained_players = []
post_counts = collections.defaultdict(lambda: collections.defaultdict(int))