__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from typing import Any, Dict, List
from uuid import uuid4

from bigur.auth.model import (
    Object,
    Provider,
    User,
    Human,
    Client,
    Scope,
    AccessCode,
)
from bigur.auth.store import abc


class Collection(abc.Collection[Object, str]):

    def __init__(self, store: abc.Store):
        self._db: Dict[str, Any] = dict()
        super().__init__(store)

    async def get(self, key: str) -> Object:
        return self._db[key]

    async def put(self, obj: Object) -> Object:
        if obj.id is None:
            obj.id = uuid4().hex
        self._db[obj.id] = obj
        return obj


class ProvidersCollection(Collection, abc.ProvidersCollection[Provider, str]):

    async def create(self, **kwargs) -> Provider:
        provider = Provider(**kwargs)
        await self.put(provider)
        return provider

    async def get_by_domain(self, domain: str) -> Provider:
        for v in self._db.values():
            if domain in getattr(v, 'domains', []):
                return v
        raise KeyError('Provider for domain {} not found'.format(domain))


class UsersCollection(Collection, abc.UsersCollection[User, str]):

    async def create(self, *, human=True, **kwargs) -> User:
        if human:
            user = Human(**kwargs)
        else:
            user = User(**kwargs)
        await self.put(user)
        return user

    def get_by_username(self, username: str) -> User:
        for v in self._db.values():
            if v.username == username:
                return v
        raise KeyError('User not found')

    async def get_by_oidp(self, provider_id: str, user_id: str) -> User:
        for v in self._db.values():
            if v.oidc_accounts and v.oidc_accounts.get(provider_id) == user_id:
                return v
        raise KeyError('User not found')


class ClientsCollection(Collection, abc.ClientsCollection[Client, str]):

    async def create(self, **kwargs) -> Client:
        client = Client(**kwargs)
        await self.put(client)
        return client


class ScopesCollection(Collection, abc.ClientsCollection[Scope, str]):

    async def create(self, **kwargs) -> Scope:
        scope = Scope(**kwargs)
        await self.put(scope)
        return scope

    async def get_by_code(self, code: str) -> Scope:
        for v in self._db.values():
            if v.code == code:
                return v
        raise KeyError('Scope not found.')

    async def get_default_scopes(self) -> List[Scope]:
        return [v for v in self._db.values() if v.default]


class AccessCodeCollection(Collection, abc.AccessCodeCollection[Scope, str]):

    async def create(self, **kwargs) -> AccessCode:
        if 'scopes' in kwargs and isinstance(kwargs['scopes'], set):
            kwargs['scopes'] = list(kwargs['scopes'])
        code = AccessCode(**kwargs)
        await self.put(code)
        return code

    async def get_by_code(self, code: str) -> AccessCode:
        for v in self._db.values():
            if v.code == code:
                return v
        raise KeyError('Access code not found.')


class Memory(abc.Store):

    def __init__(self):
        self.providers = ProvidersCollection(self)
        self.users = UsersCollection(self)
        self.clients = ClientsCollection(self)
        self.scopes = ScopesCollection(self)
        self.access_codes = AccessCodeCollection(self)
