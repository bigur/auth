__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from bigur.utils import AttrDict

from bigur.auth.user import User, Human
from bigur.auth.namespace import Namespace
from bigur.auth.role import Role
from bigur.auth.amqp.core import Service


class GetUser(Service):

    __section__ = 'gql'

    async def call(self, context: dict):
        user = await User.find_one({
            'login': context['user']
        })
        result = {
            '__typename': type(user).__name__,
            'id': user.id,
            'ns': user.ns,
            'login': user.login,
            'namespaces': [],
        }

        for record in user.namespaces:
            namespace = await Namespace.find_one({'_id': record['namespace']})
            nsinfo = AttrDict(
                namespace=AttrDict(
                    id=namespace.id,
                    title=namespace.title
                )
            )

            roles = []
            for role_id in record['roles']:
                role = await Role.find_one({'_id': role_id})
                roles.append(AttrDict(
                    id=role.id,
                    title=role.title,
                    permissions=role.permissions,
                ))
            if roles:
                nsinfo['roles'] = roles

            result['namespaces'].append(nsinfo)

        if isinstance(user, Human):
            result['name'] = getattr(user, 'name', None)
            result['patronymic'] = getattr(user, 'patronymic', None)
            result['surname'] = getattr(user, 'surname', None)
            result['full_name'] = user.full_name()
        return result


class ChangeNamespace(Service):

    __section__ = 'gql'

    async def call(self, ns: str, context: dict):
        print('in call')
        user = await User.find_one({
            'login': context['user']
        })

        ns_ids = [x['namespace'] for x in user.namespaces]
        print(ns_ids)
        if ns not in ns_ids:
            raise KeyError('запрос на имену запрещённого ns')

        user.ns = ns
        await user.save()

        result = {'ns': ns}

        return result
