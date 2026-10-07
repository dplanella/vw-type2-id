# Local development

Local development is done in a Python 3.13 virtual environment, created with
[uv](https://docs.astral.sh/uv/), which installs Python 3.13 itself if your
system has another version. Without `DATABASE_URL` the app uses a local SQLite
file (`db.sqlite3`).

1. Install gettext (`sudo apt install gettext`),
   [uv](https://docs.astral.sh/uv/getting-started/installation/), and Google
   Chrome or Chromium for the browser test
1. Clone this repository and `cd vw-type2-id`
1. Create the virtual environment and install the dependencies:
   `uv venv --python 3.13 .venv && . .venv/bin/activate && uv pip install -r requirements-dev.txt`.
   uv environments have no `pip`, so always use `uv pip` there.
1. Set the environment for each shell:
   `export DJANGO_VW_TYPE2_ID_SECRET_KEY=dev DJANGO_DEBUG=1`
1. Create the database and compile the translations:
   `python manage.py migrate && python manage.py compilemessages`
1. Load reference data: the test fixtures give a minimal set
   (`python manage.py loaddata tst_mplate_vwtype2model tst_mplate_engine tst_mplate_gearbox`).
   The full reference data is not in this repository; if you have an export,
   save it as `mplate_decoder/fixtures/mplate_reference.json` (ignored by git)
   and run `python manage.py loaddata mplate_reference` on an empty database.
1. Run the site with `python manage.py runserver`, the tests with `pytest`
   and the linter with `make lint`.

If your system Python is already 3.13, `python3 -m venv .venv` and
`pip install -r requirements-dev.txt` work too.

To use PostgreSQL as in CI, start one in a container with
`docker run -d --name vw-postgres -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=vw -p 127.0.0.1:5432:5432 postgres:18`
and set `DATABASE_URL=postgres://postgres:dev@localhost:5432/vw`.

## Production data

The full reference data lives only in the production database. Maintainers
with server access can find the export steps in the private server
repository's documentation.

To refresh the translatable reference data strings, see
[translations.md](translations.md).
