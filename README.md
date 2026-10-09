# savannah.dev

My personal site — blog, about, work, talks. Built with FastAPI, deployed on FastAPI Cloud.

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
- **Python proposals**: edit `content/peps.yml`; these appear on the Work page with their authorship, status, and summary.
- **Talks**: add entries to `content/talks.yml` in the order they should appear. Each has a `title`, `event`, `year`, and YouTube `youtube_id` (the value after `v=` in the video URL). `kind`, `summary`, and `slides_url` are optional.
- **About**: edit `content/about.md`.

## Lint & typecheck

```
uv run ruff check .
uv run ruff format .
uv run ty check
```
