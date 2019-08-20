__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field, fields
from logging import getLogger
from typing import List, Optional, Set

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from kaptan import Kaptan

from bigur.auth.model import Client
from bigur.auth.oauth2.token import Token

logger = getLogger(__name__)


@dataclass
class BaseRequest:
    # Resource owner
    owner: str

    # Configured RSA JWT keys
    config: Kaptan
    jwt_keys: List[RSAPrivateKey]


@dataclass
class OAuth2Request(BaseRequest):

    # RFC 6749 parameters
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    response_type: Set[str] = field(default_factory=set)

    scope: Set[str] = field(default_factory=set)
    state: Optional[str] = None

    # Internal parameters
    client: Optional[Client] = None

    access_token: Optional[Token] = None
    refresh_token: Optional[Token] = None

    def __post_init__(self):
        keys = {x.name for x in fields(self) if x.type == Set[str]}
        for key in keys:
            value = getattr(self, key, None)
            if value is None:
                setattr(self, key, set())
            elif isinstance(value, str):
                setattr(self, key, {x for x in value.split() if x})
