__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass

from bigur.auth.oauth2.request import OAuth2Request


@dataclass
class OIDCRequest(OAuth2Request):
    pass
    # XXX: Properties from old class, check and remove
    # scope: List[str]
    # response_type: List[str]
    # state: Optional[str] = None
    # response_mode: Optional[str] = None
    # nonce: Optional[str] = None
    # display: Optional[str] = None
    # user: Optional[str] = None
    # acr_values: List[str] = field(default_factory=list)
