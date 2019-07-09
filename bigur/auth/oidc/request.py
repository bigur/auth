__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from typing import Optional, Set

from bigur.auth.oauth2.request import OAuth2Request


@dataclass
class OIDCRequest(OAuth2Request):
    response_mode: Optional[str] = None
    nonce: Optional[str] = None
    display: Optional[str] = None
    acr_values: Set[str] = field(default_factory=set)
