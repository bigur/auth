__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from os import urandom
from os.path import dirname, normpath

from aiohttp import CookieJar
from aiohttp.web import Application, view
from aiohttp_jinja2 import setup as jinja_setup
from jinja2 import FileSystemLoader
from kaptan import Kaptan
from pytest import fixture

from bigur.auth.authn import OpenIDConnect, UserPass
from bigur.auth.handlers import AuthorizeView
from bigur.auth.middlewares import session
from bigur.auth.model import User, Client
from bigur.auth.store import Memory


@fixture
def loop(event_loop):
    return event_loop


from aiohttp.pytest_plugin import aiohttp_client  # noqa: F401


@fixture
def debug(caplog):
    '''Enable debug logging in tests.'''
    from logging import DEBUG
    caplog.set_level(DEBUG, logger='bigur.auth')


@fixture
def app():
    app = Application(middlewares=[session])

    app.add_routes([
        view('/auth/login', UserPass),
        view('/auth/oidc', OpenIDConnect),
        view('/auth/authorize', AuthorizeView),
    ])
    app['config'] = Kaptan()
    app['config'].import_config({
        'http_server': {
            'endpoints': {
                'login': {
                    'path': '/auth/login'
                }
            }
        },
        'authn': {
            'cookie': {
                'secure': False,
                'session_name': 'sid',
                'id_name': 'uid',
                'lifetime': 3600
            }
        }
    })

    app['cookie_key'] = urandom(32)

    app['store'] = Memory()

    templates = normpath(dirname(__file__) + '../../../../templates')
    jinja_setup(app, loader=FileSystemLoader(templates))

    return app


@fixture
async def cookie_jar():
    yield CookieJar(unsafe=True)


@fixture  # noqa: F811
def cli(loop, app, cookie_jar, aiohttp_client):
    return loop.run_until_complete(aiohttp_client(app, cookie_jar=cookie_jar))


# Entities
@fixture
async def user(app):
    user = await app['store'].users.put(User('admin', '123'))
    yield user


@fixture
async def aclient(app, user):
    client = await app['store'].clients.put(
        Client('Test web client', user.id, 'password'))
    yield client


@fixture
async def login(database, user, cli):
    response = await cli.post(
        '/auth/login',
        data={
            'username': 'admin',
            'password': '123',
        },
        allow_redirects=False)
    yield response
