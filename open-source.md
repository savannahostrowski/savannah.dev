---
title: OSS Backlog
hidemeta: true
---

This is just a laundry list of things I want to do related to open source.

- Blog post ideas
    - [ ] Why a JIT and not AOT in CPython?
    - [ ] What we're going to do with freethreading and the JIT
    - [ ] Why is the JIT not universally faster yet?
    - [ ] Working on the standard library - testing, performance, backwards compatibility, etc.
    - [ ] How to contribute to CPython
    - [ ] How does bytecode optimization work in CPython?
    - [ ] I'm the next release manager for CPython
- CPython
    - JIT
        - [ ] Use pure op machinery to add `_POP_TWO_LOAD_CONST_INLINE_BORROW` and `_POP_TOP_LOAD_CONST_INLINE_BORROW` optimizations to various bytecode instructions
        - [ ] Upgrade the JIT to use LLVM 20
        - [ ] Consider exposing `--output-dir` in `configure` so that folks can point to pre-generated stencils (see https://discuss.python.org/t/building-the-jit-with-pre-built-stencils/91838/9)
        - [ ] Finish stencil diffing tool (use PEP 774 reference implementation)
    - argparse
        - [ ] Audit docs for argparse again - try to figure out how to make them more easily parseable
        - [ ] Mutually necessary arguments? Is this even required anymore?
        - [ ] Run coverage on argparse tests again
        - [ ] Performance test argparse
    - Miscellaneous
        - [ ] https://github.com/python/cpython/issues/100964
