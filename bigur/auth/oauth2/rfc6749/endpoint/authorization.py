__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger

from aiohttp.web import Request

from bigur.auth.oauth2.rfc6749.errors import InvalidRequest
from bigur.auth.oauth2.rfc6749.request import OAuth2Request, OAuth2Response

logger = getLogger(__name__)


@dataclass
class AuthorizationRequest(OAuth2Request):
    pass


@dataclass
class AuthorizationResponse(OAuth2Response):
    pass


async def create_oauth2_request(request: Request):
    logger.debug('Creating request from POST method')
    # XXX: ignore unneeded parameters
    try:
        kwargs = await request.post()
        request['oauth2_request'] = AuthorizationRequest(  # type: ignore
            **(kwargs))
    except TypeError as e:
        raise InvalidRequest(str(e)[11:])
    else:
        return request
