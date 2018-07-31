'''Пространство имён необходимо для отделения объектов одного клиента от
объектов другого. Пространство имён может содержать своих пользователей,
физических и юридических лиц, свои данные бухгалтерского учёта.

С точки зрения портала пространством имён можно считать зарегистрировавшегося
на сайте клиента.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from datetime import datetime

from bigur.store import Stored
from bigur.utils import localzone


logger = getLogger('namespace')


class Namespace(Stored):
    '''Класс пространства имён.'''

    __metadata__ = {
        'collection': 'namespaces',
    }

    def __init__(self, title, configurations):
        ''':param str title: название организации
        :param list configurations: список ИД конфигураций, доступных
            для данной организации'''
        #: Название организации.
        self.title = title

        #: Список (:class:`list`) ИД объектов
        #: :class:`~bigur.api.configuration.Configuration` - конфигураций
        #: организации.
        self.configurations = configurations

        #: Дата регистрации организации (:class:`datetime.datetime`).
        self.registered = datetime.now(tz=localzone)

        super().__init__()
