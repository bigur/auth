'''Сессия пользователя открывается после аутентификации и содержит
основные данные для взаимодействия с клиентом.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from datetime import datetime
from logging import getLogger
from time import time

from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT

from bigur.store import Stored
from bigur.utils import config, localzone
from bigur.worker import Consumer, Object

from bigur.auth.role import Role
from bigur.auth.user import User


logger = getLogger('bigur.auth.session')


class Session(Stored):
    '''Сессия пользователя.'''

    __metadata__ = {
        'collection': 'sessions',
    }

    def __init__(self, user, remote_addr=None, user_agent=None):
        ''':param str user: идентификатор пользователя, который открыл сессию
        :param str remote_addr: IP-адрес, с которого открыта сессия
        :param str user_agent: User-Agent клиента'''
        #: Идентификатор пользователя
        self.user = user

        #: IP-адрес с которого открыта сессия
        self.remote_addr = remote_addr

        #: Поле User-Agent клиента
        self.user_agent = user_agent

        #: Дата открытия сессии (:class:`~datetime.datetime`)
        self.created = datetime.now(tz=localzone)

        #: Дата последней активности (:class:`~datetime.datetime`)
        self.last_activity = datetime.now(tz=localzone)

        #: Дата закрытия (:class:`~datetime.datetime`)
        self.closed = None

        super().__init__()


class CreateSession(Consumer):

    __roles_cache__ = None

    async def call(self, login, password, context):
        logger.debug('Запрос токена для пользователя `%s\'', login)
        remote_addr=''
        user_agent=''
        if not login or not password:
            raise ValueError('логин и пароль не могут быть пустыми')

        user = await User.find_one({'login': login})
        if user is None:
            logger.warning('Пользователь с логином `%s\' не найден', login)
            raise ValueError('доступ запрещён')

        elif not user.verify_password(password):
            logger.warning('Неверный пароль для пользователя `%s\'', login)
            raise ValueError('доступ запрещён')

        session = await Session(user._id,
                                remote_addr=remote_addr,
                                user_agent=user_agent).save()

        key = JWK(k=config.get('auth', 'jwt_k'),
                  kty=config.get('auth', 'jwt_kty'))

        header = {'alg': 'HS256'}

        if self.__roles_cache__ is None:
            self.__roles_cache__ = {}

        mask = 0
        roles = [x['roles'] for x in user.namespaces \
            if x['namespace'] == user.ns][0]
        for _id in roles:
            role = self.__roles_cache__.get(_id)
            if role is None:
                role = await Role.find_one({'_id': _id})
                if role is not None:
                    self.__roles_cache__[_id] = role
            if role is not None:
                mask += getattr(role, 'bit', 0)

        expire = config.getint('auth', 'jwt_access_expire', fallback=60*15)
        claims = {
            'ns': user.ns,
            'sid': session.id,
            'user': user.login,
            'mask': int(mask),
            'exp': int(time()) + expire
        }
        access_token = JWT(header=header, claims=claims)
        access_token.make_signed_token(key)

        expire = config.getint('web', 'jwt_refresh_expire', fallback=60*15)
        claims = {
            'ns': user.ns,
            'sid': session.id,
            'exp': int(time()) + expire
        }
        refresh_token = JWT(header=header, claims=claims)
        refresh_token.make_signed_token(key)
        return {'sid': session.id,
                'access_token': access_token.serialize(),
                'refresh_token': refresh_token.serialize()}
