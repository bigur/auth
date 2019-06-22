__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from os import urandom
from os.path import dirname, normpath

from aiohttp import CookieJar
from aiohttp.web import Application
from aiohttp_jinja2 import setup as jinja_setup
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (Encoding,
                                                          PublicFormat)
from jinja2 import FileSystemLoader
from jwt import decode as jwt_decode
from kaptan import Kaptan
from pytest import fixture

from bigur.auth.authn import UserPass
from bigur.auth.middlewares import session
from bigur.auth.model import User, Client
from bigur.auth.store import Memory


# Main loop
@fixture
def loop(event_loop):
    return event_loop


from aiohttp.pytest_plugin import aiohttp_client  # noqa: F401


# Debug
@fixture
def debug(caplog):
    '''Enable debug logging in tests.'''
    from logging import DEBUG
    caplog.set_level(DEBUG, logger='bigur.auth')


# Cryptography
@fixture
def jwt_key():
    return rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend())


# Server
@fixture
def app(jwt_key):
    app = Application(middlewares=[session])
    app['config'] = Kaptan()
    app['store'] = Memory()
    app['jwt_keys'] = [jwt_key]
    app['cookie_key'] = urandom(32)
    templates = normpath(dirname(__file__) + '/../templates')
    jinja_setup(app, loader=FileSystemLoader(templates))
    return app


@fixture
def authn_userpass(app):
    app['config'].import_config({
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
    return app.router.add_route('*', '/auth/login', UserPass)


# Entities
@fixture
async def user(app):
    if 'user' not in app:
        app['user'] = await app['store'].users.put(User('admin', '123'))
    yield app['user']


@fixture
async def client(app, user):
    if 'client' not in app:
        app['client'] = await app['store'].clients.put(
            Client('Test web client', user.id, 'password'))
    yield app['client']


# Client
@fixture
async def cookie_jar():
    yield CookieJar(unsafe=True)


@fixture  # noqa: F811
def cli(loop, app, cookie_jar, aiohttp_client):
    return loop.run_until_complete(aiohttp_client(app, cookie_jar=cookie_jar))


@fixture
def decode_token(app):
    jwt_key = app['jwt_keys'][0]
    public_bytes = jwt_key.public_key().public_bytes(
        encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)

    def decode(token):
        return jwt_decode(token, public_bytes, algorithms=['RS256'])

    return decode


# Queries
@fixture
async def login(cli, user):
    response = await cli.post(
        '/auth/login',
        data={
            'username': 'admin',
            'password': '123',
        },
        allow_redirects=False)
    yield response
