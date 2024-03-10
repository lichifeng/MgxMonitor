'''Communicate with WordPress to authenticate users.'''

# pylint: disable=import-error

from hashlib import sha256
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
    _creds_set = True

    def __init__(self, username: str, password: str, wp_url: str | None = None):
        '''Initialize WordPress REST API client.'''

        if not wp_url:
            self._url = cfg.get('wordpress', 'url')
        else:
            self._url = wp_url

        self._username = username
        self._password = password
        
        if not self._url or not self._username or not self._password:
            logger.warning('WordPress credentials are not set')
            self._creds_set = False
            return

        self._api_url = urljoin(self._url, self._api_route.lstrip('/'))

    def authenticate(self, admin: bool = False) -> tuple[bool, list]:
        '''Authenticate user with WordPress.'''

        if not self._creds_set:
            return False
        
        params = {'context': 'edit'}

        response = requests.get(
            self._api_url,
            params=params,
            auth=HTTPBasicAuth(self._username, self._password),
            verify=False,
            timeout=15
        )

        if response.status_code == 200:
            resp = response.json()
            if not isinstance(resp.get('roles'), list):
                return False
            if admin:
                return 'administrator' in resp['roles'], resp.get('roles')
            return resp.get('name') == self._username, resp.get('roles')

        logger.warning(f'Failed to authenticate user {self._username} with WordPress')
        return False, []

    def need_user_login(self, hint: str = 'Need user authentication', need_admin: bool = False, brutal_term: bool = True) -> bool:
        '''Check if user needs to login to WordPress.
        
        Args:
            hint: The hint message to be returned.
            admin: Whether to check if the user is an administrator.
            brutal_term: Whether to terminate the process if the user is not logged in.
        '''

        user_hash = sha256((self._username + self._password).encode()).hexdigest()
        if user_hash in LOGGED_IN_CACHE and\
                LOGGED_IN_CACHE[user_hash]['created'] > datetime.now().timestamp() - 60 * int(cfg.get('wordpress', 'login_expire')):
            if need_admin:
                return 'administrator' in LOGGED_IN_CACHE[user_hash]['roles']
            return True

        authed, user_roles = self.authenticate(need_admin)
        if authed:
            LOGGED_IN_CACHE[user_hash] = {
                'created': datetime.now().timestamp(),
                'roles': user_roles
            }
            return True

        if brutal_term:
            raise HTTPException(status_code=401, detail=hint)
        return False

    def need_admin_login(self, hint: str = 'Need admin authentication', brutal_term: bool = True) -> bool:
        '''Check if user needs to login to WordPress as an administrator.'''

        return self.need_user_login(hint, need_admin=True, brutal_term=brutal_term)
