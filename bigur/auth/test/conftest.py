__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from os.path import dirname, normpath

from aiohttp_jinja2 import setup as jinja_setup
from aiohttp.web import Application, view
from jinja2 import FileSystemLoader
from pytest import fixture

from bigur.auth.handlers import AuthorizationHandler
from bigur.auth.middlewares import authenticate


@fixture
def loop(event_loop):
    return event_loop


from aiohttp.pytest_plugin import aiohttp_client  # noqa: F401


@fixture
def debug(caplog):
    '''Отладка тестов.'''
    from logging import DEBUG
    caplog.set_level(DEBUG, logger='bigur.auth')


@fixture
def cli(loop, aiohttp_client):
    app = Application(middlewares=[authenticate])
    app.add_routes([
        view('/authorize', AuthorizationHandler)
    ])

    templates = normpath(dirname(__file__) + '../../../../templates')
    jinja_setup(app, loader=FileSystemLoader(templates))

    return loop.run_until_complete(aiohttp_client(app))
