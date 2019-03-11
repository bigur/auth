__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import asdict
from logging import getLogger
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from aiohttp.web import Request, Response, View
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPInternalServerError,
                                    HTTPSeeOther)

from bigur.rx import ObserverBase, Subject
from bigur.rx import operators as op

from bigur.auth.authn import authenticate_end_user
from bigur.auth.oauth2.rfc6749.grant import implicit_grant
from bigur.auth.oauth2.rfc6749.errors import (OAuth2FatalError,
                                              OAuth2RedirectError)
from bigur.auth.oauth2.rfc6749.validators import (
    validate_client_id, authorize_client, validate_redirect_uri,
    validate_response_types, validate_scopes)
from bigur.auth.openid.connect.endpoint.authorization import (
    create_oidc_request)

from bigur.auth.openid.connect.grant import (implicit_grant as
                                             openid_implicit_grant)

logger = getLogger(__name__)


class ResultObserver(ObserverBase[Request]):

    def __init__(self, request: Request):
        self.request = request
        self.response: Optional[Response] = None
        super().__init__()

    async def on_next(self, request: Request) -> None:
        fragment: Dict[str, str] = {}
        query: Dict[str, str] = {}

        for oauth2_response in request['oauth2_responses']:
            if oauth2_response.mode == 'fragment':
                fragment.update(asdict(oauth2_response))
            elif oauth2_response.mode == 'query':
                query.update(asdict(oauth2_response))

        logger.debug('on_next: %s, %s', fragment, query)
        url = urlparse(request['oauth2_request'].redirect_uri)
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


class AuthorizeView(View):

    async def authorize(self):
        self.request['oauth2_request'] = None
        self.request['oauth2_responses'] = []

        stream = Subject()

        base_branch = (
            stream
            | op.map(create_oidc_request)
            | op.map(validate_client_id)
            | op.map(authorize_client)
            | op.map(validate_redirect_uri)
            | op.map(authenticate_end_user)
            | op.map(validate_response_types)
            | op.map(validate_scopes))
        # create token

        implicit_grant_branch = (
            base_branch
            | op.filter(lambda request: 'token_id' in request['oauth2_request'].
                        response_type)
            | op.map(openid_implicit_grant))

        result_branch = op.concat(implicit_grant_branch)

        result = ResultObserver(self.request)
        await result_branch.subscribe(result)

        await stream.on_next(self.request)
        await stream.on_completed()

        return result.response

    async def get(self):
        return await self.authorize()

    async def post(self):
        return await self.authorize()
