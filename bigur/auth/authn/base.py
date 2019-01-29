__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request

from bigur.auth.model import User

logger = getLogger(__name__)


class AuthN:

    async def authenticate(self, http_request: Request) -> User:
        raise NotImplementedError
