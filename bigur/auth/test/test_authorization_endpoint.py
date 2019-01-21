__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import Application, view
from aiohttp.pytest_plugin import aiohttp_client  # noqa: F401
from pytest import fixture, mark

from bigur.store import UnitOfWork
from bigur.store.test.fixtures import configured, database  # noqa: F401

from bigur.auth.model import User, Client
from bigur.auth.handlers import AuthorizationHandler


@fixture
def loop(event_loop):
    return event_loop


@fixture
def debug(caplog):
    '''Отладка тестов.'''
    from logging import DEBUG
    caplog.set_level(DEBUG, logger='bigur.auth')


@fixture  # noqa: F811
def cli(loop, aiohttp_client):
    app = Application(loop=loop)
    app.add_routes([
        view('/authorize', AuthorizationHandler)
    ])
    return loop.run_until_complete(aiohttp_client(app))


class TestAuthorizationEndpoint(object):
    '''Тестирование точки входа "Авторизация"'''
    @configured  # noqa: F811
    @mark.asyncio
    async def test_client_id(self, cli, database, debug):
        '''Тест проверки id клиента'''
        async with UnitOfWork():
            user = User('admin', '123')
            Client('Тестовый клиент', user.id, 'password')

            response = await cli.post('/authorize')
            text = await response.text()

            assert text == 'test'
