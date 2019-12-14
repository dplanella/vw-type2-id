## Volkswagen Type 2 identification

A set of tools to identify VW Type 2 vehicles for model years 1968 to 1979.

https://vw-type2-id.xyz/

Developed with:
- [Django](https://www.djangoproject.com/)
- [Python 3](https://python.org)
- [Bootstrap](https://getbootstrap.com/)

### M-plate decoder

The main app on the site: decode the [M-plate](https://vw-type2-id.xyz/mplate/) and find production data for your bus. 

https://vw-type2-id.xyz/mplate/decode/

#### Local development

Local development is done via a virtual environment managed with [`pipenv`](https://github.com/pypa/pipenv). To get started:

1. Clone this repository
1. Install `pipenv` => `pip3 install pipenv --user`
1. `cd vw-type2-id`
1. `pipenv shell`
1. Install project dependencies, if you've not already done it => `pipenv install`
1. You should be all set for development in this virtual environment. Use the django management commands to run and manage your app. E.g. `python ./manage.py runserver` to start the server.