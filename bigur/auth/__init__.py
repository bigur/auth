__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

__version__ = '1.0.1'

from bigur.rx import Observer
from bigur.store import Migrator
from bigur.worker import on_migration, on_startup

from bigur.auth import migration
from bigur.auth.session import CreateSession


async def create_consumers(_):
    await CreateSession().consume()


async def initialization(): # pylint: disable=missing-docstring
    await on_migration.subscribe(Migrator('auth', __version__))
    await on_startup.subscribe(Observer(create_consumers))
