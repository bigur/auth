API reference
=============

Authentication
--------------
.. automodule:: bigur.auth.authn


Client authentication
~~~~~~~~~~~~~~~~~~~~~
.. automodule:: bigur.auth.authn.client
.. autofunction:: bigur.auth.authn.client.authenticate_client



User registration & authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: bigur.auth.authn.user
.. autofunction:: bigur.auth.authn.user.authenticate_end_user
.. autoclass:: bigur.auth.authn.user.base.AuthN


User registration
.................
.. automodule:: bigur.auth.authn.user.registration
.. autoclass:: bigur.auth.authn.user.Registration


User & password
...............
.. automodule:: bigur.auth.authn.user.user_pass
.. autoclass:: bigur.auth.authn.user.UserPass


External OpenID connect provider
................................
.. automodule:: bigur.auth.authn.user.oidc
.. autoclass:: bigur.auth.authn.user.OpenIDConnect


Bearer token
............
.. automodule:: bigur.auth.authn.user.token
.. autoclass:: bigur.auth.authn.user.Token


HTTP Handlers
-------------
.. automodule:: bigur.auth.handler
.. autoclass:: bigur.auth.handler.base.OAuth2Handler


OAuth2 handlers
~~~~~~~~~~~~~~~
.. automodule:: bigur.auth.handler.oauth2
.. autoclass:: bigur.auth.handler.oauth2.authorize.AuthorizationHandler
.. autoclass:: bigur.auth.handler.oauth2.token.TokenHandler


OpenIDConnect handlers
~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: bigur.auth.handler.oidc


OAuth2 features
---------------
.. automodule:: bigur.auth.oauth2.validators
.. automodule:: bigur.auth.oauth2.validators.response_type

OpenID Connect features
-----------------------

Model
-----
.. automodule:: bigur.auth.model
.. automodule:: bigur.auth.model.base

Client
~~~~~~
.. automodule:: bigur.auth.model.client

User
~~~~
.. automodule:: bigur.auth.model.user
