__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from typing import Dict, List, Optional

from aiohttp import ClientSession

from bigur.auth.model.base import Object


@dataclass
class Provider(Object):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    revocation_endpoint: str
    jwks_uri: str
    response_types_supported: List[str]
    subject_types_supported: List[str]
    id_token_signing_alg_values_supported: List[str]
    scopes_supported: List[str]
    token_endpoint_auth_methods_supported: List[str]
    claims_supported: List[str]
    code_challenge_methods_supported: List[str]
    domains: List[str]
    client_id: str
    client_secret: str
    keys: Optional[Dict[str, Dict[str, str]]] = None

    async def update_keys(self):
        async with ClientSession() as session:
            async with session.get(self.jwks_uri) as response:
                keys = (await response.json())['keys']
                self.keys = {x['kid']: x for x in keys}

    async def get_key(self, kid: str) -> Dict[str, str]:
        if self.keys:
            return self.keys[kid]
        raise KeyError('Key with kid {} not found'.format(kid))

    def __str__(self):
        return '<{}({})>'.format(type(self).__name__, self.id)
