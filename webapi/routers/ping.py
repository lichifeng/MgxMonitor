'''Get server online status'''

from datetime import datetime

from webapi import app


@app.get("/")
async def ping():
    '''Test the server is online or not
    
    Defined in: `webapi/routers/ping.py`
    '''

    return {"time": f"{datetime.now()}", "status": "online"}
