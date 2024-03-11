'''Search players by name.'''

from sqlalchemy import text

from mgxhub import db
from mgxhub.util import sanitize_playername


def search_players_by_name(
    name: str,
    stype: str = 'std',
    orderby: str = 'nagd',
    page: int = 0,
    page_size: int = 100
) -> list:
    '''Search players by name.

    Args:
        name: the name to search.
        stype: search type. 'std' for standard, 'prefix' for prefix, 'suffix' for suffix, 'exact' for exact match.
        orderby: order by. 'nagd' for name asc, game_count desc, 'gdnd' for game_count desc, name desc, etc.
        page: page number.
        page_size: page size.

    Defined in: `mgxhub/db/operation/search_player_name.py`
    '''

    name = sanitize_playername(name)

    if page < 0 or page_size < 1:
        return []

    order_parts = []
    if len(orderby) < 4:
        order_parts = ["LENGTH(name)", "game_count", "ASC", "DESC"]
    else:
        if orderby[0].lower() == 'g':
            order_parts.extend(["game_count", "LENGTH(name)"])
        else:
            order_parts.extend(["LENGTH(name)", "game_count"])
        if orderby[1].lower() == 'd':
            order_parts.append("DESC")
        else:
            order_parts.append("ASC")
        if orderby[3].lower() == 'd':
            order_parts.append("DESC")
        else:
            order_parts.append("ASC")
    order_cmd = f"{order_parts[0]} {order_parts[2]}, {order_parts[1]} {order_parts[3]}"

    sql = text(f"""
        SELECT name, name_hash, COUNT(game_guid) AS game_count
        FROM players
        WHERE name LIKE :name
        GROUP BY name
        ORDER BY {order_cmd}
        LIMIT :page_size
        OFFSET :page;
    """)

    if stype == 'prefix':
        name = f"{name}%"
    elif stype == 'suffix':
        name = f"%{name}"
    elif stype == 'exact':
        name = f"{name}"
    else:
        name = f"%{name}%"

    players = db().execute(
        sql,
        {
            "name": name,
            "page_size": page_size,
            "page": page * page_size
        }
    ).fetchall()

    return [list(row) for row in players]
