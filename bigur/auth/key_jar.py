__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from hashlib import sha1
from logging import getLogger
from typing import Dict

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.backends.openssl.rsa import RSAPrivateKeyWithSerialization
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
    load_pem_private_key,
)
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

from bigur.auth.config import config

logger = getLogger(__name__)


class KeyJar:

    __instance: 'KeyJar' = None

    @classmethod
    def instance(cls):
        if not cls.__instance:
            cls.__instance = KeyJar()
        return cls.__instance

    @staticmethod
    def key_id(private_key: RSAPrivateKeyWithSerialization):
        public_key = private_key.public_key()
        numbers = public_key.public_numbers()
        n = numbers.n.to_bytes(
            int(public_key.key_size / 8),
            'big',
        ).lstrip(b'\x00')
        return sha1(n).hexdigest()

    def __init__(self):
        self._keys: Dict[str, RSAPrivateKeyWithSerialization] = {}
        self.load_keys()

        type(self).__instance = self

    def load_keys(self):
        backend = default_backend()
        filenames = config.get('oauth2.jwt_keys', [])
        for jwt_key_file in filenames:
            try:
                with open(jwt_key_file, 'rb') as fh_jwt_read:
                    key = load_pem_private_key(
                        fh_jwt_read.read(),
                        password=None,
                        backend=backend,
                    )
                    self._keys[self.key_id(key)] = key

            except OSError as exc:
                logger.error('Error while load jwt key file: %s', exc)

        if not self._keys:
            logger.warning('No jwt keys, generate new one...')
            for filename in filenames:
                key = generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=backend,
                )
                self._keys[self.key_id(key)] = key

                try:
                    with open(filename, 'w') as fh_jwt_write:
                        pem = key.private_bytes(
                            encoding=Encoding.PEM,
                            format=PrivateFormat.TraditionalOpenSSL,
                            encryption_algorithm=NoEncryption(),
                        )
                        fh_jwt_write.write(pem.decode('utf-8'))
                except OSError as e:
                    logger.error('Error while save generated key: %s', e)
