__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from time import time
from typing import Callable, Optional, Union

from aiohttp.web import Response, middleware
from aiohttp.web_exceptions import HTTPError
from bigur.store import Stored, UnitOfWork
from bigur.utils import config

from bigur.auth.authn import choose_authn
from bigur.auth.authn.base import AuthN

from bigur.auth.model import User


logger = getLogger(__name__)


class AuthEvent(Stored):
    def __init__(self, user: str, timestamp: int = None, valid: int = None):
        self.user = user
        if timestamp is None:
            timestamp = int(time())
        self.timestamp = timestamp
        self.valid = valid
        super().__init__()


def load_cookie_key():
    key_file = config.get('auth', 'cookie_key_file',
                          fallback='/etc/bigur/cookie.key')

    try:
        with open(key_file, 'rb') as fh:
            key = fh.read()

    except OSError as e:
        logger.warning('%s', e)
        need_write = config.getboolean('auth', 'cookie_write_key',
                                       fallback=False)
        key = b''
        if need_write:
            try:
                with open(key_file, 'wb') as fh:
                    fh.write(key)
            except OSError as e:
                logger.warning('%s', e)
    return key


@middleware
async def authenticate(request, handler: Callable) -> Response:
    logger.debug('Запрос %s', request.path)

    # Получаем ключ
    key: bytes = load_cookie_key()

    # Проверяем cookie
    cookie_name: str = config.get('auth', 'cookie_name', fallback='oidc')
    value: Optional[str] = request.cookies.get(cookie_name)

    # Cookie установлена, проверяем валидность
    if value:
        logger.debug('Cookie установлена в %s', value)

        # Расшифровываем

        # Загружаем AuthEvent

        # Проверяем срок действия

        # TODO: если cookie не валидна, надо её снять

    # Cookie не установлена (или не валидна)
    if value is None:
        logger.debug('Cookie не установлена, аутентификация')

        # Выбираем провайдера для аутентификации
        authn: AuthN = choose_authn(request)

        # Производим аутентификацию
        result: Union[Response, User] = await authn.verify(request)

        # Возвращают Response, выходим
        if isinstance(result, Response):
            return result

        # Аутентификация прошла, создаём событие входа
        async with UnitOfWork():
            request['auth_event'] = AuthEvent(result.id)

        # Устанавливаем cookie
        #value=

    response = await handler(request)

    return response
