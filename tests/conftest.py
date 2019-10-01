__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger, DEBUG, INFO

from pytest import fixture

from aiohttp.pytest_plugin import aiohttp_client  # noqa: F401

logger = getLogger(__name__)
logger.setLevel(INFO)


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
    config = Kaptan()
    config.import_config({
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
    return config


# Store
@fixture(scope='function')
def store():
    logger.debug('Creating store')
    from bigur.auth.store import Memory
    return Memory()


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
    from aiohttp.web import Application
    from aiohttp_jinja2 import setup as jinja_setup
    from jinja2 import FileSystemLoader
    from rx.scheduler.eventloop import AsyncIOScheduler
    from bigur.auth.middlewares import session
    app = Application(middlewares=[session])
    app['config'] = config
    app['store'] = store
    app['jwt_keys'] = [jwt_key]
    app['cookie_key'] = cookie_key
    app['scheduler'] = AsyncIOScheduler(loop)
    app['provider'] = {}
    templates = normpath(dirname(__file__) + '/../templates')
    jinja_setup(app, loader=FileSystemLoader(templates))
    return app


@fixture(scope='function')
def authn_userpass(app):
    logger.debug('Add userpass authn route')
    from bigur.auth.authn import UserPass
    return app.router.add_route('*', '/auth/login', UserPass)


# Entities
@fixture(scope='function')
async def user(store):
    logger.debug('Creating new user')
    from bigur.auth.model import User
    yield await store.users.put(User('admin', '123'))


@fixture(scope='function')
async def client(store, user):
    logger.debug('Creating client')
    from bigur.auth.model import Client
    yield await store.clients.put(
        Client('Test web client', user.id, 'password'))


@fixture
def token(config, user, client, scope='function'):
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
