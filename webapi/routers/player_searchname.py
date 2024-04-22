'''Search player by name'''

from datetime import datetime

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.db.operation import search_players_by_name
from webapi import app


@app.get("/player/searchname", tags=['player'])
async def search_player_by_name(
    player_name: str,
    stype: str = 'std',
    orderby: str = 'nad',
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1),
    db: Session = Depends(db_dep)
) -> dict:
    '''Search player by name

    Args:
        player_name (str): Player name to search
        stype (str, optional): Search type. 'std', 'prefix', 'suffix', 'exact'.
        orderby (str, optional): Order setting. Defaults to 'nagd'.
        page (int, optional): Page number. Defaults to 0.
        page_size (int, optional): Page size. Defaults to 100.

    Defined in: `webapi/routers/player_searchname.py`
    '''

    result = search_players_by_name(db, player_name, stype, orderby, page, page_size)
    current_time = datetime.now().isoformat()

    return {'players': result, 'generated_at': current_time}
