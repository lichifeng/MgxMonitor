'''Fetch latest N players and their simple stats.'''


from datetime import datetime

from sqlalchemy import func, select

from mgxhub import db
from mgxhub.model.orm import Game, Player
from webapi import app

# pylint: disable=E1102


@app.get("/player/latest")
async def get_latest_players(limit: int = 20) -> dict:
    '''Newly found players.

    Including won games, total games, and 1v1 games counts.

    Args:
        limit: maximum number of players to be included.

    Defined in: `webapi/routers/player_latest.py`
    '''

    player_query = select(
        Player.name,
        func.max(Player.created).label('latest_created')
    ).group_by(
        Player.name
    ).limit(limit).subquery('p')

    result = db().query(
        player_query.c.name,
        player_query.c.latest_created,
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
        player_query.c.latest_created.desc()
    ).all()

    players = [list(row) for row in result]

    current_time = datetime.now().isoformat()
    return {'players': players, 'generated_at': current_time}
