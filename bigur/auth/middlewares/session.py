__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from uuid import uuid4
from logging import getLogger
from typing import Callable, Optional

from aiohttp.web import Request, Response, middleware
from aiohttp.web_exceptions import HTTPException

logger = getLogger(__name__)


def set_cookie(request: Request, response: Response, name: str, value: str):
    if request.app['config'].get('authn.cookie.secure'):
        cookie_secure: Optional[str] = 'yes'
    else:
        cookie_secure = None

    response.set_cookie(name, value, secure=cookie_secure, httponly='yes')


@middleware
async def session(request: Request, handler: Callable) -> Response:
    cookie_name: str = request.app['config'].get('authn.cookie.session_name')

    sid: Optional[str] = request.cookies.get(cookie_name)
    if sid is None:
        sid = uuid4().hex
        logger.debug('Generate new session id: %s', sid)
    else:
        logger.debug('Session id is: %s', sid)
    request['sid'] = sid

    try:
        response = await handler(request)
    except HTTPException as e:
        set_cookie(request, e, cookie_name, request['sid'])
        raise
    else:
        set_cookie(request, response, cookie_name, request['sid'])

    return response
