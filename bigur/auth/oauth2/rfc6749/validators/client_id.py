__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from bigur.auth.model import Client


logger = getLogger('bigur.auth.oauth2.rfc6749.validators')


async def validate_client_id(client_id: str):
    if client_id:
        client = await Client.find_one({'_id': client_id})
        if client is not None:
            return True
    return False
