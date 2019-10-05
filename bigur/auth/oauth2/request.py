__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, fields
from typing import Set


@dataclass
class OAuth2Request:

    def __post_init__(self):
        keys = {x.name for x in fields(self) if x.type == Set[str]}
        for key in keys:
            value = getattr(self, key, None)
            if value is None:
                setattr(self, key, set())
            elif isinstance(value, str):
                setattr(self, key, {x for x in value.split() if x})
