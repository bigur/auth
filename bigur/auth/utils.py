__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from importlib import import_module
from sys import modules


def import_class(name):
    module_name, class_name = name.rsplit('.', 1)
    try:
        module = modules[module_name]
    except KeyError:
        module = import_module(module_name)
    return getattr(module, class_name)
