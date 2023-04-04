# Savannah's Personal Site
This is my personal website, written in Go using Hugo via the [Terminal theme](https://github.com/panr/hugo-theme-terminal). This site is compatible with [the Azure Developer CLI (`azd`)](https://github.com/azure/azure-dev) such that it can have its infrastructure provisioned and its code deployed in a single step via `azd up` (hosted on Azure Container Apps).

![](assets/site.png)

## Provision and Deploy
If you want to give it a shot:
1. Install [the Azure Developer CLI](https://aka.ms/azd) and its dependencies
2. Install [Go](https://go.dev/doc/install) and [Hugo](https://gohugo.io/installation/)
3. Run the following command to initialize the project.

```bash
azd init --template savannahostrowski/terminal-personal-site
```

This command will clone the code to your current folder and prompt you for the following information:

- `Environment Name`: This will be used as a prefix for the resource group that will be created to hold all Azure resources. This name should be unique within your Azure subscription.

4. Run the following command to build a deployable copy of your application, provision the template's infrastructure to Azure and also deploy the applciation code to those newly provisioned resources.

```bash
azd up
```

This command will prompt you for the following information:
- `Azure Location`: The Azure location where your resources will be deployed.
- `Azure Subscription`: The Azure Subscription where your resources will be deployed.

> NOTE: This may take a while to complete as it executes three commands: `azd package` (builds a deployable copy of your application), `azd provision` (provisions Azure resources), and `azd deploy` (deploys application code). You will see a progress indicator as it packages, provisions and deploys your application.

5. Watch magic happen.

## Local Development
1. Navigate into the `src/` directory and run `hugo server -t hugo-theme-terminal`
2. Visit `localhost:1313` for changes


## Customization
1. Edit the files in `src/content` to make it your own
2. Update or remove the backlink to Mastodon in `src/themes/hugo-theme-terminal/layouts/_default/single.html` on line 5. I wanted my website link to be verified :)
3. Run `azd deploy` to deploy the new code up to your already provisioned infrastructure (done via `azd up`)

For further stylistic changes, you can check out [this config.toml](https://github.com/panr/hugo-theme-terminal#how-to-configure) from the theme's creator.
