__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from logging import getLogger
from typing import Optional, Set

from bigur.auth.store import store

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response

logger = getLogger(__name__)


@dataclass
class AuthorizationRequest(OAuth2Request):
    response_type: Set[str] = field(default_factory=set)
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None


@dataclass
class InvalidAuthorizationRequest(OAuth2Request):
    response_type: Set[str] = field(default_factory=set)
    redirect_uri: Optional[str] = None
    state: Optional[str] = None


@dataclass
class AuthorizationCodeResponse(OAuth2Response):
    code: str
    state: Optional[str] = None


@dataclass
class AccessTokenRequest(OAuth2Request):
    grant_type: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None


@dataclass
class InvalidAccessTokenRequest(OAuth2Request):
    grant_type: Optional[str] = None


@dataclass
class AccessTokenResponse(OAuth2Response):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


async def authorization_code_grant(
        context: Context) -> AuthorizationCodeResponse:
    access_code = await store.access_codes.create()
    return AuthorizationCodeResponse(
        code=access_code.code, state=context.oauth2_request.state)


async def get_token_by_code(context: Context) -> AccessTokenResponse:
    return AccessTokenResponse()
