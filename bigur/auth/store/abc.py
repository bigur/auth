__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')
K = TypeVar('K')


class Collection(Generic[T, K], ABC):

    def __init__(self, store: 'Store'):
        self.store = store

    @abstractmethod
    async def create(self, **kwargs) -> T:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: K) -> T:
        raise NotImplementedError

    @abstractmethod
    async def put(self, obj: T) -> T:
        raise NotImplementedError


class ProvidersCollection(Collection[T, K]):

    @abstractmethod
    async def get_by_domain(self, domain: str) -> T:
        raise NotImplementedError


class UsersCollection(Collection[T, K]):

    @abstractmethod
    def get_by_username(self, username: str) -> T:
        raise NotImplementedError

    @abstractmethod
    async def get_by_oidp(self, provider_id: K, user_id: str) -> T:
        raise NotImplementedError


class ClientsCollection(Collection[T, K]):
    pass


class ScopesCollection(Collection[T, K]):
    pass


class AccessCodeCollection(Collection[T, K]):

    @abstractmethod
    def get_by_code(self, code: str) -> T:
        raise NotImplementedError


class Store(ABC):

    providers: ProvidersCollection
    users: UsersCollection
    scopes: ScopesCollection
    clients: ClientsCollection
    access_codes: AccessCodeCollection

    @abstractmethod
    def __init__(self):
        raise NotImplementedError
