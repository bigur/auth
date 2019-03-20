__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode
from hashlib import sha1
from logging import getLogger

from aiohttp.web import View, json_response

logger = getLogger(__name__)


class JWKSHandler(View):
    '''Handler returns public JWKs.'''

    async def get(self):
        result = []
        for private_key in self.request.app['jwt_keys']:
            key = private_key.public_key()
            numbers = key.public_numbers()
            e = numbers.e.to_bytes(4, 'big').lstrip(b'\x00')
            n = numbers.n.to_bytes(int(key.key_size / 8), 'big').lstrip(b'\x00')
            result.append({
                'e': urlsafe_b64encode(e).decode('utf-8'),
                'kty': 'RSA',
                'alg': 'RSA256',
                'n': urlsafe_b64encode(n).decode('utf-8'),
                'use': 'sig',
                'kid': sha1(n).hexdigest()
            })
        return json_response({'keys': result})
