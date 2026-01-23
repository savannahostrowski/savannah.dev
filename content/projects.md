---
title: Projects
hidemeta: true
---

A collection of open source projects I've built.

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

---

## debugwand

A zero-preparation remote debugger for Python applications running in Kubernetes clusters or Docker containers. With `debugwand`, there's no sidecar pod, no application code changes, and virtually no setup required.

[GitHub](https://github.com/savannahostrowski/debugwand) ・ [PyPI](https://pypi.org/project/debugwand/)

---

## doesjitgobrrr

A (unofficial) dashboard to track CPython's JIT performance compared to the standard interpreter over time. This project is both a UI and all of the benchmarking infrastructure that powers it. I maintain a mini server farm of 4 separate runners across different platforms and architectures in my home lab to collect the data nightly.

[GitHub](https://github.com/savannahostrowski/doesjitgobrrr) ・ [Dashboard](https://doesjitgobrrr.com)