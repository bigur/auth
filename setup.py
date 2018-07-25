#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from setuptools import setup


setup(
    name='bigur-auth',
    version='1.0.0',

    # Мета-информация
    description='Сервер авторизации',
    url='http://www.bigur.com/',

    author='Геннадий Ковалёв',
    author_email='gik@bigur.ru',

    license='Proprietary',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.5',
    ],

    keywords=['bigur', 'auth'],

    # Библиотека
    packages=['bigur/auth'],

    # Файлы настроек
    data_files=[('/etc/bigur', ['conf/auth.conf'])],

    # Скрипт запуска сервера
    scripts=['bin/authd']
)
