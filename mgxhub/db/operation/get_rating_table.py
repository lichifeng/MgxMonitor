'''Get rating table'''

from sqlalchemy import text

from mgxhub import db


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
    order_method = 'DESC' if order.lower() == 'desc' else 'ASC'
    if page < 0 or page_size < 1:
        return []

    sql = text(f"""
        SELECT ROW_NUMBER() OVER (ORDER BY rating {order_method}) AS rownum,
            name,
            name_hash,
            rating,
            total,
            wins,
            streak,
            streak_max,
            highest,
            lowest,
            first_played,
            last_played
        FROM ratings
        WHERE version_code = :version_code AND matchup = :matchup_value
        ORDER BY rating {order_method}
        LIMIT :page_size
        OFFSET :page;
    """)

    ratings = db().execute(
        sql,
        {
            "version_code": version_code,
            "matchup_value": matchup_value,
            "page_size": page_size,
            "page": page * page_size
        }
    ).fetchall()
    return [list(row) for row in ratings]
