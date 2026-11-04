# auctionite-py

Django + Django REST Framework backend for Auctionite.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Docker (for postgres)
- [Task](https://taskfile.dev/) (optional — every task is just a `uv run ...` command)

## Setup

```sh
cp .env.example .env   # local values, works as-is with docker-compose.yml
docker compose up -d   # postgres (task db:up also works)
uv sync
uv run python manage.py migrate
```

## Configuration

Everything database-related is driven by `.env` — there are no built-in
defaults, a missing variable fails with a clear error. The same file feeds
Django (python-dotenv) and docker compose (variable interpolation); real
environment variables take precedence over `.env`.

`python-dotenv` is a dev-only dependency: a default `uv sync` installs it and
Django reads `.env`. Production installs (`uv sync --no-dev`) skip the file, so
export the variables in the real environment there.

| Variable             | Purpose                                                        |
| -------------------- | -------------------------------------------------------------- |
| `DATABASE_NAME`      | dev database (`runserver`, `migrate`, `seed`)                  |
| `TEST_DATABASE_NAME` | separate database for `manage.py test`                         |
| `DATABASE_USER`      | postgres user (also the container's superuser)                 |
| `DATABASE_PASSWORD`  | postgres password                                              |
| `DATABASE_HOST`      | postgres host (`localhost` for docker)                         |
| `DATABASE_PORT`      | host port postgres is published on                             |

Tests never touch dev data: `manage.py test` creates `TEST_DATABASE_NAME`,
migrates it, and destroys it again — Django's test-database override, so no
separate test settings module is needed. Postgres only reads its
`POSTGRES_*` values on first init of the volume; after changing them run
`docker compose down -v`.

## Development

```sh
task db:up      # start postgres
task db:down    # stop postgres
task db:psql    # psql into the dev database
task run        # ./manage.py runserver
task test       # ./manage.py test (against auctionite_test)
task seed       # demo user + 5 items, each with generated pictures
task lint       # ruff check
task format     # ruff format + import sorting
task typecheck  # pyrefly
task check      # lint + typecheck
```

## Layout

- `config/` — settings, urls, wsgi/asgi
- `src` — Django apps
