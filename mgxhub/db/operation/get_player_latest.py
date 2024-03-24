'''Get latest players'''

from sqlalchemy import func, select

from mgxhub import db
from mgxhub.model.orm import Game, Player

# pylint: disable=E1102


def get_latest_players(limit: int = 20) -> dict:
    '''Newly found players.

    Including name, name_hash, first_found, won games, total games, and 1v1 games counts.

    Args:
        limit: maximum number of players to be included.

    Defined in: `mgxhub/db/operation/get_player_latest.py`
    '''

    player_query = select(
        Player.name,
        Player.name_hash,
        func.min(Player.created).label('first_found')
    ).group_by(
        Player.name
    ).subquery('p')

    result = db().query(
        player_query.c.name,
        player_query.c.name_hash,
        player_query.c.first_found,
        select(func.count(Player.name).label('win_count')).where(
            Player.name == player_query.c.name, Player.is_winner == 1).correlate(player_query).as_scalar(),
        select(func.count(Player.name).label('total_games')).where(
            Player.name == player_query.c.name).correlate(player_query).as_scalar(),
        select(func.count(Game.game_guid).label('total_1v1_games')).select_from(Game).join(
            Player, Game.game_guid == Player.game_guid).where(
            Player.name == player_query.c.name, Game.matchup == '1v1').correlate(player_query).as_scalar()
    ).select_from(
        player_query
    ).order_by(
        player_query.c.first_found.desc()
    ).limit(limit).all()

    return [list(row) for row in result]
