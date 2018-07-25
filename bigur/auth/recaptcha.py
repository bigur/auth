#!/usr/bin/env python3

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2017 Business group for development management'
__licence__ = 'For license information see LICENSE'

import json
import logging
import urllib.parse

import tornado.options as options
import tornado.httpclient as httpclient


options.define('recaptcha_secret',
                group='portal', help='code for recaptcha')


logger = logging.getLogger('office.recaptcha')


class ReCAPTCHA(object):

    url = 'https://www.google.com/recaptcha/api/siteverify'

    async def check(self, response, remoteip=None):
        secret = options.options.recaptcha_secret

        checked = False

        client = httpclient.AsyncHTTPClient()
        try:
            data = {'secret': secret, 'response': response}
            if remoteip is None:
                data['remoteip'] = remoteip
            body = urllib.parse.urlencode(data)
            result = await client.fetch(self.url, method='POST', body=body)
            if result.code == 200:
                data = {}
                try:
                    data = json.loads(result.body.decode('utf-8'))
                except:
                    pass
                checked = data.get('success')

        except (OSError, httpclient.HTTPError) as e:
            logger.error('Ошибка во время проверки ReCAPTCHA')

        return checked
