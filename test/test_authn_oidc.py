__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode
from json import loads

from pytest import fixture, mark
from urllib.parse import urlparse, parse_qs

from aiohttp.web import View, json_response

from bigur.auth.authn import OpenIDConnect
from bigur.auth.authn.base import decrypt
from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oauth2.endpoint import Endpoint


class OpenIDConfigHandler(View):

    async def get(self):
        host = self.request.host
        return json_response({
            'issuer': 'http://{}'.format(host),
            'authorization_endpoint': 'http://{}/provider/auth'.format(host),
            'jwks_uri': 'http://{}/provider/keys'.format(host),
            'response_types_supported': ['id_token', 'token', 'code'],
            'subject_types_supported': 'public',
            'id_token_signing_alg_values_supported': ['RS256'],
            'scopes_supported': ['openid']
        })


class TestEndpoint(Endpoint):
    pass


class TestHandler(OAuth2Handler):
    __endpoint__ = TestEndpoint


@fixture
def fix_client_config(config, cli):
    data = config.configuration_data['authn']['oidc']
    if 'clients' not in data:
        data['clients'] = {}
    data['clients']['localhost:{}'.format(cli.port)] = {
        'client_id': 'pytest',
        'client_secret': 'xxx',
    }


@fixture
def provider_routing(app):
    app.router.add_route('*', '/.well-known/openid-configuration',
                         OpenIDConfigHandler)


@fixture
def authn_oidc_routing(config, app):
    app.router.add_route('*', '/auth/test', TestHandler)

    app.router.add_route('*', '/auth/oidc', OpenIDConnect)
    config.configuration_data['http_server']['endpoints']['oidc'] = {
        'path': '/auth/oidc'
    }


@fixture
async def authn_oidc(provider_routing, authn_oidc_routing, fix_client_config):
    pass


class TestOIDCAuthn(object):
    '''Test authentication via third party oidc'''

    @mark.asyncio
    async def test_redirect_to_provider(self, app, authn_oidc, cli):
        response = await cli.get(
            '/auth/test',
            params={
                'client_id': 'blah',
                'acr_values': 'idp:localhost:{}'.format(cli.port),
            },
            allow_redirects=False)
        assert 303 == response.status

        assert 'text/plain' == response.content_type

        assert 'location' in response.headers
        parsed = urlparse(response.headers['Location'])

        query = parse_qs(parsed.query)

        assert 'http' == parsed.scheme
        assert 'localhost:{}'.format(cli.port) == parsed.netloc

        assert '/provider/auth' == parsed.path

        assert {
            'client_id',
            'response_type',
            'redirect_uri',
            'scope',
            'state',
            'nonce',
        } == set(query.keys())
        assert ['pytest'] == query['client_id']
        assert ['code'] == query['response_type']
        assert (['http://127.0.0.1:{}/auth/oidc'.format(
            cli.port)] == query['redirect_uri'])
        assert ['openid'] == query['scope']
        assert 64 == len(query['nonce'][0])

        state = loads(
            decrypt(app['cookie_key'], urlsafe_b64decode(query['state'][0])))
        assert isinstance(state, dict)
        assert {'n', 'p', 'u'} == set(state.keys())
        assert query['nonce'][0] == state['n']
        assert '/auth/test' == state['u']
        assert {
            'acr_values': 'idp:localhost:{}'.format(cli.port),
            'client_id': 'blah'
        } == state['p']
