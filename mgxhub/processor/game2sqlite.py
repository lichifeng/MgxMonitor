'''Save game data to SQLite database'''

from mgxhub import logger
from mgxhub.db.operation import add_game
from mgxhub.rating import RatingLock


def save_game_sqlite(data: dict) -> tuple[str, str]:
    '''Save game data to SQLite database.

    **Only handles data. Need to clean the file depends on returned status.**

    Args:
        data: Game data from the parser.

    Returns:
        tuple: Status message and game GUID. 
        Possible status are: 
            success, updated, error, 
            duplicate, invalid, exists.
    '''

    try:
        result = add_game(data)
        logger.info(f'Game added: {result}')
        if result[0] in ['success', 'updated']:
            RatingLock().start_calc(schedule=True)
    except Exception as e:
        logger.error(f'game2sqlite error: {e}')
        result = 'error', data.get('guid', 'unknown guid')

    return result


async def async_save_game_sqlite(data: dict) -> tuple[str, str]:
    '''Async version of save_game_sqlite.

    **Only handles data. Need to clean the file depends on returned status.**
    '''

    return save_game_sqlite(data)
