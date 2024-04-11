'''Save game data to SQLite database'''

import traceback

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mgxhub import logger
from mgxhub.db.operation import add_game
from mgxhub.rating import RatingLock


def save_game_sqlite(session: Session, data: dict, retries: int = 3) -> tuple[str, str]:
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
        result = add_game(session, data)
        logger.info(f'Game added: {result}')
        if result[0] in ['success', 'updated']:
            RatingLock().start_calc(schedule=True)
    except IntegrityError:
        if retries > 0:
            session.rollback()  # 回滚事务
            return save_game_sqlite(session, data, retries - 1)  # 重新调用自身，减少重试次数
        else:
            result = 'error', data.get('guid', 'unknown guid')
    except Exception as e:
        tb = traceback.format_exc()  # 获取异常的详细信息
        logger.error(f'game2sqlite error: {e}\n{tb}')  # 记录异常的详细信息
        result = 'error', data.get('guid', 'unknown guid')

    return result


async def async_save_game_sqlite(session: Session, data: dict) -> tuple[str, str]:
    '''Async version of save_game_sqlite.

    **Only handles data. Need to clean the file depends on returned status.**
    '''

    return save_game_sqlite(session, data)
