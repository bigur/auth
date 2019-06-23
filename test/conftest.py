__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger, DEBUG

from pytest import fixture

from aiohttp.pytest_plugin import aiohttp_client  # noqa: F401

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
            }
        },
        'http_server': {
            'endpoints': {
                'login': {
                    'path': '/auth/login'
                }
            }
        }
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
def app(config, store, jwt_key, cookie_key):
    logger.debug('Creating application')
    from os.path import dirname, normpath
    from aiohttp.web import Application
    from aiohttp_jinja2 import setup as jinja_setup
    from jinja2 import FileSystemLoader
    from bigur.auth.middlewares import session
    app = Application(middlewares=[session])
    app['config'] = config
    app['store'] = store
    app['jwt_keys'] = [jwt_key]
    app['cookie_key'] = cookie_key
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


# Client
@fixture(scope='function')
async def cookie_jar():
    logger.debug('Creating CookieJar')
    from aiohttp import CookieJar

    yield CookieJar(unsafe=True)


@fixture(scope='function')  # noqa: F811
def cli(loop, app, cookie_jar, aiohttp_client):
    return loop.run_until_complete(aiohttp_client(app, cookie_jar=cookie_jar))


@fixture(scope='module')
def decode_token(jwt_key):
    from cryptography.hazmat.primitives.serialization import (Encoding,
                                                              PublicFormat)
    from jwt import decode as jwt_decode
    public_bytes = jwt_key.public_key().public_bytes(
        encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)

    def decode(token):
        return jwt_decode(token, public_bytes, algorithms=['RS256'])

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
