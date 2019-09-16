#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from setuptools import setup

exec(  # pylint: disable=W0122
    compile(
        open('bigur/auth/version.py', "rb").read(), 'bigur/auth/version.py',
        'exec'), globals(), locals())

setup(
    # pylint: disable=E0602
    version=__version__,  # type: ignore  # noqa
)
