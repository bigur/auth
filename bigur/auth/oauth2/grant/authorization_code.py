__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from logging import getLogger
from typing import Optional, Set

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response

logger = getLogger(__name__)


@dataclass
class InvalidRequest(OAuth2Request):
    response_type: Set[str] = field(default_factory=set)
    redirect_uri: Optional[str] = None
    state: Optional[str] = None


@dataclass
class AuthorizationRequest(OAuth2Request):
    response_type: Set[str] = field(default_factory=set)
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None


@dataclass
class AuthorizationCodeResponse(OAuth2Response):
    code: str
    state: Optional[str] = None


@dataclass
class TokenResponse(OAuth2Response):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    state: Optional[str] = None


async def authorization_code_grant(
        context: Context) -> AuthorizationCodeResponse:
    logger.warning('Authorization code grant stub')
    return AuthorizationCodeResponse(
        code='stub', state=context.oauth2_request.state)


async def get_token_by_code(context: Context) -> AuthorizationCodeResponse:
    pass
