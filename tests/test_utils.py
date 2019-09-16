__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.utils import get_accept, choice_content_type


class TestUtils(object):
    '''Test various utils'''

    def test_get_accept(self):
        '''Test accept header'''
        assert ([
            'text/html',
            'application/json',
        ] == get_accept('application/json; q=0.3, '
                        'text/html; q=0.4'))

        assert ([
            'text/plain',
            'application/json',
            'application/octet-stream',
        ] == get_accept('application/json; q=0.9, '
                        '*, '
                        'application/octet-stream; q=0.8'))

    def test_choice_content_type(self):
        accepts = get_accept('application/json; q=0.9, '
                             '*, '
                             'application/octet-stream; q=0.8')
        assert ('text/plain' == choice_content_type(
            accepts, {'application/json', 'text/plain'}))
