__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from time import time

from jwcrypto.jwk import JWK
from jwcrypto.jwt import JWT

from bigur.utils import config

from bigur.auth.role import Role
from bigur.auth.session import Session
from bigur.auth.user import User

from .core import Service


logger = getLogger('bigur.auth.amql.auth_service')


class GetToken(Service):

    __roles_cache__ = None

    async def call(self, login, password, remote_addr, user_agent,
                   context=None):
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
                'access_token': access_token.serialize(),
                'refresh_token': refresh_token.serialize()}
