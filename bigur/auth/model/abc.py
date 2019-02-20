__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union


class AbstractUser(ABC):

    @abstractmethod
    def get_id(self) -> Optional[Union[int, str]]:
        '''Returns user's id.'''
        raise NotImplementedError

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


class AbstractClient(ABC):

    @abstractmethod
    def get_id(self) -> Optional[Union[int, str]]:
        '''Returns client's id.'''
        raise NotImplementedError


class AbstractProvider(ABC):

    @abstractmethod
    def get_id(self) -> Optional[Union[int, str]]:
        '''Return provider's id.'''
        raise NotImplementedError

    @abstractmethod
    async def get_authorization_endpoint(self) -> str:
        '''Return authorization endpoint url.'''
        raise NotImplementedError

    @abstractmethod
    async def get_token_endpoint(self) -> str:
        '''Return token endpoint url.'''
        raise NotImplementedError

    @abstractmethod
    async def get_client_id(self) -> str:
        '''Return client_id.'''
        raise NotImplementedError

    @abstractmethod
    async def get_client_secret(self) -> str:
        '''Return client_secret.'''
        raise NotImplementedError

    @abstractmethod
    async def get_response_types_supported(self) -> List[str]:
        '''Return list of supported response types.'''
        raise NotImplementedError

    @abstractmethod
    async def get_scopes_supported(self) -> List[str]:
        '''Return list of supported scopes.'''
        raise NotImplementedError

    @abstractmethod
    async def update_keys(self) -> None:
        '''Download keys from `jwks_uri` and prepare to store them into db.'''
        raise NotImplementedError

    @abstractmethod
    async def get_key(self, kid: str) -> Dict[str, str]:
        '''Return key with `kid`.'''
        raise NotImplementedError
