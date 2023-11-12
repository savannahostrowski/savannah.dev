# Savannah's Personal Site
This is my personal website, written in Go using Hugo via the [Terminal theme](https://github.com/panr/hugo-theme-terminal).

![](assets/site.png)

## Provision and Deploy
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/savannahostrowski/terminal-personal-site?devcontainer_path=.devcontainer/devcontainer.json)
1. Open in Codespace/Dev Container
1. Run `azd up`

## Local Development
1. Run `hugo server`
1. Visit `localhost:1313` for changes

## Customization
2. Update or remove the backlink to Mastodon in `src/themes/hugo-theme-terminal/layouts/_default/single.html` on line 5. I wanted my website link to be verified :)
3. Run `azd deploy` to deploy the new code up to your already provisioned infrastructure (done via `azd up`)