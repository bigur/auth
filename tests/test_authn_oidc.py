__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode, urlsafe_b64encode
from json import dumps, loads
from hashlib import sha1
from re import match, DOTALL, MULTILINE

from pytest import fixture, mark
from urllib.parse import urlparse, parse_qs

from aiohttp.web import View, json_response

from bigur.auth.authn import OpenIDConnect
from bigur.auth.authn.base import crypt, decrypt
from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oauth2.endpoint import Endpoint


class ProviderOpenIDConfigHandler(View):

    async def get(self):
        host = self.request.host
        return json_response({
            'issuer': 'http://{}'.format(host),
            'authorization_endpoint': 'http://{}/provider/auth'.format(host),
            'token_endpoint': 'http://{}/provider/token'.format(host),
            'jwks_uri': 'http://{}/provider/keys'.format(host),
            'response_types_supported': ['id_token', 'token', 'code'],
            'subject_types_supported': 'public',
            'id_token_signing_alg_values_supported': ['RS256'],
            'scopes_supported': ['openid']
        })


class ProviderKeysHandler(View):

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


class ProviderAuthorizeHandler(View):
    pass


class ProviderTokenHandler(View):

    async def post(self):
        app = self.request.app
        params = await self.request.post()
        assert params.get('code') == '123'
        token = app['provider']['token']
        return json_response({
            'token_type': 'bearer',
            'id_token': token.encode(app['jwt_keys'][0]).decode('utf-8')
        })


class AuthorizeTestEndpoint(Endpoint):
    pass


class AuthorizeTestHandler(OAuth2Handler):
    __endpoint__ = AuthorizeTestEndpoint


@fixture
def fix_client_config(config, client, cli):
    data = config.configuration_data['authn']['oidc']
    if 'clients' not in data:
        data['clients'] = {}
    data['clients']['localhost:{}'.format(cli.port)] = {
        'client_id': client.id,
        'client_secret': 'xxx',
    }


@fixture
def provider_routing(app):
    app.router.add_route('*', '/.well-known/openid-configuration',
                         ProviderOpenIDConfigHandler)
    app.router.add_route('*', '/provider/keys', ProviderKeysHandler)
    app.router.add_route('*', '/provider/authorize', ProviderAuthorizeHandler)
    app.router.add_route('*', '/provider/token', ProviderTokenHandler)


@fixture
def authn_oidc_routing(config, app):
    app.router.add_route('*', '/auth/authorize', AuthorizeTestHandler)

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
    async def test_redirect_to_provider(self, app, client, authn_oidc, cli):
        response = await cli.get(
            '/auth/authorize',
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
        assert [client.id] == query['client_id']
        assert ['code'] == query['response_type']
        assert (['http://127.0.0.1:{}/auth/oidc'.format(cli.port)
                ] == query['redirect_uri'])  # noqa
        assert ['openid'] == query['scope']
        assert 64 == len(query['nonce'][0])

        state = loads(
            decrypt(app['cookie_key'], urlsafe_b64decode(query['state'][0])))
        assert isinstance(state, dict)
        assert {'n', 'p', 'u'} == set(state.keys())
        assert query['nonce'][0] == state['n']
        assert '/auth/authorize' == state['u']
        assert {
            'acr_values': 'idp:localhost:{}'.format(cli.port),
            'client_id': 'blah'
        } == state['p']

    @mark.asyncio
    async def test_redirect_from_provider(self, app, client, user, token,
                                          authn_oidc, cli):
        app['provider']['token'] = token
        state = {
            'n': 'test nonce',
            'u': '/auth/authorize',
            'p': {
                'acr_values': 'idp:localhost:{}'.format(cli.port)
            },
        }
        response = await cli.get(
            '/auth/oidc',
            params={
                'client_id':
                    'blah',
                'acr_values':
                    'idp:localhost:{}'.format(cli.port),
                'code':
                    '123',
                'state':
                    urlsafe_b64encode(crypt(app['cookie_key'],
                                            dumps(state))).decode('utf-8'),
            },
            allow_redirects=False)

        # User not registered, so endpoint will return registration form
        assert 200 == response.status

        assert 'text/html; charset=utf-8' == response.headers['Content-Type']
        assert match(r'.*<form.*>.*</form>.*', await response.text(),
                     DOTALL | MULTILINE) is not None
