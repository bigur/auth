__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import asdict as asdict_core
from importlib import import_module
from sys import modules


def import_class(name):
    '''Import module and return class from it.
    :param str name: full path to class with dot as delemiter,
        e.g. `a.b.c.Class`'''

    module_name, class_name = name.rsplit('.', 1)
    try:
        module = modules[module_name]
    except KeyError:
        module = import_module(module_name)
    return getattr(module, class_name)


def asdict(self, *, dict_factory=dict):
    '''Returns :func:`dataclasses.asdict` without `None` values,
    empty lists and dicts.'''

    result = dict_factory()
    for k, v in asdict_core(self).items():
        if v is None:
            continue
        elif isinstance(v, (list, dict)) and not v:
            continue
        result[k] = v
    return result
