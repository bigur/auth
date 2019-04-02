__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import Dict, List, Optional, Type
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from aiohttp.web import Request, Response, View
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPInternalServerError,
                                    HTTPSeeOther)

from bigur.rx import ObserverBase

from bigur.auth.authn import authenticate_end_user
from bigur.auth.oauth2.exceptions import (OAuth2FatalError, OAuth2RedirectError)
from bigur.auth.oauth2.response import OAuth2Response
from bigur.auth.utils import asdict

logger = getLogger(__name__)


class ResultObserver(ObserverBase):

    def __init__(self, request: Request):
        self._request = request
        self._responses: List[OAuth2Response] = []

        self.response: Optional[Response] = None

    async def on_next(self, response: OAuth2Response) -> None:
        self._responses.append(response)

    async def on_error(self, error: Exception):
        if isinstance(error, OAuth2FatalError):
            logger.debug('Return HTTPBadRequest("%s")', str(error))
            raise HTTPBadRequest(reason=str(error))

        elif isinstance(error, OAuth2RedirectError):
            # TODO: check oidc's response_mode parameter
            # TODO: check prompt parameter
            logger.debug('Redirect with error: %s', error.location)
            raise HTTPSeeOther(error.location)

        else:
            logger.error('Internal server error', exc_info=error)
            raise HTTPInternalServerError()

    async def on_completed(self):
        logger.debug('Request process finished')

        params: Dict[str, str] = {}
        for response in self._responses:
            print(response)
            params.update(asdict(response))

        fragment: Dict[str, str] = {}
        query: Dict[str, str] = {}

        logger.warning('Hardcoded response mode: fragment')
        mode = 'fragment'
        if mode == 'fragment':
            fragment = params
        elif mode == 'query':
            query = params
        else:
            raise NotImplementedError('response mode not implemented')

        url = urlparse(self._request['params']['redirect_uri'])
        query.update(parse_qs(url.query))
        fragment.update(parse_qs(url.fragment))

        self.response = Response(
            status=303,
            headers={
                'Location':
                    urlunparse((url.scheme, url.netloc, url.path, url.params,
                                urlencode(query, doseq=True),
                                urlencode(fragment, doseq=True)))
            })


class OAuth2Handler(View):

    __endpoint__: Type

    async def handle(self):
        request = self.request
        owner = await authenticate_end_user(request)

        stream = self.__endpoint__(owner=owner, params=request['params'])

        result = ResultObserver(request)
        await stream.subscribe(result)

        return result.response

    async def get(self):
        self.request['params'] = self.request.query
        return await self.handle()

    async def post(self):
        self.request['params'] = await self.request.post()
        return await self.handle()
