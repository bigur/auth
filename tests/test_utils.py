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
