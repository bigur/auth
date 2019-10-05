__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import InitVar, dataclass, field
from logging import getLogger
from typing import Dict, Optional

from bigur.auth.model.abc import AbstractUser
from bigur.auth.model.base import Object, PasswordMixin

logger = getLogger(__name__)


@dataclass
class UserMixin(Object):
    username: str
    oidc_accounts: Optional[Dict[str, str]] = None


@dataclass
class User(PasswordMixin, UserMixin, AbstractUser):

    def add_oidc_account(self, provider_id: str, subject: str):
        if self.oidc_accounts is None:
            self.oidc_accounts = {}
        self.oidc_accounts[provider_id] = subject

    def delete_oidc_account(self, provider_id: str):
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
