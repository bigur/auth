__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from oauthlib.oauth2 import RequestValidator

logger = getLogger('bigur.auth.oidc_validator')


class OIDCValidator(RequestValidator):

    async def authenticate_client(self, *args, **kwargs):
        logger.debug('Авторизация клиентd')
        return False
