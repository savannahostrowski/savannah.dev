# Savannah's Personal Site
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/savannahostrowski/terminal-personal-site?devcontainer_path=.devcontainer/devcontainer.json)

This is my personal website, written in Go using Hugo via the [Terminal theme](https://github.com/panr/hugo-theme-terminal).

## Local Development
1. Run `hugo server` in `src/`
1. Visit `localhost:1313` for changes

## Deployment
1. Run `hugo` in `src/` to build static assets.
1. Deployment is handled via the GitHub Action pipeline (via `azd`)
