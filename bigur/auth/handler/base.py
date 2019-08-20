__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from aiohttp.web import Response, View, json_response
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPInternalServerError)

from multidict import MultiDictProxy

from bigur.rx import ObserverBase

from bigur.auth.authn import authenticate_end_user
from bigur.auth.oauth2.endpoint import Endpoint
from bigur.auth.oauth2.exceptions import (OAuth2FatalError,
                                          OAuth2RedirectionError)
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response, JSONResponse
from bigur.auth.utils import asdict

logger = getLogger(__name__)


class ResultObserver(ObserverBase):

    def __init__(self, request: OAuth2Request):
        self._request = request
        self._response: Optional[OAuth2Response] = None

    def http_response(self):
        request = self._request
        response = self._response
        params: Dict[str, str] = {}

        fragment: Dict[str, str] = {}
        query: Dict[str, str] = {}

        if isinstance(response, JSONResponse):
            return json_response(asdict(response))

        elif isinstance(response, OAuth2FatalError):
            raise HTTPBadRequest(reason=str(response)) from response

        elif isinstance(response, OAuth2RedirectionError):
            params['error'] = response.error_code
            params['error_description'] = str(response)

        elif isinstance(response, Exception):
            logger.error('%s: %s', type(response), response, exc_info=response)
            raise HTTPInternalServerError() from response

        elif response is None:
            logger.error('OAUth2 response is not set')
            raise HTTPInternalServerError()

        else:
            params.update(asdict(response))
        logger.debug('Response params is %s', params)

        response_mode = getattr(request, 'response_mode', 'fragment')

        if response_mode == 'query':
            query.update(params)
        elif response_mode is None or response_mode == 'fragment':
            fragment.update(params)
        else:
            logger.warning('Response mode %s not supported', response_mode)
            raise HTTPBadRequest(reason='Response mode not supported')

        if request.redirect_uri is None:
            logger.debug('Bad request: missing redirect_uri')
            raise HTTPBadRequest(reason='Missing \'redirect_uri\' parameter')

        url = urlparse(request.redirect_uri)
        query.update(parse_qs(url.query))
        fragment.update(parse_qs(url.fragment))

        return Response(
            status=303,
            headers={
                'Location':
                    urlunparse((url.scheme, url.netloc, url.path, url.params,
                                urlencode(query, doseq=True),
                                urlencode(fragment, doseq=True)))
            })

    async def on_next(self, response: OAuth2Response) -> None:
        logger.debug('Processing response: %s', response)
        self._response = response

    async def on_error(self, error: Exception):
        logger.debug('Processing response error: %s', error)
        self._response = error

    async def on_completed(self):
        logger.debug('Request process finished')


class OAuth2Handler(View):

    __request_class__: OAuth2Request
    __endpoint__: Endpoint

    async def handle(self, params: MultiDictProxy) -> Response:
        request = self.request
        app = request.app

        request['params'] = params

        await authenticate_end_user(request)

        oauth2_request = self.__request_class__(
            owner=request['user'],
            jwt_keys=app['jwt_keys'],
            config=app['config'],
            **params)
        stream = self.__endpoint__(oauth2_request)

        result = ResultObserver(oauth2_request)
        try:
            await stream.subscribe(result)
        except Exception as e:
            logger.error('Unknown exception while process request', exc_info=e)
            raise HTTPInternalServerError() from e

        return result.http_response()

    async def get(self) -> Response:
        return await self.handle(self.request.query)

    async def post(self) -> Response:
        return await self.handle(await self.request.post())
