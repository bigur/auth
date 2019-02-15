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
    async def get_by_oidp(self, provider_id: K, user_id: str) -> T:
        raise NotImplementedError


class Store(ABC):

    providers: ProvidersCollection
    users: UsersCollection

    @abstractmethod
    def __init__(self):
        raise NotImplementedError
