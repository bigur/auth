__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class Object:

    id: Optional[Union[int, str]] = field(init=False)

    def __post_init__(self):
        self.id = None

    def get_id(self) -> Optional[Union[int, str]]:
        return self.id
