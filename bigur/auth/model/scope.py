__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from typing import Optional

from bigur.auth.model.abc import AbstractScope
from bigur.auth.model.base import Object


@dataclass
class Scope(Object, AbstractScope):

    #: Unique code of scope.
    code: str

    #: Title of scope.
    title: str

    #: Description of scope.
    description: Optional[str] = None

    #: Is this scope will be returned if no scopes is request.
    default: bool = False
