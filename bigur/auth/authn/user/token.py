__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from urllib.parse import urlencode

from aiohttp.web import HTTPSeeOther

from bigur.auth.oauth2.token import RSAJWT

from bigur.auth.authn.user.base import AuthN

logger = getLogger(__name__)


class Token(AuthN):

    async def authenticate(self):
        request = self.request
        params = request['params']

        token_bytes = request.headers.get('Authorization', '')
        token_bytes = token_bytes.lstrip('Bearer').strip()
        user_id = RSAJWT.decode(request.app['jwt_keys'][0], token_bytes)

        if user_id is None:
            reason = 'Invalid token'
            raise HTTPSeeOther('{}?{}'.format(
                request.app['config'].get('http_server.endpoints.login.path'),
                urlencode({
                    'error':
                        'bigur_token_error',
                    'error_description':
                        reason,
                    'next': ('{}?{}'.format(request.path,
                                            urlencode(query=params,
                                                      doseq=True))),
                })))

        return user_id
