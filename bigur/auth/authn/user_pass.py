__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Response

logger = getLogger(__name__)


class UserPass(object):
    '''Авторизация по логину и паролю'''

    async def verify(self, request):
        return Response(text='user-pass')
