'''List online users.

Logged in users are cached for a period of time. This endpoint returns the
current list of cached users.
'''

from mgxhub.auth import LOGGED_IN_CACHE
from webapi.admin_api import admin_api


@admin_api.get("/auth/onlineusers")
async def list_online_users() -> dict:
    '''Check if a user is logged in

    Defined in: `webapi/routers/auth_onlineusers.py`
    '''

    return LOGGED_IN_CACHE
