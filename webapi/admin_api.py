'''Used to wrap routes that require admin login'''

from fastapi import APIRouter, Depends

from webapi.authdepends import need_admin_login

admin_api = APIRouter(dependencies=[Depends(need_admin_login)])
