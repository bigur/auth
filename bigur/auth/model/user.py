__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import InitVar, dataclass, field
from hashlib import sha512
from logging import getLogger
from typing import Dict, Optional
from uuid import uuid4

from bigur.auth.model.abc import AbstractUser
from bigur.auth.model.base import Object

logger = getLogger(__name__)


@dataclass
class User(Object, AbstractUser):
    username: str
    crypt: str = field(init=False, repr=False)
    salt: str = field(init=False, repr=False)
    password: InitVar[Optional[str]] = None
    oidc_accounts: Optional[Dict[str, str]] = None

    def __post_init__(self, password):
        if password is not None:
            self.set_password(password)
        else:
            self.salt = None
            self.crypt = None
        super().__post_init__()

    @staticmethod
    def _get_hash(salt: str, password: str) -> str:
        return sha512((password + salt).encode('utf-8')).hexdigest()

    def set_password(self, password: str):
        self.salt = uuid4().hex
        self.crypt = self._get_hash(self.salt, password)

    def verify_password(self, password: str) -> bool:
        if self.salt and self.crypt:
            return self.crypt == self._get_hash(self.salt, password)
        return False

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
