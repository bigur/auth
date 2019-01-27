__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from aiohttp.web import Request, Response
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPInternalServerError,
                                    HTTPSeeOther)

from bigur.rx import ObserverBase, Subject
from bigur.rx import operators as op

from bigur.auth.authn import authenticate_resource_owner
from bigur.auth.oauth2.rfc6749.grant import implicit_grant
from bigur.auth.oauth2.rfc6749.errors import (OAuth2FatalError,
                                              OAuth2RedirectError)
from bigur.auth.openid.connect.endpoint.authorization import (
    create_oidc_request)

logger = getLogger(__name__)


class ResultObserver(ObserverBase[Request]):

    def __init__(self, request):
        self.request = request
        self.response = None
        super().__init__()

    async def on_next(self, request: Request):
        logger.debug('on_next')
        self.response = Response(text='response')

    async def on_error(self, error: Exception):
        if isinstance(error, OAuth2FatalError):
            logger.debug('Return HTTPBadRequest("%s")', str(error))
            raise HTTPBadRequest(reason=str(error))

        elif isinstance(error, OAuth2RedirectError):
            # TODO: check oauth2 response mode
            location = error.http_request['oauth2_request'].redirect_uri

            parts = urlparse(location)

            query = parse_qs(parts.query)

            query['error'] = [error.error_code]
            query['error_description'] = [str(error)]

            state = error.http_request['oauth2_request'].state
            if state is not None:
                query['state'] = state

            location = urlunparse(
                (parts.scheme, parts.netloc, parts.path, parts.params,
                 urlencode(query, doseq=True), parts.fragment))

            logger.debug('Redirect with error: %s', location)

            raise HTTPSeeOther(location)

        else:
            logger.error('Internal server error', exc_info=error)
            raise HTTPInternalServerError()

    async def on_completed(self):
        logger.debug('Request process finished')


async def authorization_handler(request: Request):

    request['oauth2_request'] = None
    request['oauth2_responses'] = []

    stream = Subject()

    base_branch = (
        stream
        | op.map(create_oidc_request)
        | op.map(authenticate_resource_owner))
    # check redirect uri

    implicit_grant_branch = (
        base_branch
        | op.filter(lambda x: 'token_id' in x['oauth2_request'].response_type)
        | op.map(implicit_grant))

    result_branch = op.concat(implicit_grant_branch)

    result = ResultObserver(request)
    await result_branch.subscribe(result)

    await stream.on_next(request)

    return result.response
