'''Get rating page of where a player is located'''

from datetime import datetime

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
    '''Fetch rating of a player'''

    ratingpage = get_player_rating_table(player_hash, version_code, matchup, order, page_size)
    current_time = datetime.now().isoformat()

    return {'ratings': ratingpage, 'generated_at': current_time}
