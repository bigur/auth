'''Сессия пользователя открывается после аутентификации и содержит
основные данные для взаимодействия с клиентом.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from datetime import datetime

from bigur.store import Stored
from bigur.utils import localzone


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
