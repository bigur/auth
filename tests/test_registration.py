__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from re import DOTALL, MULTILINE, match

from pytest import fixture, mark

logger = getLogger(__name__)


@fixture(scope='function')
def reg_endpoint(app):
    logger.debug('Add registration route')
    from bigur.auth.authn import Registration
    return app.router.add_route('*', '/auth/registration', Registration)


class TestRegistration(object):
    '''Test user registration'''

    @mark.asyncio
    async def test_registration_form(self, reg_endpoint, cli):
        response = await cli.get('/auth/registration')
        assert response.status == 200
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert match(r'.*<form.*>.*</form>.*', await response.text(),
                     DOTALL | MULTILINE) is not None

    @mark.asyncio
    async def test_html_registration(self, reg_endpoint, store, cli, debug):
        response = await cli.post(
            '/auth/registration',
            data={
                'given_name': 'Ivan',
                'patronymic': 'Ivanovich',
                'family_name': 'Smirnov',
                'username': 'admin',
                'password': '123'
            },
            headers={'Accept': 'text/plain'})
        assert (await response.text()) == ('Login successful')
        assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert response.status == 200

        user = store.users.get_by_username('admin')
        assert 'Ivan' == user.given_name
        assert 'Ivanovich' == user.patronymic
        assert 'Smirnov' == user.family_name

    @mark.asyncio
    async def test_invalid_json(self, reg_endpoint, store, cli, debug):
        response = await cli.post(
            '/auth/registration',
            headers={'Content-Type': 'application/json'},
            data=b'{"given_name": "123')
        assert 400 == response.status

    @mark.asyncio
    async def test_json_registration(self, reg_endpoint, store, cli, debug):
        response = await cli.post(
            '/auth/registration',
            json={
                'given_name': 'Ivan',
                'patronymic': 'Ivanovich',
                'family_name': 'Sidorov',
                'username': 'admin',
                'password': '123'
            },
            headers={'Accept': 'application/json; q=0.9, text/html; q=0.5'})
        assert 200 == response.status
        assert ('application/json; '
                'charset=utf-8' == response.headers['Content-Type'])
        res_data = await response.json()

        assert {'status': 'ok'} == res_data['meta']

        user = store.users.get_by_username('admin')
        assert 'Ivan' == user.given_name
        assert 'Ivanovich' == user.patronymic
        assert 'Sidorov' == user.family_name

        assert {
            'id': user.id,
            'username': user.username,
            'given_name': user.given_name,
            'patronymic': user.patronymic,
            'family_name': user.family_name
        } == res_data['data']

    # TODO: Bad content type
    # TODO: Long fields
    # TODO: Invalid url encoded form
    # TODO: Username already exists
