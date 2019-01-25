__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger
from typing import List, Optional

from aiohttp.web import Request

from bigur.auth.oauth2.rfc6749.endpoint.authorization import (
    AuthorizationRequest as OAuth2AuthorizationRequest)
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


async def create_oidc_request(http_request: Request):
    logger.debug('Creating OIDC Authorization request object')
    return await create_request(AuthorizationRequest, http_request)
