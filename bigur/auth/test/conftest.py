__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from os import environ, urandom
from os.path import dirname, normpath

from aiohttp import CookieJar
from aiohttp.web import Application, get, post, view
from aiohttp_jinja2 import setup as jinja_setup
from jinja2 import FileSystemLoader
from pytest import fixture, mark

from bigur.store import UnitOfWork, db
from bigur.utils import config

from bigur.auth.authn import UserPass
from bigur.auth.handlers import authorization_handler
from bigur.auth.middlewares import session
from bigur.auth.model import User, Client


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
        get('/auth/authorize', authorization_handler),
        post('/auth/authorize', authorization_handler),
    ])
    app['cookie_key'] = urandom(32)
    conf = config.get_object()
    if not conf.has_section('user_pass'):
        conf.add_section('user_pass')
    conf.set('user_pass', 'cookie_secure', 'false')
    templates = normpath(dirname(__file__) + '../../../../templates')
    jinja_setup(app, loader=FileSystemLoader(templates))
    return app


@fixture
async def cookie_jar():
    yield CookieJar(unsafe=True)


@fixture  # noqa: F811
def cli(loop, app, cookie_jar, aiohttp_client):
    return loop.run_until_complete(aiohttp_client(app, cookie_jar=cookie_jar))


@fixture
async def database():
    conf = config.get_object()
    if not conf.has_section('general'):
        conf.add_section('general')
    conf.set('general', 'database_url', environ.get('BIGUR_TEST_DB'))
    db._db = None
    for collection in await db.list_collection_names():
        await db.drop_collection(collection)
    yield db


mark.db_configured = mark.skipif(
    environ.get('BIGUR_TEST_DB') is None,
    reason='Setup BIGUR_TEST_DB env with mongodb URL.')


# Entities
@fixture
async def user(database):
    async with UnitOfWork():
        user = User('admin', '123')
    yield user


@fixture
async def aclient(database, user):
    async with UnitOfWork():
        client = Client('Test web client', user.id, 'password')
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
