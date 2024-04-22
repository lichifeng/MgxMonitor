'''Set visibility level of a game'''

from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from mgxhub.db import db_dep
from mgxhub.model.orm import Game
from webapi.admin_api import admin_api


@admin_api.get("/game/setvisibility", tags=['game'])
async def set_game_visibility(guid: str, lv: int = 0, db: Session = Depends(db_dep)) -> dict:
    '''Set visibility level of a game.

    - **guid**: The GUID of the game.
    - **lv**: Visibility level. 0 for public, 1 for private, 2 for unlisted.

    Defined in: `webapi/routers/game_visibility.py`
    '''

    if lv not in [0, 1, 2]:
        raise HTTPException(status_code=400, detail="Invalid visibility level. Must be 0, 1, or 2.")

    game = db.query(Game).filter(Game.game_guid == guid).first()
    if game:
        game.visibility = lv
        db.commit()
        return JSONResponse(status_code=200, content={"detail": f"Game [{guid}] visibility set to {lv}"})

    raise HTTPException(status_code=404, detail=f"Game [{guid}] not found")
