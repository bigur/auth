__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from typing import List, Optional, Union

from bigur.auth.model.base import Object, PasswordMixin


@dataclass
class ClientMixin(Object):
    '''Base class for :class:`~bigur.auth.model.client.Client`. This class
    needed for propertly arguments resolution for :mod:`dataclasses`: position arguments
    must be before named.'''

    #: Client type: must be `confidential` or `public`.
    client_type: str

    #: Id of client's owner (:class:`~bigur.auth.model.user.User`).
    user_id: Union[str, int]

    #: Client title.
    title: str

    #: List of allowed redirect URIs.
    redirect_uris: Optional[List[str]] = None


@dataclass
class Client(PasswordMixin, ClientMixin):
    '''RFC6749's client - application making protected resource request.'''

    def __post_init__(self, password) -> None:
        if self.client_type not in ('public', 'confidential'):
            raise TypeError('Client type must be public or confidential')
        if password is not None:
            password = password.strip()
        if self.client_type == 'confidential' and not password:
            raise TypeError('Password is required for confidential clients')
        super().__post_init__(password)

    def check_redirect_uri(self, uri: str) -> bool:
        if self.redirect_uris:
            return uri.lower() in self.redirect_uris
        return False
