__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.utils import parse_accept, choice_content_type


class TestUtils(object):
    '''Test various utils'''

    def test_parse_accept(self):
        '''Test accept header'''
        assert ([('text/html', 0.4), ('application/json', 0.3)] == parse_accept(
            'application/json; q=0.3, '
            'text/html; q=0.4'))

        assert ([
            ('*/*', 1),
            ('application/json', 0.9),
            ('application/octet-stream', 0.8),
        ] == parse_accept('application/json; q=0.9, '
                          '*/*, '
                          'application/octet-stream; q=0.8'))

        assert ([('application/signed-exchange', 1.0),
                 ('application/xhtml+xml', 1.0), ('image/apng', 1.0),
                 ('image/webp', 1.0), ('text/html', 1.0),
                 ('application/xml', 0.9), ('*/*', 0.8)] == parse_accept(
                     'text/html,'
                     'application/xhtml+xml,'
                     'application/xml;q=0.9,'
                     'image/webp,'
                     'image/apng,'
                     '*/*;q=0.8,'
                     'application/signed-exchange;v=b3'))

    def test_choice_content_type(self):
        assert ('application/json' == choice_content_type([
            ('*/*', 1),
            ('application/json', 0.9),
            ('application/octet-stream', 0.8),
        ], ['application/json', 'text/plain']))
        assert ('application/octet-stream' == choice_content_type([
            ('application/json', 0.9),
            ('application/octet-stream', 0.9),
            ('*/*', 0.1),
        ], ['application/octet-stream', 'text/plain']))

        assert ('text/html' == choice_content_type(
            [('text/html', 1), ('application/xhtml+xml', 1),
             ('application/xml', 0.9), ('image/webp', 1), ('image/apng', 1),
             ('*/*', 0.8), ('application/signed-exchange', 1)],
            ['application/json', 'text/html']))
