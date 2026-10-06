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

#### Translations

Translatable strings come from two places: the code and templates, and the reference data (M-code descriptions, colours, countries, engines and gearboxes), which lives in the production database. The reference data strings are exported to `mplate_decoder/db_strings.py`, which is committed, so the translation catalogs can be regenerated without a database.

```mermaid
flowchart LR
    subgraph prod["Only with production access"]
        A["Edit reference data<br>in the admin"] --> B["Refresh db_strings.py<br>(export_db_strings)"]
    end
    B -->|commit| R[("Repo: code +<br>db_strings.py")]
    subgraph any["Anyone, no database"]
        R --> C["makemessages<br>regenerates the .pot"]
        C --> D["Translate<br>(Crowdin or .po files)"]
        D -->|commit| R
    end
```

**For admins with database access**
- After editing the reference data: save a dump of the production reference data as `mplate_decoder/fixtures/mplate_reference.json`, run `make db-strings` and commit `db_strings.py` and the catalogs. The rule loads the dump into your development database.
- Don't edit `db_strings.py` by hand.

**For developers**
- Regenerate the catalogs (no database needed):
  `make messages` updates `vw_type2_id/locale/django.pot` and the `.po` files. Then run `python manage.py compilemessages`.
- Commit the updated .pot with the code change that adds or changes a string. CI fails if the committed .pot is out of date.

**Optional: update the catalogs on every commit**

[pre-commit](https://pre-commit.com) can run `make messages` before each commit, so you don't have to remember it. It comes with the development dependencies; to enable it, run `pre-commit install` once per clone, with the virtual environment active.

From then on, when a commit touches code or templates and the catalogs change, the commit stops. Add the catalogs with `git add vw_type2_id/locale` and commit again. Commit with the virtual environment active and `DJANGO_VW_TYPE2_ID_SECRET_KEY` set, as for any management command. To skip the hook for one commit, use `git commit --no-verify`.
