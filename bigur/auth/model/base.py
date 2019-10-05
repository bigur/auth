__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import InitVar, dataclass, field
from hashlib import sha512
from typing import Optional, Union
from uuid import uuid4


@dataclass
class Object:

    id: Optional[Union[int, str]] = field(init=False)

    def __post_init__(self):
        self.id = None

    def get_id(self) -> Optional[Union[int, str]]:
        return self.id


@dataclass
class PasswordMixin:
    #: Client's password, init var only, not saved in instance.
    password: InitVar[Optional[str]] = None

    #: Client's password hash.
    crypt: Optional[str] = field(init=False, repr=False, default=None)

    #: Client's password hash salt.
    salt: Optional[str] = field(init=False, repr=False, default=None)

    def __post_init__(self, password) -> None:
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
