'''Communicate with WordPress to authenticate users.'''

# pylint: disable=import-error

from datetime import datetime
from urllib.parse import urljoin
import urllib3
import requests
from requests.auth import HTTPBasicAuth
from fastapi import HTTPException
from mgxhub.config import cfg
from mgxhub.logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGED_IN_CACHE = {}

class WPRestAPI:
    '''Communicate with WordPress REST API.'''

    _api_route = '/wp-json/wp/v2/users/me'
    _api_url = None

    def __init__(self, wp_cred: list | None = None):
        '''Initialize WordPress REST API client.'''

        if not wp_cred:
            self._username = cfg.get('wordpress', 'username')
            self._password = cfg.get('wordpress', 'password')
            self._url = cfg.get('wordpress', 'url')
        else:
            self._username = wp_cred[0]
            self._password = wp_cred[1]
            self._url = wp_cred[2]

        if not self._url or not self._username or not self._password:
            logger.warning('WordPress credentials are not set')
            self.creds_set = False
            return

        self._api_url = urljoin(self._url, self._api_route.lstrip('/'))

    def authenticate(self, admin: bool = False) -> bool:
        '''Authenticate user with WordPress.'''

        if not self.creds_set:
            return False
        
        if admin:
            params = {'context': 'edit'}
        else:
            params = {'context': 'view'}

        response = requests.get(
            self._api_url,
            params=params,
            auth=HTTPBasicAuth(self._username, self._password),
            verify=False,
            timeout=15
        )

        if response.status_code == 200:
            resp = response.json()
            if admin and isinstance(resp.get('roles'), list):
                return 'administrator' in resp['roles']
            return resp.get('name') == self._username

        logger.warning(f'Failed to authenticate user {self._username} with WordPress')
        return False

    def need_user_login(self, hint: str = 'Need user authentication', admin: bool = False, brutal_term: bool = True) -> bool:
        '''Check if user needs to login to WordPress.
        
        Args:
            hint: The hint message to be returned.
            admin: Whether to check if the user is an administrator.
            brutal_term: Whether to terminate the process if the user is not logged in.
        '''

        if self._username in LOGGED_IN_CACHE and\
                LOGGED_IN_CACHE[self._username] > datetime.now().timestamp() - 60 * int(cfg.get('wordpress', 'login_expire')):
            return True

        if self.authenticate(admin):
            LOGGED_IN_CACHE[self._username] = datetime.now().timestamp()
            return True

        if brutal_term:
            raise HTTPException(status_code=401, detail=hint)
        return False

    def need_admin_login(self, hint: str = 'Need admin authentication', brutal_term: bool = True) -> bool:
        '''Check if user needs to login to WordPress as an administrator.'''

        return self.need_user_login(hint, admin=True, brutal_term=brutal_term)
