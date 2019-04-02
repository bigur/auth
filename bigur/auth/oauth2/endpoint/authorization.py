__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger

from multidict import MultiDictProxy

from bigur.rx import Subject, ObserverBase, ObservableBase, operators as op

from bigur.auth.model import User
from bigur.auth.oauth2.exceptions import InvalidRequest
from bigur.auth.oauth2.request import OAuth2Request, create_request
from bigur.auth.oauth2.response import OAuth2Response
from bigur.auth.oauth2.validators import (
    validate_client_id, authenticate_client, validate_redirect_uri)

logger = getLogger(__name__)


@dataclass
class AuthCodeRequest(OAuth2Request):
    pass


@dataclass
class AccessTokenRequest(OAuth2Request):
    pass


@dataclass
class InvalidResponseTypeRequest(OAuth2Request):
    pass


@dataclass
class AuthorizationResponse(OAuth2Response):
    pass


class AuthorizationEndpoint(ObserverBase, ObservableBase):

    def __init__(self, owner: User, params: MultiDictProxy):
        self._owner = owner
        self._params = params
        self._observer: ObserverBase = None
        super().__init__()

    def authorization_code_stream(self, stream) -> ObservableBase:
        pass

    def access_token_stream(self, stream) -> ObservableBase:
        pass

    def invalid_response_type_stream(self, stream,
                                     description: str) -> ObservableBase:

        def raise_invalid_request(request: OAuth2Request):
            raise InvalidRequest(request, description)

        return (stream
                | op.map(validate_client_id)
                | op.map(authenticate_client)
                | op.map(validate_redirect_uri)
                | op.map(raise_invalid_request))

    async def _subscribe(self, observer: ObserverBase):
        self._observer = observer

        stream = Subject()

        try:
            response_types = self._params.getall('response_type')
            if len(response_types) > 1:
                raise ValueError('Multiple values in response_type '
                                 'are not allowed')

            response_type = response_types[0]

            # Access core request
            if response_type == 'code':
                request_type = AuthCodeRequest
                xs = self.authorization_code_stream(stream)

            # Token request with implicit grant
            elif response_type == 'token':
                request_type = AccessTokenRequest
                xs = self.access_token_stream(stream)

            # Invalid response_type value
            else:
                raise ValueError('Invalid response_type value')

        except (KeyError, ValueError) as e:
            # Invalid response_type value. This exception we must
            # raise with redirection to client's endpoint, but first
            # of all we must check client and validate redirect_uri.
            if isinstance(e, KeyError):
                description = 'Missing response_type parameter'
            else:
                description = str(e)

            request_type = InvalidResponseTypeRequest
            xs = self.invalid_response_type_stream(stream, description)

        request = await create_request(request_type, self._owner, self._params)

        await xs.subscribe(self)

        await stream.on_next(request)
        await stream.on_completed()

    async def on_next(self, response: OAuth2Response):
        await self._observer.on_next(response)

    async def on_error(self, error: Exception):
        await self._observer.on_error(error)

    async def on_completed(self):
        await self._observer.on_completed()
