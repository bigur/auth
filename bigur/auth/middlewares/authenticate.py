__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode, urlsafe_b64encode
from logging import getLogger
from os import urandom
from time import time
from typing import Callable, Optional, Union

from aiohttp.web import Response, middleware
from bigur.store import Stored, UnitOfWork
from bigur.utils import config
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.backends import default_backend

from bigur.auth.authn import choose_authn
from bigur.auth.authn.base import AuthN

from bigur.auth.model import User


BLOCK_SIZE = 16

logger = getLogger(__name__)


class AuthEvent(Stored):
    def __init__(self, user: str, timestamp: int = None, valid: int = None):
        self.user = user
        if timestamp is None:
            timestamp = int(time())
        self.timestamp = timestamp
        self.valid = valid
        super().__init__()


@middleware
async def authenticate(request, handler: Callable) -> Response:
    logger.debug('Запрос %s', request.path)

    # Проверяем cookie
    cookie_name: str = config.get('auth', 'cookie_name', fallback='oidc')
    value: Optional[str] = request.cookies.get(cookie_name)

    # Инициализируем криптографию
    backend = default_backend()

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
        response = Response(text='ok')

        iv: bytes = urandom(BLOCK_SIZE)
        cipher = Cipher(AES(request.app['cookie_key']),
                        CBC(iv),
                        backend=backend)
        encryptor = cipher.encryptor()

        msg = result.id
        encrypted = encryptor.update(msg.encode('utf-8'))
        value = urlsafe_b64encode(encrypted + b':' + iv).decode('utf-8')

        cookie_lifetime: int = config.getint('auth', 'cookie_lifetime',
                                             fallback=3600)

        if config.getboolean('auth', 'cookie_secure', fallback=True):
            cookie_secure: Optional[str] = 'yes'
        else:
            cookie_secure = None

        response.set_cookie(cookie_name,
                            value,
                            max_age=cookie_lifetime,
                            secure=cookie_secure,
                            httponly='yes')
        return response

    response = await handler(request)

    return response
