__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from typing import Any, Optional


class Object:

    id: Optional[Any]

    def __init__(self):
        self.id = None
