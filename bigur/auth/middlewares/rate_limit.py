__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import middleware


logger = getLogger(__name__)


@middleware
async def rate_limit(request, handler):
    logger.debug('Проверяю количество запросов в секунду')
    return await handler(request)
