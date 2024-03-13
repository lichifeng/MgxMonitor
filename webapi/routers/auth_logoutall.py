'''Logout all users'''

from mgxhub.auth import LOGGED_IN_CACHE
from webapi.admin_api import admin_api


@admin_api.get("/auth/logoutall")
async def logout_all_users() -> dict:
    '''Logout all users

    Defined in: `webapi/routers/auth_logoutall.py`
    '''

    LOGGED_IN_CACHE.clear()
    return {"status": "All users was logged out"}
