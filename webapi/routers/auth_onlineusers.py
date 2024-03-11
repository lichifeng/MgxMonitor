'''Check if a user is logged in'''

from mgxhub.auth import LOGGED_IN_CACHE
from webapi.admin_api import admin_api


@admin_api.get("/auth/onlineusers")
async def list_online_users() -> dict:
    '''Check if a user is logged in
    
    Defined in: `webapi/routers/auth_onlineusers.py`
    '''

    return LOGGED_IN_CACHE
