# savannah.dev

My personal site — blog, about, projects. Built with FastAPI, deployed on FastAPI Cloud.

## Local development

```
uv run fastapi dev main.py
```

Or via Docker (hot-reload):

```
docker compose -f docker-compose.dev.yml up --build
```

## Deploy

Push to `main` — GitHub Actions runs `fastapi deploy` against FastAPI Cloud. See `.github/workflows/fastapicloud-deploy.yml`.

Manual deploy:

```
uv run fastapi deploy
```

## Adding content

- **Posts**: drop a directory under `content/posts/<slug>/` with an `index.md` (frontmatter: `title`, `date`, `summary`, `tags`). Images go in `images/` next to it.
- **Projects**: append to `content/projects.yml`.
- **About**: edit `content/about.md`.

## Lint & typecheck

```
uv run ruff check .
uv run ruff format .
uv run ty check
```
