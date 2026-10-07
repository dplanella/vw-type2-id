# Contributing

- Every change goes through a pull request to `master`. CI lints the code,
  checks migrations and the translation template, and runs the tests; a pull
  request can be merged only when the tests pass.
- Pull requests are merged with a merge commit.
- **Merging to `master` deploys to production.** CI builds the image and
  deploys it straight away; there is no staging environment. Merge only what
  is ready to go live.
- When a change adds or changes a translatable string, commit the updated
  translation template with it (see [docs/translations.md](docs/translations.md)).

See [docs/](docs/README.md) for setting up a development environment and for
how translations are managed.
