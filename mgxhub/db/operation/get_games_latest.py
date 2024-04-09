from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from mgxhub.model.orm import File, Game, Player


async def fetch_latest_games_async(session: Session, limit: int) -> dict:
    '''Fetch recently uploaded games

    - **limit**: The number of games to fetch. Default is 100.

    Returned data format:
        [game_guid, version_code, created_time, game_time, map_name, matchup, duration, speed, uploader]

    Defined in: `webapi/routers/game_latest.py`
    '''

    latest_game_query = select(
        Game.game_guid,
        Game.version_code,
        Game.created,
        Game.game_time,
        Game.map_name,
        Game.matchup,
        Game.duration,
        Game.speed,
        File.recorder_slot
    ).select_from(
        Game
    ).join(
        File, Game.game_guid == File.game_guid
    ).order_by(
        Game.created.desc()
    ).limit(limit).subquery('g')

    result = session.query(
        latest_game_query.c.game_guid,
        latest_game_query.c.version_code,
        latest_game_query.c.created,
        latest_game_query.c.game_time,
        latest_game_query.c.map_name,
        latest_game_query.c.matchup,
        latest_game_query.c.duration,
        latest_game_query.c.speed,
        select(Player.name).where(
            Player.game_guid == latest_game_query.c.game_guid,
            Player.slot == latest_game_query.c.recorder_slot
        ).correlate(latest_game_query).as_scalar()
    ).all()
    games = [list(row) for row in result]
    current_time = datetime.now().isoformat()

    return {'games': games, 'generated_at': current_time}
