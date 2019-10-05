__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

# flake8: noqa

from .memory import Memory


class DatabaseProxy:

    def __init__(self):
        self._store = None

    def set_store(self, instance):
        self._store = instance

    def __getattribute__(self, name):
        if name in ('_store', 'set_store'):
            return super().__getattribute__(name)
        if not self._store:
            raise ValueError('Store not initialized')
        return self._store.__getattribute__(name)

    def __setattr__(self, name, value):
        if name == '_store':
            super().__setattr__(name, value)
        elif not self._store:
            raise ValueError('Store not initialized')
        else:
            self._store.__setattr__(name, value)


store = DatabaseProxy()
