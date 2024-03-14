'''Get rating table'''

from sqlalchemy import asc, desc, func

from mgxhub import db
from mgxhub.model.orm import Rating

# pylint: disable=not-callable


def get_rating_table(
    version_code: str = 'AOC10',
    matchup: str = '1v1',
    order: str = 'desc',
    page: int = 0,
    page_size: int = 100,
) -> list:
    '''Get ratings information.

    Args:
        version_code: Version code of the game.
        matchup: Matchup of the game.
        page_size: page size of the result.

    Defined in: `mgxhub/db/operation/get_rating_table.py`
    '''

    matchup_value = '1v1' if matchup.lower() == '1v1' else 'team'
    order_method = desc if order.lower() == 'desc' else asc
    if page < 0 or page_size < 1:
        return []

    ratings = db().query(
        func.row_number().over(order_by=order_method(Rating.rating)).label('rownum'),
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
    ).order_by(
        order_method(Rating.rating)
    ).limit(
        page_size
    ).offset(
        page * page_size
    ).all()

    return [list(row) for row in ratings]
