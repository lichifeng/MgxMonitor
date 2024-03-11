from fastapi import APIRouter, Depends

from webapi.authdepends import need_admin_login

admin_api = APIRouter(dependencies=[Depends(need_admin_login)])
