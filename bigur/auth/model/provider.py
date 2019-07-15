__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from aiohttp import ClientSession

from bigur.auth.model.abc import AbstractProvider
from bigur.auth.model.base import Object


@dataclass
class Provider(Object, AbstractProvider):
    issuer: str
    authorization_endpoint: str
    jwks_uri: str
    response_types_supported: List[str]
    subject_types_supported: List[str]
    id_token_signing_alg_values_supported: List[str]
    client_id: str
    client_secret: str
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    revocation_endpoint: Optional[str] = None
    scopes_supported: List[str] = field(default_factory=list)
    token_endpoint_auth_methods_supported: List[str] = field(
        default_factory=list)
    claims_supported: List[str] = field(default_factory=list)
    code_challenge_methods_supported: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    keys: Optional[Dict[str, Dict[str, str]]] = None

    def get_authorization_endpoint(self):
        return self.authorization_endpoint

    def get_token_endpoint(self):
        return self.token_endpoint

    def get_response_types_supported(self):
        if not self.response_types_supported:
            return []
        return self.response_types_supported

    def get_scopes_supported(self):
        if not self.scopes_supported:
            return []
        return self.scopes_supported

    def get_client_id(self):
        return self.client_id

    def get_client_secret(self):
        return self.client_secret

    def get_key(self, kid: str) -> Dict[str, str]:
        if self.keys:
            return self.keys[kid]
        raise KeyError('Key with kid {} not found'.format(kid))

    async def update_keys(self):
        async with ClientSession() as session:
            async with session.get(self.jwks_uri) as response:
                keys = (await response.json())['keys']
                self.keys = {x['kid']: x for x in keys}

    def __str__(self):
        return '<{}({})>'.format(type(self).__name__, self.id)
