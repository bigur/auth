__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger
from typing import Dict

from aiohttp.web import Request

from bigur.rx import Subject, Observer

from bigur.auth.model import User
from bigur.auth.oauth2.exceptions import InvalidRequest
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response

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


class AuthCodeEndpoint(Subject):

    def __init__(self, owner: User, params: Dict):
        self._owner = owner
        self._params = params
        super().__init__()

    async def subscribe(self, observer: Observer):
        await super().subscribe(observer)

        if 'response_type' not in self._params:
            await self.on_error(InvalidRequest('No response_type parameter'))
        else:
            response_type = self._params['response_type']
            if not isinstance(response_type, list):
                response_type = {response_type}
            else:
                response_type = set(response_type)

            if response_type == 'code':
                pass
            elif response_type == 'token':
                pass
            else:
                await self.on_error(
                    InvalidRequest('Invalid response_type value'))
        stream = AuthorizationCodeGrant()
