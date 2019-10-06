__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger
from typing import Dict, Optional

from bigur.auth.model.abc import AbstractUser
from bigur.auth.model.base import Object, PasswordMixin

logger = getLogger(__name__)


@dataclass
class UserMixin(Object):
    '''Base class for :class:`~bigur.auth.model.user.User`.'''
    #: User\'s login.
    username: str

    #: User\'s external OpenID connect accounts. Is is a :class:`dict`
    #: with :class:`~bigur.auth.model.provider.Provider`.id as key
    #: and OpenID connect provider's user id (subject field of token) as
    #: value.
    oidc_accounts: Optional[Dict[str, str]] = None


@dataclass
class User(PasswordMixin, UserMixin, AbstractUser):

    def add_oidc_account(self, provider_id: str, subject: str) -> None:
        '''Add external OpenID connect account to user's record.

        :param str provider_id: id of
            :class:`~bigur.auth.model.provider.Provider`
        :param str subject: OpenID connect's user id'''
        if self.oidc_accounts is None:
            self.oidc_accounts = {}
        self.oidc_accounts[provider_id] = subject

    def delete_oidc_account(self, provider_id: str) -> None:
        '''Delete external OpenID connect account to user's record.

        :param str provider_id: id of
            :class:`~bigur.auth.model.provider.Provider`'''
        if self.oidc_accounts:
            try:
                del self.oidc_accounts[provider_id]
            except KeyError:
                pass


@dataclass
class Human(User):

    given_name: Optional[str] = None
    patronymic: Optional[str] = None
    family_name: Optional[str] = None
