'''Search games by some criteria'''


from fastapi import Body, HTTPException

from mgxhub.db.operation import search_games as search_games_in_db
from mgxhub.model.searchcriteria import SearchCriteria
from webapi import app


@app.post("/game/search")
async def search_games(criteria: SearchCriteria = Body(...)) -> dict:
    '''Search games by some criteria

    Args:
        criteria: Search criteria.

    Returns:
        A dictionary containing the search result.

    Defined in: `webapi/routers/game_search.py`
    '''

    if not criteria:
        raise HTTPException(status_code=400, detail="Invalid search criteria")

    return search_games_in_db(criteria)
