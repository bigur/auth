__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from os import environ, urandom
from os.path import dirname, normpath

from aiohttp_jinja2 import setup as jinja_setup
from aiohttp.web import Application, get, post
from jinja2 import FileSystemLoader
from pytest import fixture, mark

from bigur.store import UnitOfWork, db
from bigur.utils import config

from bigur.auth.handlers import authorization_handler, user_pass_handler
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
    return Application()


@fixture  # noqa: F811
def cli(loop, app, aiohttp_client):
    '''Setup aiohttp client'''
    app.add_routes([
        get('/auth/login', user_pass_handler),
        post('/auth/login', user_pass_handler),
        get('/auth/authorize', authorization_handler),
        post('/auth/authorize', authorization_handler),
    ])

    app['cookie_key'] = urandom(32)

    templates = normpath(dirname(__file__) + '../../../../templates')
    jinja_setup(app, loader=FileSystemLoader(templates))

    return loop.run_until_complete(aiohttp_client(app))


@fixture
async def database():
    '''Database setup.'''
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
