'''Set visibility level of a game'''

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from mgxhub import db
from mgxhub.model.orm import Game
from webapi.admin_api import admin_api


@admin_api.get("/game/setvisibility")
async def set_game_visibility(guid: str, lv: int = 0) -> dict:
    '''Set visibility level of a game.

    - **guid**: The GUID of the game.
    - **lv**: Visibility level. 0 for public, 1 for private, 2 for unlisted.

    Defined in: `webapi/routers/game_visibility.py`
    '''

    game = db().query(Game).filter(Game.game_guid == guid).first()
    if game:
        game.visibility = lv
        db().commit()
        return JSONResponse(status_code=200, content={"detail": f"Game [{guid}] visibility set to {lv}"})

    raise HTTPException(status_code=404, detail=f"Game [{guid}] not found")
