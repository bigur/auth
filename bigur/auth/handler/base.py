__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import Any, Callable, Dict
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from aiohttp.web import Response, View, json_response
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPInternalServerError)
from rx import Observable
from multidict import MultiDictProxy

from bigur.auth.authn import authenticate_end_user
from bigur.auth.oauth2.exceptions import (OAuth2FatalError,
                                          OAuth2RedirectionError)
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response, JSONResponse
from bigur.auth.utils import asdict

logger = getLogger(__name__)


class OAuth2Handler(View):

    __request_class__: OAuth2Request
    __get_stream__: Callable[[], Observable]

    async def handle(self, params: MultiDictProxy) -> Response:
        http_request = self.request
        http_request['params'] = params

        await authenticate_end_user(http_request)

        app = http_request.app
        oauth2_request = self.__request_class__(
            owner=http_request['user'],
            jwt_keys=app['jwt_keys'],
            config=app['config'],
            **params)

        response_params: Dict[str, Any] = {}

        fragment: Dict[str, str] = {}
        query: Dict[str, str] = {}

        try:
            oauth2_response = await type(self).__get_stream__(oauth2_request)

        except Exception as exc:
            logger.error('%s: %s', type(exc), exc, exc_info=exc)

            if isinstance(exc, OAuth2FatalError):
                raise HTTPBadRequest(reason=str(exc)) from exc

            elif isinstance(exc, OAuth2RedirectionError):
                response_params['error'] = exc.error_code
                response_params['error_description'] = str(exc)

            else:
                raise HTTPInternalServerError()

        else:
            if not oauth2_response:
                logger.error('OAuth2 response is not set')
                raise HTTPInternalServerError()

            elif not isinstance(oauth2_response, OAuth2Response):
                logger.error('Invalid OAuth2 response: %s', oauth2_response)
                raise HTTPInternalServerError()

            elif isinstance(oauth2_response, JSONResponse):
                return json_response(asdict(oauth2_response))

            response_params = asdict(oauth2_response)
            logger.debug('Response params is %s', response_params)

        # Check if OpenID Connect's response mode is set
        response_mode = getattr(oauth2_request, 'response_mode', 'fragment')

        if response_mode == 'query':
            query.update(response_params)
        elif response_mode is None or response_mode == 'fragment':
            fragment.update(response_params)
        else:
            logger.warning('Response mode %s not supported', response_mode)
            raise HTTPBadRequest(reason='Response mode not supported')

        # Process redirect URI
        if oauth2_request.redirect_uri is None:
            logger.debug('Bad request: missing redirect_uri')
            raise HTTPBadRequest(reason='Missing \'redirect_uri\' parameter')

        url = urlparse(oauth2_request.redirect_uri)
        query.update(parse_qs(url.query))
        fragment.update(parse_qs(url.fragment))

        # Create response
        return Response(
            status=303,
            headers={
                'Location':
                    urlunparse((url.scheme, url.netloc, url.path, url.params,
                                urlencode(query, doseq=True),
                                urlencode(fragment, doseq=True)))
            })

    async def get(self) -> Response:
        return await self.handle(self.request.query)

    async def post(self) -> Response:
        return await self.handle(await self.request.post())
