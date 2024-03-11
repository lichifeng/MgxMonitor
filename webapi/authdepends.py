'''Auth routers for FastAPI'''

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from mgxhub.auth.wordpress import WPRestAPI

security = HTTPBasic()


def need_admin_login(credentials: HTTPBasicCredentials = Depends(security)):
    '''Check if user needs to login as admin to WordPress.'''

    WPRestAPI(credentials.username, credentials.password).need_admin_login()
    return credentials


def need_user_login(credentials: HTTPBasicCredentials = Depends(security)):
    '''Check if user needs to login to WordPress.'''

    WPRestAPI(credentials.username, credentials.password).need_user_login()
    return credentials
