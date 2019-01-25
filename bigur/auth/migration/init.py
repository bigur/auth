__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from hashlib import sha512
from logging import getLogger
from uuid import uuid4

from bigur.store.migrator import transition

from bigur.auth.version import __version__


logger = getLogger(__name__)


@transition('auth', None, __version__)
async def init(db):
    logger.debug('Initializing database')

    admin_id = str(uuid4())

    salt = uuid4().hex
    crypt = sha512(('admin' + salt).encode('utf-8')).hexdigest()

    await db.users.insert_one({
        '_id': admin_id,
        '_class': 'bigur.auth.model.user.User',
        'username': 'admin',
        'salt': salt,
        'crypt': crypt
    })

    await db.clients.insert_one({
        '_id': '34833d5e-7e17-4f76-a489-5f1d8530f55f',
        '_class': 'bigur.auth.model.client.Client',
        'title': 'Test client',
        'user_id': admin_id,
        'grant_type': 'implicit',
    })
