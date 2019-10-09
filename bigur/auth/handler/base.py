__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import fields
from collections import defaultdict
from logging import getLogger
from re import sub as re_sub
from typing import Any, Dict, List, Type, Union
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from aiohttp.web import Response as HTTPResponse, View, json_response
from aiohttp.web_exceptions import (HTTPException, HTTPBadRequest,
                                    HTTPInternalServerError, HTTPUnauthorized)
from multidict import MultiDict
from rx import Observable

from bigur.auth.authn import authenticate_client, authenticate_end_user
from bigur.auth.oauth2.exceptions import (
    HTTPRequestError,
    InvalidClient,
    OAuth2Error,
    ServerError,
)
from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.response import OAuth2Response
from bigur.auth.utils import asdict

logger = getLogger(__name__)


class OAuth2Handler(View):

    def get_request_class(self, params: MultiDict) -> Type:
        raise NotImplementedError('Method must be implemented in child class')

    def create_stream(self, context: Context) -> Observable:
        raise NotImplementedError('Method must be implemented in child class')

    def get_response_mode(self, context: Context) -> str:
        '''Returns string that represent mode to response on request. String
        must be `query`, `fragment` or `json`.

        :returns: string with response mode.'''
        raise NotImplementedError('Method must be implemented in child class')

    def create_response(
            self,
            context: Context,
            oauth2_response: Union[OAuth2Response, Exception],
    ) -> HTTPResponse:

        if (not oauth2_response or
                not isinstance(oauth2_response, (OAuth2Response, OAuth2Error))):
            logger.error('OAuth2 response is not set')
            oauth2_response = ServerError('Internal server error.')

        # Initialize respones parameters.
        response_params: Dict[str, Any] = {}

        if isinstance(oauth2_response, OAuth2Response):
            response_params = asdict(oauth2_response)
        elif isinstance(oauth2_response, OAuth2Error):
            class_name = type(oauth2_response).__name__
            error_code = re_sub(
                '([a-z0-9])([A-Z])',
                r'\1_\2',
                re_sub(
                    '(.)([A-Z][a-z]+)',
                    r'\1_\2',
                    class_name,
                ),
            ).lower()
            response_params['error'] = error_code.lower()
            response_params['error_description'] = str(oauth2_response.args[0])

        # Detect response mode
        response_mode = self.get_response_mode(context)

        # Process json response
        if response_mode == 'json':
            if isinstance(oauth2_response, InvalidClient):
                response_status = 401
            elif isinstance(oauth2_response, OAuth2Error):
                response_status = 400
            else:
                response_status = 200
            return json_response(response_params, status=response_status)

        # Process 401 exceptions
        if isinstance(oauth2_response, InvalidClient):
            raise HTTPUnauthorized(reason=str(oauth2_response.args[0]))

        # Update query and fragment parameters
        query: Dict[str, List[str]] = defaultdict(list)
        fragment: Dict[str, List[str]] = defaultdict(list)
        if response_mode == 'query':
            for k, v in response_params.items():
                query[k].append(str(v))
        elif response_mode == 'fragment':
            for k, v in response_params.items():
                fragment[k].append(str(v))
        else:
            logger.error('Response mode %s not supported', response_mode)
            raise HTTPInternalServerError()

        # Check redirect URI
        logger.debug('Response params: %s', response_params)
        redirect_uri = getattr(context.oauth2_request, 'redirect_uri', None)
        if not redirect_uri:
            logger.error('Parameter `redirect_uri\' is not set.')
            raise HTTPInternalServerError()

        # Merge query with redirect_uri's query
        url = urlparse(redirect_uri)
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

    async def handle(self, params: MultiDict) -> HTTPResponse:
        http_request = self.request

        # Rebuild parameters without value, as in RFC 6794 sec. 3.1
        new_params = MultiDict()
        for k, v in params.items():
            if v:
                new_params.add(k, v)
        params = new_params

        logger.debug('Request params: %s', params)

        # Create context
        context = Context(http_request=http_request, http_params=params)

        try:
            # Authenticate end user
            context.owner = await authenticate_end_user(http_request, params)

            # Authenticate client
            context.client = await authenticate_client(http_request, params)

            # Get request class
            request_class = self.get_request_class(params)

            # Create OAuth2 request
            kwargs = {}
            request_fields = {f.name for f in fields(request_class)}
            for k, v in params.items():
                if k in request_fields:
                    kwargs[k] = v
            context.oauth2_request = request_class(**kwargs)

            # Prepare response
            oauth2_response = await self.create_stream(context)

        except HTTPException as exc:
            return exc

        except HTTPRequestError as exc:
            raise HTTPBadRequest(reason=str(exc.args[0]))

        except OAuth2Error as exc:
            oauth2_response = exc

        except Exception as exc:  # pylint: disable=broad-except
            logger.error('%s: %s', type(exc), exc, exc_info=exc)
            oauth2_response = ServerError('Unexpected server error, '
                                          'please try later.')

        return self.create_response(context, oauth2_response)
