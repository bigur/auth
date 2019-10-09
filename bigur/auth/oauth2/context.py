__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from typing import Optional

from aiohttp.web import Request as HTTPRequest
from multidict import MultiDict

from bigur.auth.model import Client, User
from bigur.auth.oauth2.request import OAuth2Request


@dataclass
class Context:
    #: Resource owner
    owner: Optional[User] = None

    #: Client for request
    client: Optional[Client] = None

    #: Original HTTP request
    http_request: Optional[HTTPRequest] = None

    #: HTTP GET/POST parametes
    http_params: Optional[MultiDict] = None

    #: OAuth2 request params
    oauth2_request: Optional[OAuth2Request] = None
