'''Get rating page of where a player is located'''

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from mgxhub import db
from mgxhub.model.orm import Rating

# pylint: disable=not-callable


def get_player_rating_table(
    session: Session,
    name_hash: str,
    version_code: str = 'AOC10',
    matchup: str = '1v1',
    order: str = 'desc',
    page_size: int = 100,
) -> tuple[list[list], int]:
    '''Get rating page of where a player is located.

    This is not only for the player, but also for page where the player is
    located.

    Args:
        name_hash: the name_hash of the player. version_code: Version code of
        the game. matchup: Matchup of the game. page_size: page size.

    Defined in: `mgxhub/db/operation/get_player_rating.py`
    '''

    matchup_value = '1v1' if matchup.lower() == '1v1' else 'team'
    order_method = desc if order.lower() == 'desc' else asc

    if page_size < 1:
        return []

    rating_table = select(
        func.row_number().over(order_by=[order_method(Rating.rating), desc(Rating.total)]).label('rownum'),
        Rating.name,
        Rating.name_hash,
        Rating.rating,
        Rating.total,
        Rating.wins,
        Rating.streak,
        Rating.streak_max,
        Rating.highest,
        Rating.lowest,
        Rating.first_played,
        Rating.last_played
    ).filter(
        Rating.version_code == version_code,
        Rating.matchup == matchup_value
    ).cte('rating_table')

    name_hash_index = select(
        rating_table.c.rownum
    ).where(
        rating_table.c.name_hash == (name_hash.lower() if name_hash else None)
    ).cte('name_hash_index')

    name_hash_rownum = select(name_hash_index.c.rownum).limit(1).as_scalar()

    ratings = session.query(
        rating_table
    ).filter(
        rating_table.c.rownum > (name_hash_rownum // page_size) * page_size,
        rating_table.c.rownum <= ((name_hash_rownum // page_size) + 1) * page_size
    ).order_by(
        rating_table.c.rownum
    ).limit(page_size).correlate(rating_table, name_hash_index).all()

    ratings_count = session.query(
        func.count(Rating.rating)
    ).filter(
        Rating.version_code == version_code,
        Rating.matchup == matchup_value
    ).scalar()

    return [list(row) for row in ratings], ratings_count
