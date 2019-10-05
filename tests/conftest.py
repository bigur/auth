__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger, DEBUG, INFO

from pytest import fixture

# pylint: disable=unused-import
from aiohttp.pytest_plugin import aiohttp_client  # noqa

# pylint: disable=redefined-outer-name,unused-argument

logger = getLogger(__name__)
logger.setLevel(DEBUG)


# Main loop
@fixture
def loop(event_loop):
    return event_loop


# Debug
@fixture
def debug(caplog):
    '''Enable debug logging in tests.'''
    caplog.set_level(DEBUG, logger='bigur.auth')
    return logger.debug


# Cryptography
@fixture(scope='module')
def jwt_key():
    logger.debug('Generating new JWT key')
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    return rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend())


# App configuration
@fixture(scope='module')
def config():
    logger.debug('Loading configuration')
    from kaptan import Kaptan
    cfg = Kaptan()
    cfg.import_config({
        'authn': {
            'cookie': {
                'secure': False,
                'session_name': 'sid',
                'id_name': 'uid',
                'max_age': 3600
            },
            'oidc': {
                'provider_protocol': 'http',
            }
        },
        'http_server': {
            'endpoints': {
                'login': {
                    'path': '/auth/login'
                },
                'registration': {
                    'path': '/auth/registration'
                }
            }
        },
        'oidc': {
            'iss': 'https://localhost:8889',
        },
    })
    return cfg


# Store
@fixture(scope='function')
def store():
    logger.debug('Creating store')
    from bigur.auth.store import Memory
    from bigur.auth.store import store
    store.set_store(Memory())
    return store


# Cookie key
@fixture(scope='module')
def cookie_key():
    logger.debug('Generating cookie key')
    from os import urandom
    return urandom(32)


# Server
@fixture(scope='function')
def app(loop, config, store, jwt_key, cookie_key):
    logger.debug('Creating application')
    from os.path import dirname, normpath
    from warnings import warn
    from aiohttp.web import Application
    from aiohttp_jinja2 import setup as jinja_setup
    from jinja2 import FileSystemLoader
    from rx.scheduler.eventloop import AsyncIOScheduler
    from bigur.auth.middlewares import session
    app = Application(middlewares=[session])
    app['config'] = config
    app['jwt_keys'] = [jwt_key]
    app['cookie_key'] = cookie_key
    app['scheduler'] = AsyncIOScheduler(loop)
    app['provider'] = {}
    templates = normpath(dirname(__file__) + '/../templates')
    jinja_setup(app, loader=FileSystemLoader(templates))

    class WarnWrapper:

        def __getattr__(self, name):
            warn(
                'Use of app[\'store\'] is depricated',
                DeprecationWarning,
                stacklevel=2)
            return getattr(store, name)

        def __setattr__(self, name, value):
            warn(
                'Use of app[\'store\'] is depricated',
                DeprecationWarning,
                stacklevel=2)
            return setattr(store, name, value)

    app['store'] = WarnWrapper()

    return app


@fixture(scope='function')
def authn_userpass(app):
    logger.debug('Add userpass authn route')
    from bigur.auth.authn.user import UserPass
    return app.router.add_route('*', '/auth/login', UserPass)


# Entities
@fixture(scope='function')
async def user(store):
    logger.debug('Creating new user')
    from bigur.auth.model import User
    yield await store.users.put(User(username='admin', password='123'))


@fixture(scope='function')
async def client(store, user):
    logger.debug('Creating client')
    from bigur.auth.model import Client
    yield await store.clients.put(
        Client(
            client_type='confidential',
            user_id=user.id,
            title='Test web client',
            password='123',
            redirect_uris=['http://localhost/feedback']))


@fixture(scope='function')
def token(config, user, client):
    logger.debug('Creating id_token')
    from time import time
    from bigur.auth.oidc.grant.implicit import IDToken
    return IDToken(
        iss=config.get('oidc.iss'),
        sub=str(user.id),
        aud=str(client.id),
        nonce='test nonce',
        iat=int(time()),
        exp=int(time()) + 600)


# Client
@fixture(scope='function')
async def cookie_jar():
    logger.debug('Creating CookieJar')
    from aiohttp import CookieJar

    yield CookieJar(unsafe=True)


@fixture(scope='function')  # noqa: F811
def cli(loop, app, cookie_jar, aiohttp_client):  # noqa
    return loop.run_until_complete(aiohttp_client(app, cookie_jar=cookie_jar))


@fixture(scope='module')
def decode_token(jwt_key):
    from cryptography.hazmat.primitives.serialization import (Encoding,
                                                              PublicFormat)
    from jwt import decode as jwt_decode
    public_bytes = jwt_key.public_key().public_bytes(
        encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)

    def decode(token, **kwargs):
        return jwt_decode(token, public_bytes, algorithms=['RS256'], **kwargs)

    return decode


# Queries
@fixture(scope='function')
async def login(cli, user):
    logger.debug('Logining to server with username & password')
    response = await cli.post(
        '/auth/login',
        data={
            'username': 'admin',
            'password': '123',
        },
        allow_redirects=False)
    yield response


# Stub endpoint
@fixture(scope='function')
async def stub_endpoint(app):
    from dataclasses import dataclass
    from typing import Optional
    from rx import return_value
    from rx import operators as op
    from bigur.auth.handler.base import OAuth2Handler
    from bigur.auth.oauth2.request import OAuth2Request
    from bigur.auth.oauth2.response import OAuth2Response

    @dataclass
    class StubRequest(OAuth2Request):
        redirect_uri: Optional[str] = None

    @dataclass
    class StubResponse(OAuth2Response):
        test: Optional[str] = None

    def create_stub_stream(context):
        return return_value(context).pipe(
            op.map(lambda x: StubResponse(test='passed')))

    class StubHandler(OAuth2Handler):

        def get_request_class(self, params):
            return StubRequest

        def create_stream(self, context):
            return create_stub_stream(context)

        async def post(self):
            return await self.handle(await self.request.post())

    app.router.add_route('*', '/auth/stub', StubHandler)
