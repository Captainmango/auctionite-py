# auctionite-py

Django + Django REST Framework backend for Auctionite.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- [Task](https://taskfile.dev/) (optional — every task is just a `uv run ...` command)

## Setup

```sh
uv sync
uv run python manage.py migrate
```

## Development

```sh
task run        # ./manage.py runserver
task lint       # ruff check
task format     # ruff format + import sorting
task typecheck  # pyrefly
task check      # lint + typecheck
```

## Layout

- `config/` — settings, urls, wsgi/asgi
- `src` — Django apps
