'''Get details for a game by its GUID.'''

from fastapi import Depends, HTTPException
from sqlalchemy import asc
from sqlalchemy.orm import Session

from mgxhub import logger
from mgxhub.db import db_dep
from mgxhub.model.orm import Chat, File, Game, Player
from mgxhub.model.webapi import GameDetail
from webapi import app


@app.get("/game/detail", tags=['game'])
async def get_game(guid: str, lang: str = 'en', db: Session = Depends(db_dep)) -> GameDetail | None:
    '''Get details for a game by its GUID

    - **guid**: GUID of the game.
    - **lang**: Language code. Default is 'en'.

    Defined in: `webapi/routers/game_detail.py`
    '''

    game_basic = db.query(Game).filter(Game.game_guid == guid).first()
    if game_basic is None:
        raise HTTPException(status_code=404, detail=f"Game profile [{guid}] not found")

    player_data = db.query(Player).filter(Player.game_guid == guid).all()
    file_data = db.query(File).filter(File.game_guid == guid).limit(10).all()
    chat_data = db.query(Chat.chat_time, Chat.chat_content)\
        .filter(Chat.game_guid == guid)\
        .group_by(Chat.chat_time, Chat.chat_content)\
        .order_by(asc(Chat.chat_time))\
        .all()

    details = GameDetail(game_basic, player_data, file_data, chat_data, lang)

    if details:
        return details

    error_msg = f"Failed to fetch game profile: {guid}"
    logger.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)
