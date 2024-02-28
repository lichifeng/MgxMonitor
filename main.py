'''Main entry point of the application'''

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from mgxhub.model.webapi import GameDetail
from mgxhub.handler import DBHandler

app = FastAPI()
db = DBHandler()

@app.get("/")
async def ping():
    '''Test the server is online or not'''

    return {"time": f"{datetime.now()}", "status": "online"}

@app.get("/system/langcodes")
async def get_langcodes() -> dict[str, list]:
    '''Get available language codes and their names.'''

    # Scan `translations/` directory for .po files to get available language codes
    lang_codes = []
    for file in os.listdir('translations/LC_MESSAGES/'):
        if file.endswith('.mo'):
            lang_codes.append(file[:-3])

    return {"lang_codes": lang_codes}

@app.get("/game/{game_guid}")
async def get_game(game_guid: str, lang: str = 'en') -> GameDetail | None:
    '''Get details for a game by its GUID.
    
    - **game_guid**: GUID of the game.
    - **lang**: Language code. Default is 'en'.
    '''

    details = db.get_game(game_guid, lang)

    if details:
        return details

    raise HTTPException(status_code=404, detail=f"Game profile [{game_guid}] not found.")
