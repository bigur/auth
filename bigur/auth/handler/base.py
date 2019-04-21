__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from aiohttp.web import Response, View
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPInternalServerError)

from multidict import MultiDictProxy

from bigur.rx import ObserverBase

from bigur.auth.authn import authenticate_end_user
from bigur.auth.oauth2.endpoint import Endpoint
from bigur.auth.oauth2.exceptions import (OAuth2FatalError,
                                          OAuth2RedirectionError)
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response
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

        if isinstance(response, OAuth2FatalError):
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

        response_mode = getattr(request, 'response_mode', 'fragment')

        if response_mode == 'query':
            query.update(params)
        elif response_mode == 'fragment':
            fragment.update(params)
        else:
            raise HTTPBadRequest(reason='Response mode not supported')

        if request.redirect_uri is None:
            raise HTTPBadRequest(reason='Redirect uri is not set')

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
        self._response = response

    async def on_error(self, error: Exception):
        self._response = error

    async def on_completed(self):
        logger.debug('Request process finished')


class OAuth2Handler(View):

    __endpoint__: Endpoint

    async def handle(self, params: MultiDictProxy) -> Response:
        owner = await authenticate_end_user(self.request)

        oauth2_request = OAuth2Request(owner=owner, **params)
        stream = self.__endpoint__(oauth2_request)

        result = ResultObserver(oauth2_request)
        await stream.subscribe(result)

        return result.http_response()

    async def get(self) -> Response:
        return await self.handle(self.request.query)

    async def post(self) -> Response:
        return await self.handle(await self.request.post())
