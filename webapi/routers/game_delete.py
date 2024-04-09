'''Delete a game from the database'''

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from mgxhub import db, logger
from mgxhub.model.orm import Chat, File, Game, LegacyInfo, Player
from webapi.admin_api import admin_api


@admin_api.get("/game/delete")
async def delete_game(guid: str) -> dict:
    '''Delete a game from the database.

    - **guid**: The GUID of the game.

    Defined in: `webapi/routers/game_delete.py`
    '''

    session = db()
    game = session.query(Game).filter(Game.game_guid == guid).first()
    if game:
        session.query(Player).filter(Player.game_guid == guid).delete()
        session.query(Chat).filter(Chat.game_guid == guid).delete()
        session.query(File).filter(File.game_guid == guid).delete()
        session.query(LegacyInfo).filter(LegacyInfo.game_guid == guid).delete()
        session.delete(game)
        session.commit()
        logger.info(f"[DB] Delete: {guid}")
        return JSONResponse(status_code=200, content={"detail": f"Game [{guid}] deleted"})

    raise HTTPException(status_code=404, detail=f"Game not exists: [{guid}]")
