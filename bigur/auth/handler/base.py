__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import fields
from collections import defaultdict
from logging import getLogger
from typing import Any, Dict, List, Type
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from aiohttp.web import Response as HTTPResponse, View, json_response
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPInternalServerError)
from multidict import MultiDict
from rx import Observable

from bigur.auth.authn import authenticate_client, authenticate_end_user
from bigur.auth.oauth2.exceptions import (OAuth2FatalError,
                                          OAuth2RedirectionError)
from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.response import OAuth2Response, JSONResponse
from bigur.auth.utils import asdict

logger = getLogger(__name__)


class OAuth2Handler(View):

    def get_request_class(self, params: MultiDict) -> Type:
        raise NotImplementedError('Method must be implemented in child class')

    def create_stream(self, context: Context) -> Observable:
        raise NotImplementedError('Method must be implemented in child class')

    async def handle(self, params: MultiDict) -> HTTPResponse:
        http_request = self.request

        # Rebuild parameters without value, as in RFC 6794 sec. 3.1
        new_params = MultiDict()
        for k, v in params.items():
            if v:
                new_params.add(k, v)
        params = new_params

        # Authenticate end user
        user = await authenticate_end_user(http_request, params)

        # Authenticate client
        client = await authenticate_client(http_request, params)

        # Get request class
        request_class = self.get_request_class(params)

        # Create request
        kwargs = {}
        request_fields = {f.name for f in fields(request_class)}
        for k, v in params.items():
            if k in request_fields:
                kwargs[k] = v
        oauth2_request = request_class(**kwargs)
        context = Context(
            client=client,
            owner=user,
            http_request=http_request,
            http_params=params,
            oauth2_request=oauth2_request)

        # Prepare response
        response_params: Dict[str, Any] = {}

        fragment: Dict[str, List[str]] = defaultdict(list)
        query: Dict[str, List[str]] = defaultdict(list)

        try:
            oauth2_response = await self.create_stream(context)

        except Exception as exc:  # pylint: disable=broad-except
            logger.error('%s: %s', type(exc), exc, exc_info=exc)

            if isinstance(exc, OAuth2FatalError):
                raise HTTPBadRequest(reason=str(exc)) from exc

            if isinstance(exc, OAuth2RedirectionError):
                response_params['error'] = exc.error_code  # pylint: disable=no-member
                response_params['error_description'] = str(exc)

            else:
                raise HTTPInternalServerError() from exc

        else:
            if not oauth2_response:
                logger.error('OAuth2 response is not set')
                raise HTTPInternalServerError()

            if not isinstance(oauth2_response, OAuth2Response):
                logger.error('Invalid OAuth2 response: %s', oauth2_response)
                raise HTTPInternalServerError()

            if isinstance(oauth2_response, JSONResponse):
                return json_response(asdict(oauth2_response))

            response_params = asdict(oauth2_response)

        # Check if OpenID Connect's response mode is set
        response_part: Dict[str, List[str]]
        response_mode = getattr(oauth2_request, 'response_mode', 'fragment')

        if response_mode == 'query':
            response_part = query
        elif response_mode is None or response_mode == 'fragment':
            response_part = fragment
        else:
            logger.warning('Response mode %s not supported', response_mode)
            raise HTTPBadRequest(reason='Response mode not supported')

        for k, v in response_params.items():
            response_part[k].append(str(v))

        # Process redirect URI
        if oauth2_request.redirect_uri is None:
            logger.debug('Bad request: missing redirect_uri')
            raise HTTPBadRequest(reason='Missing \'redirect_uri\' parameter')

        url = urlparse(oauth2_request.redirect_uri)
        for k, v in parse_qs(url.query).items():
            query[k] += v

        # Log redirect
        mask_fields = {'code', 'access_token', 'refresh_token'}
        log_query = {
            key: key in mask_fields and 'xxx' or value
            for key, value in query.items()
        }
        log_fragment = {
            key: key in mask_fields and 'xxx' or value
            for key, value in fragment.items()
        }
        location = urlunparse((
            url.scheme,
            url.netloc,
            url.path,
            url.params,
            urlencode(log_query, doseq=True),
            urlencode(log_fragment, doseq=True),
        ))
        logger.debug('Redirecting to: %s', location)

        # Create response
        return HTTPResponse(
            status=303,
            headers={
                'Location':
                    urlunparse((url.scheme, url.netloc, url.path, url.params,
                                urlencode(query, doseq=True),
                                urlencode(fragment, doseq=True)))
            })
