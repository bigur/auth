__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import uuid4

from bigur.auth.model.abc import AbstractAccessCode
from bigur.auth.model.base import Object


@dataclass
class AccessCode(Object, AbstractAccessCode):
    #: Code string.
    code: str = field(default_factory=lambda: uuid4().hex)

    #: Scopes which will be used when generate token by this code.
    scopes: List[str] = field(default_factory=list)

    #: Timestamp when code generated.
    created: datetime = field(default_factory=datetime.now)

    #: True if this code already used.
    used: bool = field(default=False)
