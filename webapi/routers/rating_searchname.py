'''Search player names by keyword in ratings table'''

from fastapi import Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.model.orm import Rating
from webapi import app

# pylint: disable=not-callable


@app.get("/rating/searchname", tags=['rating'])
async def get_player_name_by_hash(
        keyword: str,
        version_code: str = 'AOC10',
        matchup: str = 'team',
        page: int = Query(1, ge=1),
        page_size: int = Query(1, ge=1),
        session: Session = Depends(db_dep)
) -> dict:
    '''Search player names by keyword in ratings table.

    Args:
        keyword (str): Keyword to search.
        version_code (str, optional): Version code. Defaults to 'AOC10'.
        matchup (str, optional): Matchup type. Defaults to 'team'.
        limit (int, optional): Limit of results. Defaults to 1.

    Defined in: `webapi/routers/rating_searchname.py`
    '''

    names = session.query(
        Rating.name,
        Rating.name_hash,
        Rating.rating
    ).filter(
        Rating.version_code == version_code.upper(),
        Rating.matchup == matchup.lower(),
        Rating.name.like(f"%{keyword}%")
    ).distinct().order_by(
        func.length(Rating.name)
    ).offset((page-1)*page_size).limit(page_size).all()

    return {'names': [(name[0], name[1], name[2]) for name in names]}
