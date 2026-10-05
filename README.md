[![pipeline status](https://gitlab.com/vw-type2/vw-type2-id/badges/master/pipeline.svg)](https://gitlab.com/vw-type2/vw-type2-id/commits/master)
[![coverage report](https://gitlab.com/vw-type2/vw-type2-id/badges/master/coverage.svg)](https://vw-type2.gitlab.io/vw-type2-id)

## Volkswagen Type 2 identification

A set of tools to identify VW Type 2 vehicles for model years 1968 to 1979.

![Type 2 ID](https://i.imgur.com/DWkcx2v.gif)

https://vw-type2-id.xyz/

Developed with:
- [Django](https://www.djangoproject.com/)
- [Python 3](https://python.org)
- [Bootstrap](https://getbootstrap.com/)

### M-plate decoder

The main app on the site: decode the [M-plate](https://vw-type2-id.xyz/mplate/) and find production data for your bus. 

https://vw-type2-id.xyz/mplate/decode/

#### Local development

Local development is done in a Python virtual environment. To get started:

1. Clone this repository
1. `cd vw-type2-id`
1. `python3 -m venv .venv && . .venv/bin/activate`
1. Install project dependencies => `pip install -r requirements-dev.txt`
1. You should be all set for development in this virtual environment. Use the django management commands to run and manage your app. E.g. `python ./manage.py runserver` to start the server.
