'''Search games by some criteria'''


from fastapi import Body, Depends
from sqlalchemy.orm import Session

from mgxhub import logger
from mgxhub.db import db_dep
from mgxhub.db.operation import search_games as search_games_in_db
from mgxhub.model.searchcriteria import SearchCriteria
from webapi import app


@app.post("/game/search", tags=['game'])
async def search_games(criteria: SearchCriteria = Body(...), session: Session = Depends(db_dep)) -> dict:
    '''Search games by some criteria

    Args:
        criteria: Search criteria.

    Returns:
        A dictionary containing the search result.

    Defined in: `webapi/routers/game_search.py`
    '''

    logger.info(criteria.model_dump())

    result = search_games_in_db(session, criteria)

    return result
