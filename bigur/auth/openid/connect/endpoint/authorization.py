__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from logging import getLogger
from typing import List, Optional

from aiohttp.web import Request

from bigur.auth.oauth2.rfc6749.endpoint.authorization import (
    AuthorizationRequest as OAuth2AuthorizationRequest, AuthorizationResponse as
    OAuth2AuthorizationResponse)
from bigur.auth.oauth2.rfc6749.request import create_request

logger = getLogger(__name__)


@dataclass
class AuthorizationRequest(OAuth2AuthorizationRequest):
    scope: List[str]
    response_type: List[str]
    client_id: str
    redirect_uri: str
    state: Optional[str] = None
    response_mode: Optional[str] = None
    nonce: Optional[str] = None
    display: Optional[str] = None
    user: Optional[str] = None
    acr_values: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.response_type = [x.strip() for x in self.response_type.split(' ')]
        if isinstance(self.acr_values, str):
            self.acr_values = [x.strip() for x in self.acr_values.split(' ')]


@dataclass
class AuthorizationResponse(OAuth2AuthorizationResponse):
    pass


async def create_oidc_request(request: Request) -> Request:
    logger.debug('Creating OIDC Authorization request object')
    return await create_request(AuthorizationRequest, request)


async def create_response(request: Request) -> Request:
    logger.debug('Creating response')
    response = AuthorizationResponse()
    request['oauth2_responses'].append(response)
    return request
