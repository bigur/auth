__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request, HTTPUnauthorized, HTTPForbidden
from multidict import MultiDict

from bigur.auth.store import store

from bigur.auth.oauth2.exceptions import InvalidClient

logger = getLogger(__name__)


# pylint: disable=unused-argument
async def authenticate_client(request: Request, params: MultiDict) -> None:
    '''This method do client authentication. If it finished sucessfull
    method return nothing, overwise raises exception.

    :returns: None
    :throw: :class:`~bigur.auth.oauth2.exceptions.InvalidClient`,
        :class:`~bigur.auth.oauth2.exceptions.InvalidRequest`'''
    if 'client_id' in params:
        client = await store.clients.get(params['client_id'])
        if client.client_type == 'public':
            if client.has_password():
                if 'client_secret' not in params:
                    raise InvalidClient('Client\'s credentials not specified.')
            else:
                if 'client_secret' not in params:
                    return client
        elif client.client_type == 'confidential':
            if 'client_secret' not in params:
                raise InvalidClient('Client\'s credentials not specified.')
        if not client.verify_password(params['client_secret']):
            raise InvalidClient('Invalid client\'s password.')
    else:
        raise InvalidClient('Parameter `client_id\' is not set.')

    return client
