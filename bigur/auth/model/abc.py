__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from abc import ABC, abstractmethod


class User(ABC):

    @abstractmethod
    def set_password(self, password: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def verify_password(self, password: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def add_oidc_account(self, provider_id: str, subject: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_oidc_account(self, provider_id: str) -> None:
        raise NotImplementedError


class Client(ABC):
    pass


class Provider(ABC):

    @abstractmethod
    async def update_keys(self) -> None:
        '''Download keys from `jwks_uri` and prepare to store them into db.'''

    @abstractmethod
    async def get_key(self, kid: str):
        '''Return key with `kid`.'''
