__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import asdict as asdict_core
from importlib import import_module
from sys import modules
from typing import Dict, List, Set


def import_class(name: str):
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


def get_accept(header_string: str, default='text/plain') -> List[str]:
    if not header_string:
        return [default]

    parsed: Dict[str, float] = {}

    for record in [x.strip() for x in header_string.split(',')]:
        parts = record.split(';')
        ctype = parts.pop(0).strip().lower()
        if ctype in ('*', '*/*'):
            ctype = default
        quality: float = 1.0
        for param in parts:
            if '=' not in param:
                continue
            k, v = param.split('=')
            if k.strip() == 'q':
                try:
                    quality = float(v.strip())
                except ValueError:
                    continue
                else:
                    break
        parsed[ctype] = quality

    return [k for k in reversed(sorted(parsed, key=lambda x: parsed[x]))]


def choice_content_type(ctypes: List[str], needed: Set[str]) -> str:
    for accept in ctypes:
        if accept in needed:
            return accept
    return next(iter(needed))
