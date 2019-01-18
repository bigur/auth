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
from typing import List
from uuid import uuid4

from bigur.store import Embedded, Stored
from bigur.store.typing import Id


logger = getLogger('bigur.auth.user')


class NamespaceInfo(Embedded):

    def __init__(self, ns: Id, roles: List[Id]):
        self.ns = ns
        self.roles = roles


class User(Stored):
    '''Учётная запись пользователя в системе.'''

    __metadata__ = {
        'collection': 'users',
        'replace_attrs': {'_crypt': 'crypt',
                          '_salt':  'salt'},
    }

    def __init__(self, ns, login, password=None, namespaces=None,
                 settings=None):
        ''':param str ns: идентификатор текущего пространства имён
        :param str login: имя пользователя
        :param str password: пароль
        :param list namespaces: информация о разрешённых для данного
            пользователя пространтствах имён, необходимо для учётных
            записей, поддерживающих нескольких клиентов. Каждый элемент
            списка - это :class:`dict` следующего формата:
            ``{'namespace': ns, 'roles': [role1, role2, ...]}``, где ``ns`` и
            ``roleX`` - идентификаторы соответствующих объектов.
        :param dict settings: настройки пользователя, ключи данных должны быть
            строкамии, а значения должны иметь элементарный тип, легко
            кодируемый в JSON.'''

        #: Идентификатор текущего пространства имён пользователя.
        self.ns = ns

        if namespaces is None:
            namespaces = [{
                'namespace': ns,
            }]
        assert isinstance(namespaces, list), 'namespaces должен быть списком'
        #: Список пространств имён, которые доступны пользователю.
        #: Это список :class:`list` словарей :class:`dict` с записями
        #: следующего вида::
        #:
        #:  {'namespace': ns, 'roles': [role1, role2...]}
        #:
        #: Где `ns` и ``roleX`` - идентификаторы (:class:`str`). Если роли
        #: не установлены, то ``roles``` отсутствует.
        self.namespaces = namespaces

        #: Логин пользователя.
        self.login = login

        if password is not None:
            self.set_password(password)

        if settings is not None:
            #: Настройки пользователя. Это :class:`dict`, ключи которого
            #: являются строками, а значения элементарного типа, легко
            #: трансформирующегося в JSON.
            self.settings = settings

        super().__init__()

    @staticmethod
    def _get_hash(salt, password):
        string = (password + salt).encode('utf-8')
        return sha512(string).hexdigest()

    def set_password(self, password):
        '''Устанавливает новый пароль пользователя.

        :param str password: пароль пользователя'''
        self._salt = uuid4().hex
        self._crypt = self._get_hash(self._salt, password)

    def verify_password(self, password):
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

    def __init__(self, ns, login, password=None, namespaces=None,
                 roles=None, settings=None,
                 name=None, patronymic=None, surname=None,
                 social=None):
        ''':param str ns: идентификатор текущего пространства имён
        :param str login: имя пользователя
        :param str password: пароль
        :param list namespaces: информация о разрешённых для данного
            пользователя пространтствах имён, необходимо для учётных
            записей, поддерживающих нескольких клиентов. Каждый элемент
            списка - это :class:`dict` следующего формата:
            ``{'namespace': ns, 'roles': [role1, role2, ...]}``, где ``ns`` и
            `roleX` - идентификаторы соответствующих объектов.
        :param dict settings: настройки пользователя, ключи данных должны быть
            строкамии, а значения должны иметь элементарный тип, легко
            кодируемый в JSON
        :param str name: реальное имя человека
        :param str patronymic: отчество
        :param str surname: фамилия
        :param dict social: информация о социальных сетях, ключ - код
            социальной сети (``facebook``, ``vk``...), значение -
            :class:`dict` со специфическими настройками социальной сети'''
        if name:
            #: Настояще имя человека
            self.name = name

        if patronymic:
            #: Отчество человека
            self.patronymic = patronymic

        if surname:
            #: Фамилия человека
            self.surname = surname

        if social is not None:
            #: Информация социальных сетей. Это :class:`dict`, ключи которого указывают на
            #: соответствующую социальную сеть, а значения, в свою очередь, также
            #: являются :class:`dict` со своими ключами. Ключи социальных сетей:
            #:
            #:  * ``vk`` - ВКонтакте.
            self.social = {}

        super().__init__(ns=ns,
                         login=login,
                         password=password,
                         namespaces=namespaces,
                         settings=settings)

    def full_name(self):
        '''Возвращает ИОФ человека в формате `Имя Отчество Фамилия`'''
        attrs = ( 'surname', 'name', 'patronymic')
        return ' '.join([getattr(self, x) for x in attrs if hasattr(self, x)])
