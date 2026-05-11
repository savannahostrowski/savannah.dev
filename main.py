from __future__ import annotations

import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import frontmatter
import markdown
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from jinja2 import BaseLoader, Environment, FileSystemLoader
from starlette.exceptions import HTTPException as StarletteHTTPException

# ---------------------------------------------------------------------------
# Site constants (used in <head> meta and canonical URLs)
# ---------------------------------------------------------------------------

SITE_URL = "https://savannah.dev"
SITE_NAME = "Savannah Ostrowski"
SITE_DESCRIPTION = (
    "Python Steering Council member, CPython Release Manager (3.16 and 3.17), "
    "Python Core Developer, and Engineer at FastAPI Labs."
)
SITE_OG_IMAGE = "/static/img/social-share.png"

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
POSTS_DIR = CONTENT_DIR / "posts"
STATIC_DIR = BASE_DIR / "static"

# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

_MARKDOWN = markdown.Markdown(extensions=["extra", "codehilite", "toc"])


def render_markdown(source: str) -> str:
    """Convert markdown source to HTML."""
    _MARKDOWN.reset()
    return _MARKDOWN.convert(source)


def slugify(value: str) -> str:
    """Lowercase, ASCII-ish, hyphenated. Matches Hugo's default for tag URLs."""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


# ---------------------------------------------------------------------------
# Post model
# ---------------------------------------------------------------------------


class Post:
    """A blog post loaded from an index.md file."""

    def __init__(self, path: Path, post_dir: Path):
        self.path = path
        self.post_dir = post_dir
        self.slug = post_dir.stem
        self.metadata: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        post = frontmatter.load(str(self.path))
        self.metadata = dict(post.metadata)
        self.title: str = self.metadata.get("title", self.slug.replace("-", " ").title())
        date_str = self.metadata.get("date", "2000-01-01")
        date = datetime.fromisoformat(date_str)
        self.date: datetime = date if date.tzinfo else date.replace(tzinfo=UTC)
        self.summary: str = self.metadata.get("summary", "")
        self.description: str = self.metadata.get("description", self.summary)
        self.tags: list[str] = list(self.metadata.get("tags", []))
        self.body_html: str = render_markdown(str(post))
        self.hide_meta: bool = self.metadata.get("hidemeta", False)

    @property
    def image_dir(self) -> Path:
        return self.post_dir / "images"

    @property
    def tag_pairs(self) -> list[tuple[str, str]]:
        """List of (display_name, slug) tuples."""
        return [(t, slugify(t)) for t in self.tags]


@lru_cache(maxsize=1)
def load_all_posts() -> list[Post]:
    """Load every post from content/posts, newest first. Cached for the app lifetime."""
    posts: list[Post] = []
    if not POSTS_DIR.exists():
        return posts
    for post_dir in POSTS_DIR.iterdir():
        if not post_dir.is_dir():
            continue
        index_md = post_dir / "index.md"
        if index_md.exists():
            posts.append(Post(index_md, post_dir))
    posts.sort(key=lambda p: p.date.replace(tzinfo=None) if p.date.tzinfo else p.date, reverse=True)
    return posts


@lru_cache(maxsize=1)
def load_static_pages() -> dict[str, Post]:
    """Load top-level content/*.md files as static pages."""
    pages: dict[str, Post] = {}
    if not CONTENT_DIR.exists():
        return pages
    for md_file in CONTENT_DIR.glob("*.md"):
        if md_file.name == "index.md":
            continue
        stem = md_file.stem
        post = Post(md_file, md_file.parent)
        post.slug = stem
        pages[stem] = post
    return pages


@lru_cache(maxsize=1)
def load_tag_map() -> dict[str, tuple[str, list[Post]]]:
    """Map tag-slug -> (canonical display name, posts). First-seen casing wins."""
    out: dict[str, tuple[str, list[Post]]] = {}
    for post in load_all_posts():
        for display, slug in post.tag_pairs:
            if slug not in out:
                out[slug] = (display, [])
            out[slug][1].append(post)
    return out


@lru_cache(maxsize=1)
def load_projects() -> list[dict[str, Any]]:
    projects_file = CONTENT_DIR / "projects.yml"
    if not projects_file.exists():
        return []
    return yaml.safe_load(projects_file.read_text()) or []


# ---------------------------------------------------------------------------
# Jinja2 environment
# ---------------------------------------------------------------------------


def _get_jinja_env() -> Environment:
    templates_dir = STATIC_DIR / "templates"
    env = Environment(
        loader=FileSystemLoader(templates_dir) if templates_dir.exists() else BaseLoader(),
        autoescape=True,
    )
    g: dict[str, Any] = env.globals  # type: ignore[assignment]
    g["current_year"] = datetime.now().year
    g["site_url"] = SITE_URL
    g["site_name"] = SITE_NAME
    g["site_description"] = SITE_DESCRIPTION
    g["site_og_image"] = SITE_OG_IMAGE
    g["slugify"] = slugify
    return env


def render(
    template_name: str,
    *,
    page_path: str,
    page_title: str,
    page_description: str | None = None,
    page_image: str | None = None,
    **context: Any,
) -> HTMLResponse:
    env = _get_jinja_env()
    template = env.get_template(template_name)
    html = template.render(
        site_title=page_title,
        page_url=SITE_URL + page_path,
        page_description=page_description or SITE_DESCRIPTION,
        page_image=SITE_URL + (page_image or SITE_OG_IMAGE),
        **context,
    )
    return HTMLResponse(html)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

TALKS_DIR = BASE_DIR / "talks"


@app.get("/talks/{talk}/")
async def talk_index(talk: str):
    index = TALKS_DIR / talk / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(index)


@app.get("/talks/{talk}/{path:path}")
async def talk_asset(talk: str, path: str):
    talk_dir = TALKS_DIR / talk
    if not talk_dir.is_dir():
        raise HTTPException(status_code=404)
    requested = (talk_dir / path).resolve()
    # Guard against path traversal
    if not str(requested).startswith(str(talk_dir.resolve())):
        raise HTTPException(status_code=404)
    if requested.is_file():
        return FileResponse(requested)
    # SPA fallback: deep links like /talks/remote-debug/1 get the slide app's index.html
    index = talk_dir / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        env = _get_jinja_env()
        template = env.get_template("404.html")
        html = template.render(
            site_title="Page not found",
            page_url=SITE_URL + str(request.url.path),
            page_description=SITE_DESCRIPTION,
            page_image=SITE_URL + SITE_OG_IMAGE,
        )
        return HTMLResponse(html, status_code=404)
    return Response(content=exc.detail or "", status_code=exc.status_code)


@app.get("/")
async def index():
    posts = load_all_posts()
    return render(
        "index.html",
        page_path="/",
        page_title="Savannah's Blog",
        posts=posts,
    )


@app.get("/posts/{slug}/")
async def post_page(slug: str):
    posts = load_all_posts()
    for i, post in enumerate(posts):
        if post.slug == slug:
            newer = posts[i - 1] if i > 0 else None
            older = posts[i + 1] if i + 1 < len(posts) else None
            return render(
                "post.html",
                page_path=f"/posts/{slug}/",
                page_title=post.title,
                page_description=post.description or post.summary or SITE_DESCRIPTION,
                post=post,
                newer=newer,
                older=older,
            )
    raise HTTPException(status_code=404)


@app.get("/posts/{slug}/images/{filename:path}")
async def post_image(slug: str, filename: str):
    posts = load_all_posts()
    for post in posts:
        if post.slug == slug:
            image_path = post.image_dir / filename
            if image_path.is_file():
                return FileResponse(image_path)
            raise HTTPException(status_code=404)
    raise HTTPException(status_code=404)


@app.get("/tags/{tag_slug}/")
async def tag_page(tag_slug: str):
    tag_map = load_tag_map()
    if tag_slug not in tag_map:
        raise HTTPException(status_code=404)
    display, tagged = tag_map[tag_slug]
    return render(
        "tag.html",
        page_path=f"/tags/{tag_slug}/",
        page_title=f"Posts tagged: {display}",
        page_description=f"Posts tagged with {display} on {SITE_NAME}'s blog.",
        tag=display,
        tag_slug=tag_slug,
        posts=tagged,
    )


@app.get("/tags/{tag_slug}/index.xml")
async def tag_feed(tag_slug: str):
    tag_map = load_tag_map()
    if tag_slug not in tag_map:
        raise HTTPException(status_code=404)
    display, tagged = tag_map[tag_slug]
    env = _get_jinja_env()
    template = env.get_template("feed.xml.j2")
    body = template.render(
        posts=tagged,
        site_title=f"{SITE_NAME} — posts tagged {display}",
        feed_path=f"/tags/{tag_slug}/index.xml",
    )
    return Response(content=body, media_type="application/rss+xml")


@app.get("/index.xml")
async def feed():
    posts = load_all_posts()
    env = _get_jinja_env()
    template = env.get_template("feed.xml.j2")
    body = template.render(posts=posts, site_title="Savannah's Blog")
    return Response(content=body, media_type="application/rss+xml")


@app.get("/sitemap.xml")
async def sitemap():
    posts = load_all_posts()
    tag_map = load_tag_map()
    env = _get_jinja_env()
    template = env.get_template("sitemap.xml.j2")
    body = template.render(posts=posts, tag_slugs=sorted(tag_map.keys()))
    return Response(content=body, media_type="application/xml")


@app.get("/about/")
async def about():
    pages = load_static_pages()
    if "about" not in pages:
        raise HTTPException(status_code=404)
    post = pages["about"]
    return render(
        "post.html",
        page_path="/about/",
        page_title=post.title,
        page_description=post.description or SITE_DESCRIPTION,
        post=post,
        newer=None,
        older=None,
    )


@app.get("/projects/")
async def projects():
    return render(
        "projects.html",
        page_path="/projects/",
        page_title="Projects",
        page_description="Open source projects by Savannah Ostrowski.",
        projects=load_projects(),
    )


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(STATIC_DIR / "favicon.ico")


@app.get("/robots.txt")
async def robots():
    return FileResponse(STATIC_DIR / "robots.txt", media_type="text/plain")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
