---
title: "How JIT builds of CPython actually work"
date: "2025-07-27"
summary: "You don't have to be a compiler engineer to understand how your code runs in a JIT build of CPython"
description: "You don't have to be a compiler engineer to understand how your code runs in a JIT build of CPython"
tags: ["Python", "JIT", "CPython", "You don't have to be a compiler engineer"]
---

>  This is a post in a series around making CPython internals more approachable. If I missed something or you’d like to request a topic, feel free to drop me a line via [email](mailto:savannah@python.org). You can also read other posts in the series [here](https://savannah.dev/tags/you-dont-have-to-be-a-compiler-engineer/).

Ever wonder what really happens under the hood when you run your Python code? If you're using a JIT build of CPython, the answer may involve a few more steps than you'd expect but thankfully, you don't have to be a compiler engineer to understand it. 

Before I get into it, I want to shamelessly plug that you can help us test JIT builds of CPython pretty easily as of Python 3.14! You can now get official Python builds from [python.org](https://www.python.org/downloads/) for both Windows and macOS that include [CPython’s experimental just-in-time (JIT) compiler built in but off by default](https://docs.python.org/3.14/whatsnew/3.14.html#binary-releases-for-the-experimental-just-in-time-compiler). While the JIT builds are not (yet) recommended for production use, you can enable the JIT using the `PYTHON_JIT=1` environment variable. We’d love to hear about your experience using Python with the JIT - the good, the bad, the ugly!

Alright, let's get after it.

## What happens when you execute your code: A brief overview of CPython’s interpreter

...Well, before we get into what happens in a JIT build of Python, we should probably briefly talk about what happens in a "regular" build for anyone that isn't familiar with how the interpreter works, as this lays the foundation for the JIT builds later on. I think the best way to talk about this is by example. To cover this, let’s consider this very basic function:

```python
def abs(a: int, b: int) -> int:
    if a > b:
        return a - b
    return b - a
```
So, let's say you execute this with your local version of Python and boom, the code is running. But what actually happens here?

### First, your code is broken down into tokens

When you run this code, the first thing that happens is that Python breaks it down into tokens. Tokens are the smallest units of meaning in your code, like keywords, identifiers, literals, and operators. For example, in our function, `def`, `abs`, `(`, `a`, `b`, `if`, `>`, `return`, and so on are all tokens. This process is known as lexical analysis or tokenization.
You can see what the tokens for our function look like using the `tokenize` module in the standard library. Here’s how you can do that:

```python
import tokenize
from io import BytesIO
source = b"""
def abs(a: int, b: int) -> int:
    if a > b:
        return a - b
    return b - a
"""
tokens = tokenize.tokenize(BytesIO(source).readline)
for token in tokens:
    print(token)
```

This will output a list of tokens that look something like this:

```plaintext
TokenInfo(type=65 (ENCODING), string='utf-8', start=(0, 0), end=(0, 0), line='')
TokenInfo(type=63 (NL), string='\n', start=(1, 0), end=(1, 1), line='\n')
TokenInfo(type=1 (NAME), string='def', start=(2, 0), end=(2, 3), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=1 (NAME), string='abs', start=(2, 4), end=(2, 7), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=55 (OP), string='(', start=(2, 7), end=(2, 8), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=1 (NAME), string='a', start=(2, 8), end=(2, 9), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=55 (OP), string=':', start=(2, 9), end=(2, 10), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=1 (NAME), string='int', start=(2, 11), end=(2, 14), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=55 (OP), string=',', start=(2, 14), end=(2, 15), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=1 (NAME), string='b', start=(2, 16), end=(2, 17), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=55 (OP), string=':', start=(2, 17), end=(2, 18), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=1 (NAME), string='int', start=(2, 19), end=(2, 22), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=55 (OP), string=')', start=(2, 22), end=(2, 23), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=55 (OP), string='->', start=(2, 24), end=(2, 26), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=1 (NAME), string='int', start=(2, 27), end=(2, 30), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=55 (OP), string=':', start=(2, 30), end=(2, 31), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=4 (NEWLINE), string='\n', start=(2, 31), end=(2, 32), line='def abs(a: int, b: int) -> int:\n')
TokenInfo(type=5 (INDENT), string='    ', start=(3, 0), end=(3, 4), line='    if a > b:\n')
TokenInfo(type=1 (NAME), string='if', start=(3, 4), end=(3, 6), line='    if a > b:\n')
TokenInfo(type=1 (NAME), string='a', start=(3, 7), end=(3, 8), line='    if a > b:\n')
TokenInfo(type=55 (OP), string='>', start=(3, 9), end=(3, 10), line='    if a > b:\n')
TokenInfo(type=1 (NAME), string='b', start=(3, 11), end=(3, 12), line='    if a > b:\n')
TokenInfo(type=55 (OP), string=':', start=(3, 12), end=(3, 13), line='    if a > b:\n')
TokenInfo(type=4 (NEWLINE), string='\n', start=(3, 13), end=(3, 14), line='    if a > b:\n')
TokenInfo(type=5 (INDENT), string='        ', start=(4, 0), end=(4, 8), line='        return a - b\n')
TokenInfo(type=1 (NAME), string='return', start=(4, 8), end=(4, 14), line='        return a - b\n')
TokenInfo(type=1 (NAME), string='a', start=(4, 15), end=(4, 16), line='        return a - b\n')
TokenInfo(type=55 (OP), string='-', start=(4, 17), end=(4, 18), line='        return a - b\n')
TokenInfo(type=1 (NAME), string='b', start=(4, 19), end=(4, 20), line='        return a - b\n')
TokenInfo(type=4 (NEWLINE), string='\n', start=(4, 20), end=(4, 21), line='        return a - b\n')
TokenInfo(type=6 (DEDENT), string='', start=(5, 4), end=(5, 4), line='    return b - a\n')
TokenInfo(type=1 (NAME), string='return', start=(5, 4), end=(5, 10), line='    return b - a\n')
TokenInfo(type=1 (NAME), string='b', start=(5, 11), end=(5, 12), line='    return b - a\n')
TokenInfo(type=55 (OP), string='-', start=(5, 13), end=(5, 14), line='    return b - a\n')
TokenInfo(type=1 (NAME), string='a', start=(5, 15), end=(5, 16), line='    return b - a\n')
TokenInfo(type=4 (NEWLINE), string='\n', start=(5, 16), end=(5, 17), line='    return b - a\n')
TokenInfo(type=6 (DEDENT), string='', start=(6, 0), end=(6, 0), line='')
TokenInfo(type=0 (ENDMARKER), string='', start=(6, 0), end=(6, 0), line='')
```

Yeah, that's...a lot but don't worry, you don't have to memorize it or anything. The key takeaway here is that Python has broken down your code into its smallest meaningful parts, which will be used in the next steps of execution.

### Next, your code is parsed

Next, these tokens are combined to form a structure called an abstract syntax tree (AST), which is a tree-based representation of the structure of your code. The AST captures the hierarchical structure of your code, showing how different parts relate to each other. For example, in our function, the AST would show that `abs` is a function definition, `a` and `b` are parameters, and the `if` statement is a conditional that leads to different return statements.

It's also at this stage that Python checks for syntax errors. If there are any, it raises a `SyntaxError` and stops execution.

We can see what our simple function above's AST would look like using the [`ast` module](https://docs.python.org/3/library/ast.html) in the standard library. The code looks something like this:

```python
import ast

source = """
def abs(a: int, b: int) -> int:
    if a > b:
        return a - b
    return b - a

abs(5, 3)
"""

tree = ast.parse(source)
print(ast.dump(tree, indent=4))
```

...and this would return a tree like so:

```plaintext
Module(
    body=[
        FunctionDef(
            name='abs',
            args=arguments(
                args=[
                    arg(
                        arg='a',
                        annotation=Name(id='int')),
                    arg(
                        arg='b',
                        annotation=Name(id='int'))]),
            body=[
                If(
                    test=Compare(
                        left=Name(id='a'),
                        ops=[
                            Gt()],
                        comparators=[
                            Name(id='b')]),
                    body=[
                        Return(
                            value=BinOp(
                                left=Name(id='a'),
                                op=Sub(),
                                right=Name(id='b')))]),
                Return(
                    value=BinOp(
                        left=Name(id='b'),
                        op=Sub(),
                        right=Name(id='a')))],
            returns=Name(id='int')),
        Expr(
            value=Call(
                func=Name(id='abs'),
                args=[
                    Constant(value=5),
                    Constant(value=3)]))])
```

Again, this is a lot of information for such a short function but what you should really glean from this is that every variable, statement, function, constant, etc. along with its relationship is represented in this tree.

### Then, we compile to bytecode

Next, Python compiles that AST down into bytecode, which is really a lower-level, platform-independent representation of your code. This is what the CPython interpreter actually executes. 

Just like with the AST, you can see what the bytecode representation of this function would be. We can see what this would look like for the same function we looked at earlier using the [`dis` module](https://docs.python.org/3/library/dis.html) (aka the disassembly module) in the standard library. 

```python
import dis
def abs(a: int, b: int) -> int:
    if a > b:
        return a - b
    return b - a
dis.dis(abs)
```

```plaintext
  3           RESUME                   0

  4           LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (a, b)
              COMPARE_OP             148 (bool(>))
              POP_JUMP_IF_FALSE        9 (to L1)
              NOT_TAKEN

  5           LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (a, b)
              BINARY_OP               10 (-)
              RETURN_VALUE

  7   L1:     LOAD_FAST_BORROW_LOAD_FAST_BORROW 16 (b, a)
              BINARY_OP               10 (-)
              RETURN_VALUE
```

This might look intimidating, but it's just a lower-level form of your original code. Here's a quick mapping, removing some instructions for brevity:

| Bytecode Instruction                                           | Original Code     | Explanation                                                 |
|---------------------------------------------------------------|-------------------|--------------------------------------------------------------|
| `LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (a, b)`                  | `a > b`           | Load `a` and load `b`                                        |
| `COMPARE_OP 148 (bool(>))`                                    | `a > b`           | Compare `a` and `b` using the `>` operator                   |
| `POP_JUMP_IF_FALSE 9 (to L1)`                                 | `if a > b:`       | Jump to else clause if condition is false                    |
| `LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (a, b)`                  | `return a - b`    | Load `a` and  load `b` again for subtraction                 |
| `BINARY_OP 10 (-)`                                            | `a - b`           | Subtract `b` from `a`                                        |
| `RETURN_VALUE`                                                | `return a - b`    | Return the result of the subtraction                         |
| `LOAD_FAST_BORROW_LOAD_FAST_BORROW 16 (b, a)` (at label `L1`) | `return b - a`    | Load `b` and load `a` for the else clause                    |
| `BINARY_OP 10 (-)`                                            | `b - a`           | Subtract `a` from `b`                                        |
| `RETURN_VALUE`                                                | `return b - a`    | Return the result of the subtraction                         |

This shows how Python breaks your logic into a series of simple instructions. Each instruction is a single operation that the interpreter can execute. For example, `LOAD_FAST_BORROW_LOAD_FAST_BORROW` loads the values of `a` and `b`, `COMPARE_OP` compares them, and `BINARY_OP` performs the subtraction. 

CPython runs your code using a bytecode interpreter. It uses an internal evaluation loop, which executes one bytecode instruction at a time, dispatching to the appropriate C function that handles it. This loop also manages the Python Virtual Machine (PVM), which maintains the call stack, handles memory management, exception handling, and more.

There's more to say here about the Global Interpreter Lock, garbage collection, etc. but I'm going to save that for another post. The key takeaway here is that the PVM executes these bytecode instructions in a loop, processing each instruction in sequence until it reaches the end of the function or encounters a return statement.

For all intents and purposes, your code is now running in the Python interpreter. This is how Python executes your code in a regular build of CPython.

### But, wait, there's more: The Specializing Adaptive Interpreter

Since Python 3.11, we've had something called the [Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/) in CPython (a significant contributor to why
Python 3.11 was about 25% faster than Python 3.10 for most workloads). We won't get into this too deep in this blog post but in essence, the idea here is that once a bytecode instruction has been executed enough times in a code path, the interpreter can "specialize" it based on types and values seen at runtime. 

For example, let’s consider the `BINARY_OP` instruction in our bytecode. If the interpreter sees you're doing a lot of integer subtraction, it might optimize that instruction internally by installing a fast path for integers. This means that while the bytecode still says `BINARY_OP`, the interpreter skips type checks and uses a specialized implementation for integer subtraction behind the scenes, making it significantly faster, even without the JIT compiler.

## Okay, so what happens in JIT builds?

Right, right. Okay, so now that we understand how the interpreter works, we can talk about what happens when you run your code in a JIT build of CPython.

### Enter the micro-instruction (uops) interpreter

So, your code is running in a regular build of CPython is already doing some smart things to optimize your bytecode. But what if we could do even better? What if we could take those bytecode instructions and turn them into something even more efficient? This is where the micro-instruction interpreter comes in.

So once your code has "warmed up" or been executed enough times, we can start to optimize it even further. What's really neat is that the specializing adaptive interpreter actually provides us with a lot of profiling information about the code being executed that helps with all of this. With the micro-op interpreter, we break each bytecode instruction in the code path down into even smaller, more specialized instructions called micro-operations, or uops. These uops are designed to be more efficient and can be executed much faster than the original bytecode instructions. The process of breaking down bytecode instructions into traces happens automatically thanks to some domain-specific language (DSL) infrastructure that was introduced in Python 3.12; it's effectively a table look up to say that this bytecode instruction maps to these uops. Once we have these uops, we can even start to optimize them further by removing unnecessary checks and operations (...again, a topic for another post). 

I'd be remiss if I didn’t mention that the micro-op interpreter is a separate interpreter from the regular bytecode one. In a JIT build of CPython, both interpreters are available, and once a function becomes "hot," execution can switch from bytecode to uops. That might sound like a big performance win, but not quite yet. In fact, things often get slower at this stage. The micro-op interpreter introduces overhead by breaking each bytecode instruction into smaller, more granular uops and dispatching more instructions overall. It’s a trade-off: we’re doing extra work now to prepare for the real speedup that comes next, when the JIT compiler steps in to generate optimized machine code and (hopefully) recover that lost performance and then some.

> When you build Python with `--enable-experimental-jit` or set `PYTHON_JIT=1` in Python 3.14 builds, you're not just enabling the JIT itself, but the micro-op interpreter as well.

### JIT Compilation

Alright, we've finally made it! Let's talk about the JIT.

First off, let's talk about what a JIT compiler is, in case you're not already familiar. A JIT (Just-In-Time) compiler is a type of compiler that translates code into machine code at runtime, rather than before execution. 

In the context of CPython, our JIT compiler uses a technique called copy-and-patch. This technique is covered in [this paper](https://fredrikbk.com/publications/copy-and-patch.pdf) but don't worry, we don't need to get too academic here. Basically, what happens is as follows:

1. When CPython is built, we use LLVM to generate precompiled stencil files for your specific platform and architecture. These stencil files contain templates for how to translate the micro-ops we talked about earlier into machine code.
2. When your code is executed, the JIT compiler monitors the execution and identifies "hot" traces—sections of code that are executed frequently.
3. When a hot trace is detected, the JIT compiler takes the relevant micro-ops, which are the smaller, specialized instructions we covered earlier, and uses the precompiled stencil templates to generate native machine code.
    - The JIT compiler fills in the placeholders in the stencil templates with the actual values needed for your code, such as addresses of variables, constants, and cached results ("patching" up the code).
    - These stencil files are then linked together to form a trace, which is a sequence of micro-ops that can be executed as native machine code.
    - Finally, the JIT compiler executes this native machine code directly instead of interpreting.

> Now, the elephant in the room here is that the JIT does not (yet!) make Python a whole lot faster. In most cases, the JIT builds range from slower to about the same performance as the non-JIT build of Python. As of 3.14, the JIT is faster in select benchmarks but we have a ways to go still. Ken Jin has a great [blog post](https://fidget-spinner.github.io/posts/jit-reflections.html) that goes into more detail about the performance of the JIT builds in Python 3.14 (among other reflections) if you're interested.

## Putting it all together

So, to summarize, when you run your code in a JIT build of CPython, the following happens:
1. Your code is tokenized, parsed, and compiled into bytecode as usual.
2. The bytecode is executed by the regular bytecode interpreter, which may specialize some instructions based on runtime profiling.
3. If the code is executed enough times, the micro-op interpreter kicks in, breaking down the bytecode instructions into smaller, more specialized uops.
4. The JIT compiler then compiles these uops into native machine code using precompiled stencil templates, optimizing the execution of your code.
5. The native machine code is executed directly by the CPU, bypassing the bytecode interpreter and micro-op interpreter.

...and that's it! You now have an understanding of how your code runs in a JIT build of CPython and you didn't have to be a compiler engineer to understand it!

## Suggested readings & videos

Some other great talks, blog posts, etc. by other folks working on Python:
- Maybe watch one of Brandt's talks on this topic: 
    - [Building a JIT compiler for CPython](https://www.youtube.com/watch?v=kMO3Ju0QCDo)
    - [What they don't tell you about building a JIT compiler for CPython](https://www.youtube.com/watch?v=NE-Oq8I3X_w)
- Diego's EuroPython 2025 talk isn't up yet but I will link it as soon as it is available
- ICYMI earlier in the post, Ken Jin's [Reflections on 2 years of CPython’s JIT Compiler: The good, the bad, the ugly](https://fidget-spinner.github.io/posts/jit-reflections.html) is also great if you want to learn more about the JIT builds in Python 3.14 and what it's taken to get to this point.
- Check out [PEP 744](https://www.python.org/dev/peps/pep-0744/), it's really not that scary!

> If you enjoyed this post, please consider sharing it with anyone you think might find it interesting. If you have any questions or feedback, feel free to reach out to me via [email](mailto:savannah@python.org).
