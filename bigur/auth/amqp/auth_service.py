__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from time import time

from aio_pika import connect_robust
from aio_pika.patterns import RPC
from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT

from bigur.utils import config

from bigur.auth.role import Role
from bigur.auth.session import Session
from bigur.auth.user import User


logger = getLogger('bigur.auth.amql.auth_service')


class PermissionDenied(Exception):
    pass


class Connection(object):
    def __new__(cls, *args, **kwargs):
        if not getattr(cls, '__instance', None):
            cls.__instance = object.__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self._connection = None

    async def get_connection(self):
        if self._connection is None:
            self._connection = await connect_robust(config.get('auth', 'url'))
        return self._connection


class AuthService(object):

    _roles_cache = None

    async def consume(self):
        connection = await Connection().get_connection()

        channel = await connection.channel()

        rpc = await RPC.create(channel)
        await rpc.register(config.get('auth', 'auth_queue'),
                           self.get_token,
                           auto_delete=True)

    async def get_token(self, login, password, remote_addr, user_agent):
        logger.debug('Запрос токена для пользователя `%s\'', login)
        if not login or not password:
            raise ValueError('логин и пароль не могут быть пустыми')

        user = await User.find_one({'login': login})
        if user is None:
            logger.warning('Пользователь с логином `%s\' не найден', login)
            return
        elif not user.verify_password(password):
            logger.warning('Неверный пароль для пользователя `%s\'', login)
            return

        session = await Session(user._id,
                                remote_addr=remote_addr,
                                user_agent=user_agent).save()

        key = JWK(k=config.get('auth', 'jwt_k'),
                  kty=config.get('auth', 'jwt_kty'))

        header = {'alg': 'HS256'}

        if self._roles_cache is None:
            self._roles_cache = {}

        mask = 0
        for _id in user.roles:
            role = self._roles_cache.get(_id)
            if role is None:
                role = await Role.find_one({'_id': _id})
                if role is not None:
                    self._roles_cache[_id] = role
            if role is not None:
                mask += role.get('bit', 0)

        expire = config.getint('auth', 'jwt_access_expire', fallback=60*15)
        claims = {
            'sid': session.id,
            'user': user.login,
            'mask': int(mask),
            'exp': int(time()) + expire
        }
        access_token = JWT(header=header, claims=claims)
        access_token.make_signed_token(key)

        expire = config.getint('web', 'jwt_refresh_expire', fallback=60*15)
        claims = {
            'sid': session.id,
            'exp': int(time()) + expire
        }
        refresh_token = JWT(header=header, claims=claims)
        refresh_token.make_signed_token(key)

        return {'sid': session.id,
                'access': access_token.serialize(),
                'refresh': refresh_token.serialize()}
