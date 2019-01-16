#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from setuptools import setup

exec( # pylint: disable=W0122
    compile(
        open('bigur/auth/version.py', "rb").read(),
        'bigur/auth/version.py',
        'exec'
    ),
    globals(),
    locals()
)

setup(
    name='bigur-auth',
    # pylint: disable=E0602
    version=__version__, # type: ignore

    # Мета-информация
    description='Сервер авторизации',
    url='http://www.bigur.com/',

    author='Геннадий Ковалёв',
    author_email='gik@bigur.ru',

    license='Proprietary',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
    ],

    keywords=['bigur', 'auth'],

    # Библиотека
    packages=['bigur/auth',
              'bigur/auth/amqp',
              'bigur/auth/migration'],

    # Файлы настроек
    data_files=[('/etc/bigur', ['conf/auth.conf'])]
)
