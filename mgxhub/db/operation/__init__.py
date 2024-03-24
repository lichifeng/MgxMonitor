'''Some big database-related operations'''

from .add_game import add_game
from .find_player_friends import async_get_close_friends, get_close_friends
from .get_player_counts import async_get_player_totals, get_player_totals
from .get_player_latest import get_latest_players
from .get_player_rating import get_player_rating_table
from .get_player_rating_stats import (async_get_player_rating_stats,
                                      get_player_rating_stats)
from .get_player_recent_games import (async_get_player_recent_games,
                                      get_player_recent_games)
from .get_rating_stats import get_rating_stats
from .get_rating_table import get_rating_table
from .search_games import search_games
from .search_player_name import search_players_by_name
