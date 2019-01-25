__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request, Response
from aiohttp.web_exceptions import HTTPBadRequest, HTTPInternalServerError

from bigur.rx import ObserverBase, Subject
from bigur.rx import operators as op

from bigur.auth.authn import authenticate_resource_owner
from bigur.auth.oauth2.rfc6749.grant import implicit_grant
from bigur.auth.oauth2.rfc6749.errors import (
    OAuth2FatalError, OAuth2RedirectError)
from bigur.auth.openid.connect.endpoint.authorization import (
    create_oidc_request)


logger = getLogger(__name__)


class ResultObserver(ObserverBase[Request]):

    def __init__(self, request):
        self.request = request
        self.response = None
        super().__init__()

    async def on_next(self, response: Response):
        assert isinstance(response, Response)

        self.response = response

    async def on_error(self, error: Exception):
        if isinstance(error, OAuth2FatalError):
            logger.debug('Return HTTPBadRequest("%s")', str(error))
            raise HTTPBadRequest(reason=str(error))

        elif isinstance(error, OAuth2RedirectError):
            # TODO: check oauth2 response mode
            # XXX: must redirect
            self.response = Response(text='error')
            logger.warning('Error redirect stub')

        else:
            logger.error('Internal server error', exc_info=error)
            raise HTTPInternalServerError()

    async def on_completed(self):
        logger.debug('Request process finished')


async def authorization_handler(request: Request):

    stream = Subject()

    xs = (
        stream
        | op.map(create_oidc_request)
        | op.map(authenticate_resource_owner)
        # | op.map(validate_response_type)
    )

    (xs
        | op.filter(lambda x:
                    x['oauth2_request'].response_type == {'id_token'} or
                    x['aouth2_request'])
        | op.map(implicit_grant))

    # await xs.subscribe(impicit_stream)

    result = ResultObserver(request)

    await xs.subscribe(result)
    await stream.on_next(request)

    return result.response
