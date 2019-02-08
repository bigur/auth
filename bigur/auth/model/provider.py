__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from bigur.store import Stored


class Provider(Stored):

    __metadata__ = {
        'collection': 'providers'
    }

    keys = {
        'issuer',
        'authorization_endpoint',
        'token_endpoint',
        'userinfo_endpoint',
        'revocation_endpoint',
        'jwks_uri',
        'response_types_supported',
        'subject_types_supported',
        'id_token_signing_alg_values_supported',
        'scopes_supported',
        'token_endpoint_auth_methods_supported',
        'claims_supported',
        'code_challenge_methods_supported',
        'client_id'
    }

    def __init__(self, domain: str, **kwargs):
        self.domains = [domain]
        for key in self.keys & set(kwargs.keys()):
            setattr(self, key, kwargs[key])
        super().__init__()

    def __str__(self):
        return '<{}({})>'.format(type(self).__name__, self._id)
