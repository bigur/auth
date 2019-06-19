__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, asdict
from hashlib import sha1
from typing import Dict, List, Union

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption)
from jwt import encode as jwt_encode


@dataclass
class Token:
    pass


@dataclass
class BearerToken(Token):
    pass


@dataclass
class JWT(BearerToken):

    def payload(self) -> Dict[str, Union[List[str], str]]:
        return asdict(self)


@dataclass
class RSAJWT(JWT):

    def encode(self, private_key: RSAPrivateKey) -> bytes:

        private_bytes = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=NoEncryption())

        public_key = private_key.public_key()
        numbers = public_key.public_numbers()
        n = numbers.n.to_bytes(int(public_key.key_size / 8),
                               'big').lstrip(b'\x00')

        kid = sha1(n).hexdigest()

        payload = self.payload()

        return jwt_encode(
            payload, private_bytes, algorithm='RS256', headers={'kid': kid})
