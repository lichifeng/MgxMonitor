'''Get rating page of where a player is located'''

from sqlalchemy import text

from mgxhub import db


def get_player_rating_table(
    name_hash: str,
    version_code: str = 'AOC10',
    matchup: str = '1v1',
    order: str = 'desc',
    page_size: int = 100,
) -> dict:
    '''Get rating page of where a player is located.

    This is not only for the player, but also for page where the player is
    located.

    Args:
        name_hash: the name_hash of the player. version_code: Version code of
        the game. matchup: Matchup of the game. page_size: page size.

    Defined in: `mgxhub/db/operation/get_player_rating.py`
    '''

    matchup_value = '1v1' if matchup.lower() == '1v1' else 'team'
    order_method = 'DESC' if order.lower() == 'desc' else 'ASC'
    if page_size < 1:
        return []

    sql = text(f"""
        WITH rating_table AS (
            SELECT ROW_NUMBER() OVER (ORDER BY rating {order_method}, total DESC) AS rownum,
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
        ), name_hash_index AS (
            SELECT rownum FROM rating_table WHERE name_hash = :name_hash
        )
        SELECT * FROM rating_table
        WHERE rownum > (SELECT rownum FROM name_hash_index) / :page_size * :page_size AND rownum <= ((SELECT rownum FROM name_hash_index) / :page_size + 1) * :page_size
        ORDER BY rownum
        LIMIT :page_size;
    """)

    ratings = db().execute(
        sql,
        {
            "version_code": version_code,
            "matchup_value": matchup_value,
            "page_size": page_size,
            "name_hash": name_hash.lower() if name_hash else None
        }
    ).fetchall()

    return [list(row) for row in ratings]
