# bigur.auth

[![Documentation Status](https://readthedocs.org/projects/bigur-auth/badge/?version=latest)](https://bigur-auth.readthedocs.io/en/latest/?badge=latest) [![Build Status](https://travis-ci.org/bigur/auth.svg?branch=master)](https://travis-ci.org/bigur/auth) [![Coverage Status](https://coveralls.io/repos/github/bigur/auth/badge.svg?branch=master)](https://coveralls.io/github/bigur/auth?branch=master) [![Join the chat at https://gitter.im/bigur-auth/community](https://badges.gitter.im/bigur-auth/community.svg)](https://gitter.im/bigur-auth/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

OpenID connect &amp; OAuth2 server writed with python 3 and uses asyncio library.

**Warning!** This project under development, please do not use it in production systems.

I really appreciate your contribution in project.

## Features

- Client authentication
  - [X] Login & password authentication
  - [ ] HTTP Basic authentication
- End user registration & authentication
  - User registration
    - [X] Via web-form
    - [X] Via JSON request
  - Authentication via username & password
    - [X] Via HTML form
    - [X] Via JSON request
  - [X] Authentication via external OpenID connect provider
  - [X] HTML-forms customization using [jinja2](https://github.com/pallets/jinja) templates
- OAuth2 features
  - Endpoints
    - [X] Authorization endpoint
    - [ ] Token endpoint
  - Grant
    - [ ] Authorization code grant
    - [ ] Implicit grant
    - [ ] Resource Owner Password Credentials Grant
    - [ ] Client Credentials Grant
- [ ] OpenID Connect features
- Database engines
  - [X] Memory (for tests, all data will be lost after restart)
  - [ ] MongoDB
  - [ ] PostgreSQL
  - [ ] MySQL
- Plugins
  - [ ] RabbitMQ support

## Installation

External dependencies:

- [RxPY](https://github.com/ReactiveX/RxPY)

## Documentation

Project documentation available at [bigur-auth.readthedocs.io](https://bigur-auth.readthedocs.io/).
