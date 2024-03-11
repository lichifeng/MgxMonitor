'''Search games in the database'''

from datetime import datetime

from sqlalchemy import text

from mgxhub import db
from mgxhub.model.searchcriteria import SearchCriteria


def search_games(criteria: SearchCriteria) -> dict:
    '''Search games.

    Args:
        criteria: Search criteria.

    Note:
        The search criteria is defined in mgxhub/model/searchcriteria.py.
        1) game_guid: GUID of the game. If given, other criteria will be ignored.

    Returns:
        A dictionary containing the search result.

    Defined in: `mgxhub/model/searchresult.py`
    '''

    where_clause = []
    if criteria.game_guid and len(criteria.game_guid) == 32:
        where_clause.append(f"game_guid = '{criteria.game_guid}'")
    else:
        if criteria.duration_min:
            where_clause.append(f"duration >= {criteria.duration_min}")
        if criteria.duration_max:
            where_clause.append(f"duration <= {criteria.duration_max}")
        if criteria.include_ai is not None:
            where_clause.append(f"include_ai = {criteria.include_ai}")
        if criteria.is_multiplayer is not None:
            where_clause.append(f"is_multiplayer = {criteria.is_multiplayer}")
        if criteria.population_min:
            where_clause.append(f"population >= {criteria.population_min}")
        if criteria.population_max:
            where_clause.append(f"population <= {criteria.population_max}")
        if criteria.instruction:
            where_clause.append(f"instruction LIKE '%{criteria.instruction}%'")
        if criteria.gametime_min:
            where_clause.append(f"game_time >= '{criteria.gametime_min * 60}'")
        if criteria.gametime_max:
            where_clause.append(f"game_time <= '{criteria.gametime_max * 60}'")
        if criteria.map_name:
            where_clause.append(f"map_name LIKE '%{criteria.map_name}%'")
        if isinstance(criteria.speed, list) and len(criteria.speed) > 0:
            speed_values = ', '.join(f"'{item}'" for item in criteria.speed)
            where_clause.append(f"speed IN ({speed_values})")
        if isinstance(criteria.victory_type, list) and len(criteria.victory_type) > 0:
            victory_type_values = ', '.join(f"'{item}'" for item in criteria.victory_type)
            where_clause.append(f"victory_type IN ({victory_type_values})")
        if isinstance(criteria.version_code, list) and len(criteria.version_code) > 0:
            version_code_values = ', '.join(f"'{item}'" for item in criteria.version_code)
            where_clause.append(f"version_code IN ({version_code_values.upper()})")
        if isinstance(criteria.matchup, list) and len(criteria.matchup) > 0:
            matchup_values = ', '.join(f"'{item}'" for item in criteria.matchup)
            where_clause.append(f"matchup IN ({matchup_values})")
        if isinstance(criteria.map_size, list) and len(criteria.map_size) > 0:
            map_size_values = ', '.join(f"'{item}'" for item in criteria.map_size)
            where_clause.append(f"map_size IN ({map_size_values})")

    where_clause = " AND ".join(where_clause)
    if where_clause:
        where_clause = f"WHERE {where_clause}"

    if criteria.order_by in ['created', 'duration', 'game_time']:
        order_by = criteria.order_by
    else:
        order_by = 'game_time'
    if criteria.order_desc:
        order_by += " DESC"

    query = text(f"""
        SELECT *
        FROM games
        {where_clause}
        ORDER BY {order_by}
        LIMIT {criteria.page_size}
        OFFSET {criteria.page * criteria.page_size};
    """)
    result = db().execute(query)
    games = [list(row) for row in result.fetchall()]
    current_time = datetime.now().isoformat()
    return {'games': games, 'generated_at': current_time}
