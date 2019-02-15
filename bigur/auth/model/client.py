__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass

from bigur.auth.model.base import Object


@dataclass
class Client(Object):

    title: str
    user_id: str
    grant_type: str
    authentication_required: bool = False
