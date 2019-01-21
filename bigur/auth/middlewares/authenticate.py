__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import middleware
from bigur.utils import config

from bigur.auth.authn import choose_authn


logger = getLogger(__name__)


@middleware
async def authenticate(request, handler):
    logger.debug('Запрос %s', request.path)

    # Проверяем cookie
    cookie_name = config.get('auth', 'cookie_name', fallback='oidc')
    value = request.cookies.get(cookie_name)
    if value:
        logger.debug('Cookie установлена в %s', value)

        # Получаем ключ

        # Расшифровываем

        # Проверяем срок действия

    if value is None:
        logger.debug('Cookie не установлена, аутентификация')

        # Выбираем провайдера для аутентификации
        authn = choose_authn(request)

        response = await authn.verify(request)

    else:
        response = await handler(request)

    return response
