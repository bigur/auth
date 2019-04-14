__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from typing import Optional, Set

from bigur.auth.model import Client, User


@dataclass
class OAuth2Request:
    # Resource owner
    owner: User

    # RFC 6749 parameters
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    response_type: Set = field(default_factory=set)

    # Internal parameters
    client: Optional[Client] = None

    def __post_init__(self):
        keys = 'response_type', 'scope'
        for key in keys:
            value = getattr(self, key, None)
            if value is None:
                setattr(self, key, set())
            elif isinstance(value, str):
                setattr(self, key, {x for x in value.split() if x})
