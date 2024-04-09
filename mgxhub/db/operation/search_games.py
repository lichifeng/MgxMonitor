'''Search games in the database'''

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from mgxhub.model.orm import Game
from mgxhub.model.searchcriteria import SearchCriteria


def search_games(session: Session, criteria: SearchCriteria) -> dict:
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

    query = session.query(Game)

    if criteria.game_guid and len(criteria.game_guid) == 32:
        query = query.filter(Game.game_guid == criteria.game_guid)
    else:
        if criteria.duration_min:
            query = query.filter(Game.duration >= criteria.duration_min)
        if criteria.duration_max:
            query = query.filter(Game.duration <= criteria.duration_max)
        if criteria.include_ai is not None:
            query = query.filter(Game.include_ai == criteria.include_ai)
        if criteria.is_multiplayer is not None:
            query = query.filter(Game.is_multiplayer == criteria.is_multiplayer)
        if criteria.population_min:
            query = query.filter(Game.population >= criteria.population_min)
        if criteria.population_max:
            query = query.filter(Game.population <= criteria.population_max)
        if criteria.instruction:
            query = query.filter(Game.instruction.like(f"%{criteria.instruction}%"))
        if criteria.gametime_min:
            query = query.filter(Game.game_time >= criteria.gametime_min * 60)
        if criteria.gametime_max:
            query = query.filter(Game.game_time <= criteria.gametime_max * 60)
        if criteria.map_name:
            query = query.filter(Game.map_name.like(f"%{criteria.map_name}%"))
        if isinstance(criteria.speed, list) and len(criteria.speed) > 0:
            query = query.filter(Game.speed.in_(criteria.speed))
        if isinstance(criteria.victory_type, list) and len(criteria.victory_type) > 0:
            query = query.filter(Game.victory_type.in_(criteria.victory_type))
        if isinstance(criteria.version_code, list) and len(criteria.version_code) > 0:
            query = query.filter(Game.version_code.in_(criteria.version_code))
        if isinstance(criteria.matchup, list) and len(criteria.matchup) > 0:
            query = query.filter(Game.matchup.in_(criteria.matchup))
        if isinstance(criteria.map_size, list) and len(criteria.map_size) > 0:
            query = query.filter(Game.map_size.in_(criteria.map_size))

    if criteria.order_by.lower() in ['created', 'duration', 'game_time']:
        order_by = getattr(Game, criteria.order_by)
    else:
        order_by = Game.game_time
    if criteria.order_desc:
        order_by = desc(order_by)

    query = query.order_by(order_by).limit(criteria.page_size).offset((criteria.page - 1) * criteria.page_size)

    games = [{
        'game_guid': game.game_guid,
        'version_code': game.version_code,
        'map_name': game.map_name,
        'matchup': game.matchup,
        'duration': game.duration,
        'game_time': game.game_time,
        'population': game.population,
        'include_ai': game.include_ai,
        'is_multiplayer': game.is_multiplayer,
        'speed': game.speed,
        'victory_type': game.victory_type,
        'map_size': game.map_size,
        'instruction': game.instruction,
        'players': [(player.slot, player.name, player.civ_name, player.type, player.name_hash) for player in game.players]
    } for game in query.all()]
    current_time = datetime.now().isoformat()

    return {'games': games, 'generated_at': current_time}
