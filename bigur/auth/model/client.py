__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from typing import Optional

from bigur.store import Stored


class Client(Stored):

    __metadata__ = {
        'collection': 'clients',
    }

    def __init__(self,
                 title: str,
                 user_id: str,
                 grant_type: str,
                 authentication_required: Optional[bool] = False):

        #: Наименование клиента
        self.title = title

        #: Идентификатор пользователя, которому принадлежит клиент
        self.user = user_id

        #: Тип разрешения
        self.grant_type = grant_type

        #: Нужна ли аутентификация
        self.authentication_required = authentication_required

        super().__init__()
