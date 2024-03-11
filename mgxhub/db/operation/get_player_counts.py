'''Get game counts of a player'''

# pylint: disable=E1102

from sqlalchemy import func

from mgxhub import db
from mgxhub.model.orm import Game, Player


def get_player_totals(name_hash: str) -> dict:
    '''Get game counts of a player.

    Args:
        name_hash: the name_hash of the player.

    Defined in: `mgxhub/db/operation/get_player_counts.py`
    '''

    total_games = db().query(func.count(Game.game_guid.distinct()))\
        .join(Player, Game.game_guid == Player.game_guid)\
        .filter(Player.name_hash == name_hash).scalar()
    total_wins = db().query(func.count(Game.game_guid.distinct()))\
        .join(Player, Game.game_guid == Player.game_guid)\
        .filter(Player.name_hash == name_hash, Player.is_winner).scalar()
    total_1v1 = db().query(func.count(Game.game_guid.distinct()))\
        .join(Player, Game.game_guid == Player.game_guid)\
        .filter(Player.name_hash == name_hash, Game.matchup == '1v1').scalar()

    return {"total_games": total_games, "total_wins": total_wins, "total_1v1_games": total_1v1}


async def async_get_player_totals(name_hash: str) -> dict:
    '''Async version of fetch_player_totals()'''

    return get_player_totals(name_hash)
