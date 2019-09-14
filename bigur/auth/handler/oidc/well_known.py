__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import View, json_response
from aiohttp_cors import CorsViewMixin, ResourceOptions, custom_cors


class WellKnownHandler(View, CorsViewMixin):

    @custom_cors({'*': ResourceOptions(allow_headers='*')})
    async def get(self):
        req = self.request
        config = req.app['config']

        root = req.scheme + '://' + req.host

        result = {}
        result['issuer'] = config.get('oidc.iss')

        result['authorization_endpoint'] = root + config.get(
            'http_server.endpoints.authorize.path')
        result['token_endpoint'] = root + config.get(
            'http_server.endpoints.token.path')

        userinfo_endpoint = config.get('http_server.endpoints.'
                                       'userinfo.path', None)
        if userinfo_endpoint:
            result['userinfo_endpoint'] = root + userinfo_endpoint

        result['jwks_uri'] = root + config.get(
            'http_server.endpoints.jwks.path')

        result['response_types_supported'] = [
            'code',
            'id_token',
            'token',
            'token id_token',
        ]

        result['response_modes_supported'] = ['query', 'fragment']
        result['subject_types_supported'] = ['public']
        result['id_token_signing_alg_values_supported'] = ['RS256']

        return json_response(result)
