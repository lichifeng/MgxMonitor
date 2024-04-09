'''Search players by name.'''

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from mgxhub.model.orm import Player
from mgxhub.util import sanitize_playername

# pylint: disable=not-callable


def search_players_by_name(
    session: Session,
    name: str,
    stype: str = 'std',
    orderby: str = 'nad',
    page: int = 1,
    page_size: int = 100
) -> list:
    '''Search players by name.

    Args:
        name: the name to search.
        stype: search type. 'std' for standard, 'prefix' for prefix, 'suffix' for suffix, 'exact' for exact match.
        orderby: order by. 'nad' for name asc, game_count desc, 'gdd' for game_count desc, name desc, etc.
        page: page number.
        page_size: page size.

    Defined in: `mgxhub/db/operation/search_player_name.py`
    '''

    name = sanitize_playername(name)

    if page < 1 or page_size < 1:
        return []

    order_parts = []
    game_count = func.count(Player.game_guid).label('game_count')
    if len(orderby) < 3:
        order_parts = [func.length(Player.name), game_count, asc, desc]
    else:
        if orderby[0].lower() == 'g':
            order_parts.extend([game_count, func.length(Player.name)])
        else:
            order_parts.extend([func.length(Player.name), game_count])
        if orderby[1].lower() == 'd':
            order_parts.append(desc)
        else:
            order_parts.append(asc)
        if orderby[2].lower() == 'd':
            order_parts.append(desc)
        else:
            order_parts.append(asc)

    query = session.query(
        Player.name,
        Player.name_hash,
        game_count
    ).group_by(
        Player.name
    )

    if stype == 'prefix':
        query = query.filter(Player.name.like(f"{name}%"))
    elif stype == 'suffix':
        query = query.filter(Player.name.like(f"%{name}"))
    elif stype == 'exact':
        query = query.filter(Player.name == name)
    else:
        query = query.filter(Player.name.like(f"%{name}%"))

    query = query.order_by(
        order_parts[2](order_parts[0]),
        order_parts[3](order_parts[1])
    ).limit(
        page_size
    ).offset(
        (page - 1) * page_size
    )

    return [list(row) for row in query.all()]
