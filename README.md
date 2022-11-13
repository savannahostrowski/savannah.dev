# Savannah's Personal Site
This site is written in Go using Hugo, via the [Terminal theme](https://github.com/panr/hugo-theme-terminal). This site is also compatible with [the Azure Developer CLI (`azd`)](https://github.com/azure/azure-dev) such that it can have it's infrastructure provisioned and the site's code deployed in a single step via `azd up` (hosted on Azure Container Apps).

![](assets/site.png)

## Provision and Deploy
If you want to give it a shot:
1. Install [the Azure Developer CLI](https://aka.ms/azd) and its dependencies
1. Run `azd up -t savannahostrowski/terminal-personal-site`
1. Pass in an environment name, Azure subscription and region
1. Watch magic happen.

## Local Development
1. Navigate into the `src/` directory and run `hugo server -t hugo-theme-terminal`


## Customization
You will want to update or remove the backlink to Mastodon in `src/themes/hugo-theme-terminal/layouts/_default/single.html` on line 5. I wanted my website link to be verified :)

If you're interested in making your own, easy-to-deploy site using this template, you can check out the [this config.toml](https://github.com/panr/hugo-theme-terminal#how-to-configure)