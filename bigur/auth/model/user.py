'''Пользователь системы - учётная запись для аутентификации и авторизации.
Пользователь реализован через два класса:

  * :class:`~bigur.auth.user.User` - обыкновенный пользователь, это может
    быть учётная запись для другого сервиса.

  * :class:`~bigur.auth.user.Human` - пользователь - физическое лицо,
    к этому классу добавлены ФИО, а также информация для аутентификации
    через соцсети'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from hashlib import sha512
from logging import getLogger
from typing import Optional
from uuid import uuid4

from bigur.store import Stored


logger = getLogger('bigur.auth.model.user')


class User(Stored):
    '''Учётная запись пользователя в системе.'''

    __metadata__ = {
        'collection': 'users',
        'replace_attrs': {'_crypt': 'crypt',
                          '_salt': 'salt'},
    }

    def __init__(self, username: str, password: Optional[str] = None):
        ''':param str username: имя пользователя
        :param str password: пароль'''

        #: Логин пользователя.
        self.username = username

        if password is not None:
            self.set_password(password)

        super().__init__()

    @staticmethod
    def _get_hash(salt: str, password: str):
        string = (password + salt).encode('utf-8')
        return sha512(string).hexdigest()

    def set_password(self, password: str):
        '''Устанавливает новый пароль пользователя.

        :param str password: пароль пользователя'''
        self._salt = uuid4().hex
        self._crypt = self._get_hash(self._salt, password)

    def verify_password(self, password: str):
        '''Проверяет пароль пользователя. Возвращает ``True``, если пароль
        верный, иначе возвращает ``False``.

        :param str password: пароль пользователя'''
        salt = getattr(self, '_salt', None)
        crypt = getattr(self, '_crypt', None)
        if salt is not None and crypt is not None:
            return crypt == self._get_hash(salt, password)
        return False


class Human(User):
    '''Пользователь-физическое лицо.'''

    def __init__(self,
                 username: str,
                 password: Optional[str] = None,
                 first_name: Optional[str] = None,
                 patronymic: Optional[str] = None,
                 last_name: Optional[str] = None):
        ''':param str username: имя пользователя
        :param str password: пароль
        :param str first_name: реальное имя человека
        :param str patronymic: отчество
        :param str last_name: фамилия'''
        if first_name:
            #: Настояще имя человека
            self.first_name = first_name

        if patronymic:
            #: Отчество человека
            self.patronymic = patronymic

        if last_name:
            #: Фамилия человека
            self.last_name = last_name

        super().__init__(username=username,
                         password=password)

    def full_name(self, order=None):
        '''Возвращает ИОФ человека в формате `Имя Отчество Фамилия`.
        :param tuple order: порядок следования атрибутов при составлении
            полного имени.'''
        if order is None:
            order = ('last_name', 'first_name', 'patronymic')
        return ' '.join([getattr(self, x) for x in order if hasattr(self, x)])
