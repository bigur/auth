__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp_jinja2 import render_template
from aiohttp.web_exceptions import HTTPError, HTTPBadRequest, HTTPForbidden

from bigur.auth.authn.base import AuthN
from bigur.auth.model import User


logger = getLogger(__name__)

FIELD_LENGHT = 128


class UserPass(AuthN):
    '''Авторизация по логину и паролю'''

    def __init__(self, verify_uri: str = '/login'):
        self.verify_uri = verify_uri
        super().__init__()

    async def verify(self, request):
        user = None
        context = {}

        # XXX: check forward

        if request.method == 'POST':
            post = await request.post()

            if (request.path == self.verify_uri and
                    'username' in post and
                    'password' in post):

                try:
                    # Проверяем входящие параметры
                    username = post['username']
                    password = post['password']

                    if (not isinstance(username, str) or
                            not isinstance(password, str)):
                        raise HTTPBadRequest()

                    if (len(username) > FIELD_LENGHT or
                            len(password) > FIELD_LENGHT):
                        raise HTTPBadRequest()

                    # Находим пользователя
                    logger.debug('Выполняем аутентификацию для %s', username)

                    user = await User.find_one({'username': username})
                    if user is None:
                        logger.warning(
                            'Пользователь с логином {} не найден'.format(
                                username))
                        raise HTTPForbidden()

                    # Проверяем пароль
                    if not user.verify_password(password):
                        logger.warning(
                            'Неверный пароль для пользователя {}'.format(
                                username))
                        user = None
                        raise HTTPForbidden()

                except HTTPError as e:
                    context['error'] = str(e)
                    context['error_code'] = e.status_code

        if user is None:
            # Либо ничего не передают, либо аутентификация не удалась.
            # Возвращаем форму ввода логина-пароля.
            return render_template('login_form.j2', request, context)

        return user
