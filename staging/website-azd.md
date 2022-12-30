+++
title = "This website can have its cloud infrastructure provisioned and code deployed in one step, in minutes"
+++

# A personal website, how original!
These days it seems like everyone has a personal website, even if it just aggregates a bunch of social media links. I decided to make a new website because 1) I'm learning Go and wanted to play around with Hugo and 2) I wanted a verified personal website link on my Mastodon profile (I'm slowly migrating my Internet presence from Twitter over to Mastodon in what can only be described as "unprecedented times").

In this post, I won't dive too deep into Go or specifics around Hugo because this site is very basic and I'm still very green in this space. Instead, I want to document how I set up this website to have its cloud infrastructure provisioned and its code deployed in one step, in minutes on Azure.

# A brief introduction about this site's codebase
I've spent a lot of time writing Python and JavaScript but I've been itching to learn another language so I recently decided to give Go a try. So far, I like it so naturally when I decided to build a new website, I wanted to play with Hugo.

If you're unfamiliar, Hugo is a static-site generator framework for Go. Because it's all open source, there is also a lovely set of community-built themes (in fact, my site leverages a super cool theme called [Terminal](https://github.com/panr/hugo-theme-terminal)). 

My initial impression of Hugo is that it's pretty powerful with quite a bit of magic going on under the hood. Figuring out how to get the menu set up and get content appearing took more time than expected. Where I ran into a bit of trouble was with the content management bits, specifically around [page bundles](https://gohugo.io/content-management/page-bundles/) and how to get Markdown rendered using specific templates included in the theme. Perhaps in the future, I'll document some of my learnings with Hugo.

> You can find the codebase for this website [here](https://github.com/savannahostrowski/terminal-personal-site). This is what we'll be talking through for the remainder of this post.

![](static/img/this-site.png)

# Making going code to cloud **easier**

The reality is that for many application developers it's easy enough to conceptualize that you need components like a frontend, backend and database to  build a basic web application. It might even be easy to choose which libraries and frameworks to use. However, when it comes to figuring out how to get the application up and running in the cloud that's where things get challenging. Those frontend/backend/database components don't necessarily map 1:1 with cloud services. Alongside that, wiring services together, configuring services, setting up roles and permissions, setting up your local development environment to work with the clould all add complexity to your application and development workflow. All the questions you need to work through to get your application up and running in the cloud steal time away from application development and ultimately, hinder your productivity.

This is where tooling like the [Azure Developer CLI](https://github.com/azure/azure-dev) or `azd` can help make it easier for you to get up and running in the cloud. 

Where you might be familiar with CLIs that scaffold your application or spit out Infrastructure as Code assets, the Azure Developer CLI does both of those things and more. By exposing higher-level commands that map to your development workflow (think `provision`, `deploy`, `pipeline config`), the CLI aims to obfuscate away some of the cloud nitty gritty so that you can focus on building your application. So instead of it taking you hours researching, tearing through docs, clicking around in a website to try and figure out how to do things in the cloud **the right way**, the Azure Developer CLI does the heavy lifting (and IMO, it rules!).

# Making this site `azd` compatible: A step-by-step guide
So once I had my website working locally the next step was to move it on up to the cloud so that I could make it **real**.

## **Step 1: Find a template with similar architecture**
That said, I popped over to the [Awesome Azd template gallery site](https://aka.ms/awesome-azd) which acts as an aggregator site to host metadata about all of the Azure Developer CLI templates (community built and Microsoft authored) to make it easy to discover the right template for your application. 

> The Azure Developer CLI relies on these very extensible and customizable application templates to give you everything you need to get up and running in the cloud. The idea here is to find a template with a similar architecture to your application, modify the template to make it work for you (more details on this in a second) and then run `azd up` or `azd provision` and `azd deploy` to get the infrastructure created and the code deployed.

I wanted to run my website in a container so I opted to find a template that hosted an application on Azure Container Apps, like this [todo-python-mongo-aca](https://github.com/Azure-Samples/todo-python-mongo-aca) template. At first glance you might read the README or look at the architecture and think "wow, this has a lot more going on in it than I need for my basic personal website" and you're right! The beauty here is that I can really customize this template for my use case by removing a bunch of stuff and reorganizing it and then piggyback off of someone else's hard work to figure out all of the Infrastructure as Code bits.

## **Step 2: Run `azd init -t Azure-Samples/todo-python-mongo-aca` on the repo**
So, in the root directory of my application on my local machine, I ran `azd init -t Azure-Samples/todo-python-mongo-aca` and provided details about my environment name (you can name your environment whatever you'd like), subscription and region.

This command initialized my personal website codebase with this `todo-python-mongo-aca` template and a bunch of files were popped into my project (I opted to not let the CLI override any files in my project). Then it was on to customization.


**Step 3: Delete directories and files I not needed**
 So let's talk about what I did here to get something minimal working end-to-end. First, I removed a lot of files (knowing full well that I can add them back at anytime):
- `.azdo/pipelines`: I don't need or want to set up a CI/CD pipeline with Azure DevOps for this application
- `.devcontainer`: Maybe I'll add it back in the future but for right now, I wanted to keep it simple and I'm not currently using a [Dev Container](https://code.visualstudio.com/docs/devcontainers/containers) or Codespaces for my dev environment.
- `.github/`: I'll likely add this back soon as I'll want to have CI/CD running on my codebase against real Azure resource and possibly automate publishing my blogs to dev.to via GitHub Actions
- `.vscode/`: I'm just manually running the frontend via `hugo server -t hugo-theme-terminal` inside my `src/` but in the future I could wire this up
- `tests/`: Because we test in prod...jk, that's a bad joke but this site is really minimal so I'm going to defer dealing with testing for now.
- `.gitattributes`, `LICENSE`, `NOTICE.txt`, : Stuff not needed for my project
- `openapi.yaml`: No backend here

So the resulting file structure looked like:
```
.
├── assets/
├── infra/
├── src/
├── .gitignore
├── README.md
├── azure.yaml
```

## **Step 4: Modify the `azure.yaml`.

Then I modified the `azure.yaml`. This file defines and describes the applications and types of Azure resources that comprise the template ([docs](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/azd-schema)). This file is integral to letting the Azure Developer CLI know that this project is compatible. Here's what I did:
- I changed the `name` and `metadata.name` to better reflect my project (`terminal-personal-site`)
- I removed the `services.api` as we have no backend in this application
- I changed the `services.web.project` to `./src` to point at my code
- I removed the `services.web.language` because `go` isn't valid in the `azure.yaml` schema

So the resulting `azure.yaml` looked like:
```yaml
name: terminal-personal-site-hugo
metadata:
  template: terminal-personal-site-hugo@0.0.1-beta
services:
  web:
    project: ./src
    module: app/web
    host: containerapp
```

Note that I moved all my application code into the `src/` directory but you can have your code laid out however you'd like so long as you point `services.web.project` to the source code directory (this is important so that the CLI knows what code needs to be deployed).

**Step 5: Understand how the Infrastructure as Code files architected**
This is where things get interesting! As an application developer, you might not be familiar with Infrastructure as Code (IaC) but it's really awesome.

>  Infrastructure as Code is a way that you can manage and provision your cloud infrastructure and services via code. The files in the `infra/` directory within an Azure Developer CLI template/compatible project specify the services you want to create, their configurations and how they interact. Using Infrastructure as Code, we can ensure that environment is generated in the same way each time everything is deployed to the cloud. Infrastructure as Code also means that instead of you or your team needing to manage or maintain environment settings individually, you can work off the same well-documented code that represents the desired environment state, avoiding deployment issues by keeping everything consistent.

With the template ecosystem, you don’t necessarily learn about Infrastructure as Code on day 1 of learning about the cloud but these files are an important part of any Azure Developer CLI template. I think the nicest part of working with an Azure Developer CLI template is that you can always start with the files included in the template and then dig into the cloud specifics slowly when or if your application requirements change.

Okay, that said, let's take a look at what's in here:
```
.
├── assets/
├── infra/
│   ├──  app/
│   │   └── api.bicep
│   │   └── web.bicep
│   │   └── db.bicep
│   │   └── ...
│   └── core
│       └── database/
│       └── host/
│       └── monitor/
│       └── security/
│       └── storage/
│   ├──  abbreviations.json
│   ├──  main.bicep
│   ├──  main.parameters.json
│   ├──  resources.bicep
```

Let's talk about what we're looking at:
- `main.bicep` - serves as an entry point for all of the Infrastructure as Code
- `main.parameters.json` - specifies parameters required by the `main.bicep` file like environment name, location, principal ID and image name.
- `resources.bicep` - Inside here, you'll see a bunch of references to modules. This file is called from the `main.bicep`.
- `abbreviations.json` - abbreviations used for constructing service names
- `app/` - contains infrastructure as code organized by application component, called from within `main.bicep`
- `core/` - contains lower-level building block infrastructure as code; some of these files are used for this template but some are included as a reference library

As I mentioned before, this `todo-python-mongo-aca` template is actually quite a bit more complicated than this website I built so up next was to remove a bunch of IaC files that weren't needed for my application.


**Step 6: Remove a bunch of IaC not needed for my website**
I approached figuring out what _was_ needed by checking out the architecture diagram and sort of code navigating through the files in the `infra/` directory. I am also a newbie to the language these files are written in, Bicep, so this was the easiest way for me to understand what was going on.

So, here I started from the higher-level components and then worked my way down the call stack. Here's what I did:
1. I don't have a backend or database in this application so I removed the `api.bicep` and `db.bicep` inside `app/`.
1. From here, I knew that I wasn't going to need anything in `core/database` or anything not related to Azure Container Apps so I also removed everything in `host/` except for `container-app.bicep`, `container-apps-environment.bicep`, `container-apps.bicep` and `container-registry.bicep`. 
1. Then, I also removed the `core/monitor` for now as I'm not looking for application monitoring for this basic site (in the future, I might try to set up Grafana for this).
1. I left the `core/security` because Key Vault is needed for storing application secrets and the container image name once it's up in the Azure Container Registry (which IaC + `azd` will handle for us). 

So here's what I was left with:

```
.
├── assets/
├── infra/
│   ├──  app/
│   │   └── web.bicep
│   │   └── web.parameters.json
│   └── core
│       └── host/
│       └── security/
│   ├──  abbreviations.json
│   ├──  main.bicep
│   ├──  main.parameters.json
│   ├──  resources.bicep
```

So now it's time to talk about how the code is built and deployed!

**Step 7: Write a `Dockerfile`**
Next, I needed to write a `Dockerfile` so that we could run the application in a container. to I used a minimal Docker image for Hugo - [klakegg/hugo](https://hub.docker.com/r/klakegg/hugo/). This image also starts a web server via `nginx`. Inside of my `src/` directory, I created a `Dockerfile` with the following:

```docker
FROM klakegg/hugo:0.101.0-onbuild AS hugo

FROM nginx
COPY --from=hugo /target /usr/share/nginx/html
```

This `Dockerfile` will be used as part of the next step to build the container image, pop it into Azure Container Registry and use it for my Azure Container App. The port set in `infra/app/web.bicep` was already [set to `80`](https://github.com/Azure-Samples/todo-python-mongo-aca/blob/9387cc4a60ef40ac1593fda079f74b2e88f10896/infra/app/web.bicep#L37) so we didn't even need to update the target port to make this work.

**Step 8: Create cloud infrastructure and deploy application code in a single step, in minutes**
Finally, it was time to run `azd up` inside of the root directory of my application. This command initializes the project, provisions infrastructure and deploys the application on Azure in a single step (via running `azd init`, `azd provision` and `azd deploy` under the hood)

Because I already ran `azd init` to pull the template code down into my project, `azd up` no-ops on that command and just wraps provisioning and deployment into a single step!

After running this, you'll see each resource created for you with unique identifiers that you can reference in the Azure Portal (if you need) and then a URL where your application is up and running! 


