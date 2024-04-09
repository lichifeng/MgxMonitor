'''Get rating page of where a player is located'''

from datetime import datetime

from mgxhub import db
from mgxhub.db.operation import get_player_rating_table
from webapi import app


@app.get("/rating/playerpage")
async def player_rating_page(
    player_hash: str,
    version_code: str = 'AOC10',
    matchup: str = 'team',
    order: str = 'desc',
    page_size: int = 100
) -> dict:
    '''Fetch rating of a player

    Returns a list of following fields:
    - name (str): Name of the player
    - name_hash (str): Name hash of the player
    - rating (float): Rating of the player
    - total (int): Total games played by the player
    - wins (int): Total wins of the player
    - streak (int): Current streak of the player
    - streak_max (int): Maximum streak of the player
    - highest (float): Highest rating of the player
    - lowest (float): Lowest rating of the player
    - first_played (str): First played date of the player
    - last_played (str): Last played date of the player

    Defined in: `webapi/routers/rating_player_page.py`
    '''

    session = db()
    ratingpage = get_player_rating_table(session, player_hash, version_code, matchup, order, page_size)
    current_time = datetime.now().isoformat()

    return {'ratings': ratingpage[0], 'total': ratingpage[1], 'generated_at': current_time}
