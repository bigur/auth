__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient
from bigur.auth import __version__
from bigur.store.migrator import transition
from bigur.utils import config


logger = getLogger('bigur.auth.migration.init')


@transition('auth', None, __version__)
async def init(db):
    logger.debug('Заполняю базу первоначальным контентом')

    old_db_uri = config.get('migration', 'old_database_url', fallback=None)
    if old_db_uri is not None:
        logger.debug('Переношу данные из старой базы')

        db_name = urlparse(old_db_uri).path.strip('/')
        old_db = AsyncIOMotorClient(old_db_uri)[db_name]

        async for role in old_db.roles.find():
            role['_class'] = 'bigur.auth.role.Role'
            del role['state']
            await db.roles.insert_one(role)

        async for configuration in old_db.configurations.find():
            configuration['_class'] = 'bigur.auth.configuration.Configuration'
            configuration['roles'] = [x.id for x in configuration['roles']]
            del configuration['state']
            await db.configurations.insert_one(configuration)

        async for namespace in old_db.namespaces.find():
            namespace['_class'] = 'bigur.auth.namespace.Namespace'
            namespace['configurations'] = \
                [x.id for x in namespace['configurations']]
            del namespace['configuration']
            del namespace['state']
            await db.namespaces.insert_one(namespace)

        async for user in old_db.users.find():
            if user['_class'] == 'office.user.Human':
                user['_class'] = 'bigur.auth.user.Human'
            else:
                user['_class'] = 'bigur.auth.user.User'

            namespaces = []
            for record in user['namespaces']:
                namespaces.append({
                    'namespace': record['namespace'].id,
                    'roles': [x.id for x in record['roles']],
                })
            user['namespaces'] = namespaces

            del user['roles']
            del user['permissions']
            del user['state']
            await db.users.insert_one(user)


