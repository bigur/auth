__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from .auth_service import GetToken
from .user_service import GetUser, ChangeNamespace

async def register_services():
    await GetToken().consume()
    await GetUser().consume()
    await ChangeNamespace().consume()
