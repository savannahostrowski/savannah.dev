---
title: Projects
hidemeta: true
---

A collection of open source projects I've built.

## doesjitgobrrr

A (unofficial) dashboard to track CPython's JIT performance compared to the standard interpreter over time. This project is both a UI and all of the benchmarking infrastructure that powers it. I maintain a mini server farm of 4 separate runners across different platforms and architectures in my home lab to collect the data nightly.

[Dashboard](https://doesjitgobrrr.com) ・ [GitHub](https://github.com/savannahostrowski/doesjitgobrrr)

---

## coredispatch.xyz

A regular digest of what's happening in Python core development — from merged PRs and PEP decisions to community discussions and upcoming events. Core Dispatch aggregates information from GitHub, official and personal blogs of core developers, iCals for releases and events, and more to keep you in the loop.

[Subscribe](https://coredispatch.xyz) ・ [GitHub](https://github.com/savannahostrowski/coredispatch.xyz)

---

## debugwand

A zero-preparation remote debugger for Python applications running in Kubernetes clusters or Docker containers. With `debugwand`, there's no sidecar pod, no application code changes, and virtually no setup required.

[GitHub](https://github.com/savannahostrowski/debugwand) ・ [PyPI](https://pypi.org/project/debugwand/)

---

## pyrepl-web

An embeddable Python REPL powered by Pyodide. Add Python to your website with just a few lines of HTML (supports pre-loading packages + theming)! No installation required.

[GitHub](https://github.com/savannahostrowski/pyrepl-web) ・ [npm](https://www.npmjs.com/package/pyrepl-web)

{{< pyrepl >}}

---

## gruyere

A tiny (and pretty) program for viewing + killing listening ports on your machine.

[GitHub](https://github.com/savannahostrowski/gruyere) ・ [PyPI](https://pypi.org/project/gruyere/)

---

## every-python

A utility to build any commit of CPython, using smart caching. Build any commit of CPython (branch, tag, commit hash) with just one command. Supports building with the JIT enabled by auto-detecting the version of LLVM required.

[GitHub](https://github.com/savannahostrowski/every-python) ・ [PyPI](https://pypi.org/project/every-python/)

