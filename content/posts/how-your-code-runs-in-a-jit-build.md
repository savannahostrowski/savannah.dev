---
title: "JIT Builds of CPython"
date: "2025-07-26"
summary: "You don't have to be a compiler engineer to understand...how your code runs in a JIT build of CPython."
description: "You don't have to be a compiler engineer to understand..."
tags: ["Python", "JIT", "CPython"]
---

>  This post is the first in a planned series around CPython internals. The goal here is to make complex topics related to CPython feel more approachable. If I missed something or you’d like to request a topic, feel free to drop me a line at my [email](mailto:savannah@python.org).

Before I get into it, I want to shamelessly plug that you can help us test JIT builds of CPython pretty easily as of Python 3.14! You can now get official Python builds from [python.org](https://www.python.org/downloads/) for both Windows and macOS that include [CPython’s experimental just-in-time (JIT) compiler built in but off by default](https://docs.python.org/3.14/whatsnew/3.14.html#binary-releases-for-the-experimental-just-in-time-compiler). While the JIT builds are not (yet) recommended for production use, you can enable the JIT using the `PYTHON_JIT=1` environment variable. We’d love to hear about your experience using Python with the JIT - the good, the bad, the ugly!

Alright, let's get after it.

## What happens when you execute your code: A brief overview of CPython’s interpreter

...well, before we get into what happens in a JIT build of Python, we should probably briefly talk about what happens in a "regular" build for anyone that isn't familiar with how the interpreter works, as this lays the foundation for the JIT builds later on. I think the best way to talk about this is by example. To cover this, let’s consider this very basic function:

```python
def my_cool_function(a: int, b: int) -> int:
    if a > b:
        return a - b
    return b - a
```

You execute this with your local version of Python and boom, the code is running. But what actually happens here?

### First, we parse

Well, first, your code is turned into something called an abstract syntax tree (AST), which is a tree-based representation of the structure of your code. We can see what our simple function above's AST would look like using the `ast` module in the standard library. The code looks something like this:

```python
import ast

source = """
def my_cool_function(a: int, b: int) -> int:
    if a > b:
        return a - b
    return b - a

my_cool_function(5, 3)
"""

tree = ast.parse(source)
print(ast.dump(tree, indent=4))
```

...and this would return a tree like so:

```plaintext
Module(
    body=[
        FunctionDef(
            name='my_cool_function',
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
                func=Name(id='my_cool_function'),
                args=[
                    Constant(value=5),
                    Constant(value=3)]))])
```

This is a lot of information for such a short function but what you should really glean from this is that every variable, statement, function, constant, etc. along with its relationship is represented in this tree.

### Then, we compile to bytecode

Next, Python compiles that AST down into bytecode, which is really a lower-level, platform-independent representation of your code. This is what the CPython interpreter actually executes. 

Just like with the AST, you can see what the bytecode representation of this function would be. We can see what this would look like for the same function we looked at earlier using the `dis` module (aka the disassembly module) in the standard library. 

```python
import dis
def my_cool_function(a: int, b: int) -> int:
    if a > b:
        return a - b
    return b - a
dis.dis(my_cool_function)
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

This might look intimidating, but it's just a lower-level form of your original code. Here's a quick mapping:

<table data-start="1136" data-end="1638" class="w-fit min-w-(--thread-content-width)"><thead data-start="1136" data-end="1206"><tr data-start="1136" data-end="1206"><th data-start="1136" data-end="1179" data-col-size="sm">Bytecode instruction</th><th data-start="1179" data-end="1206" data-col-size="sm">Original code</th></tr></thead><tbody data-start="1279" data-end="1638"><tr data-start="1279" data-end="1350"><td data-start="1279" data-end="1322" data-col-size="sm"><code data-start="1281" data-end="1322">LOAD_FAST_BORROW_LOAD_FAST_BORROW (a,b)</code></td><td data-col-size="sm" data-start="1322" data-end="1350"><code data-start="1324" data-end="1331">a &gt; b</code> or <code data-start="1335" data-end="1342">a - b</code></td></tr><tr data-start="1351" data-end="1422"><td data-start="1351" data-end="1394" data-col-size="sm"><code data-start="1353" data-end="1379">COMPARE_OP 148 (bool(&gt;))</code></td><td data-col-size="sm" data-start="1394" data-end="1422"><code data-start="1396" data-end="1403">a &gt; b</code></td></tr><tr data-start="1423" data-end="1494"><td data-start="1423" data-end="1466" data-col-size="sm"><code data-start="1425" data-end="1444">POP_JUMP_IF_FALSE</code></td><td data-col-size="sm" data-start="1466" data-end="1494"><code data-start="1468" data-end="1479">if a &gt; b:</code></td></tr><tr data-start="1495" data-end="1566"><td data-start="1495" data-end="1538" data-col-size="sm"><code data-start="1497" data-end="1515">BINARY_OP 10 (-)</code></td><td data-col-size="sm" data-start="1538" data-end="1566"><code data-start="1540" data-end="1547">a - b</code> or <code data-start="1551" data-end="1558">b - a</code></td></tr><tr data-start="1567" data-end="1638"><td data-start="1567" data-end="1610" data-col-size="sm"><code data-start="1569" data-end="1583">RETURN_VALUE</code></td><td data-col-size="sm" data-start="1610" data-end="1638"><code data-start="1612" data-end="1624">return ...</code></td></tr></tbody></table>

This shows how Python breaks your logic into a series of simple instructions — each one executed by the Python Virtual Machine (PVM). The instructions here are minimal but powerful: they handle loading variables, performing comparisons, jumps, arithmetic, and returning values. The PVM pops these instructions off a stack and executes them one by one, maintaining the state of your program as it goes.

And that's it! Your code is now running in the Python interpreter, executing these bytecode instructions one by one.

### But, wait, there's more!

Since Python 3.11, we've had something called the [Specializing Adaptive Interpreter](https://peps.python.org/pep-0659/) in CPython. We won't get into this too deep in this blog post but in essence, this interpreter adds a layer to the regular interpreter which tries to look for common patterns and stable types in the code being executed and try to replace operations (aka the bytecode instruction(s)) with more specialized instructions.

For example, we could consider the `BINARY_OP` instruction in our bytecode. In the context of our function, this instruction is used to perform subtraction. In a regular build, it might be a generic operation that can handle any type of operands (like integers, floats, etc.). In a specialized build, this instruction could be replaced with a more specific one that only handles integer subtraction (assuming the operands are always integers) with `BINARY_OP_SUB_INT`, which would be faster because it skips type checks and other overhead associated with more generic operations.

The earlier parsing and compilation plus this specialization makes up what we call the **Tier 1 interpreter**. This is the first layer of optimization that Python applies to your code, and it’s what you get in a regular build of CPython.


## Okay, so what happens in JIT builds?

Right, right. Okay, so now that we understand how the interpreter works, we can talk about what happens when you run your code in a JIT build of CPython.

### Enter the Tier 2 interpreter: Micro-instruction (uops) interpreter

So, your code is running in the Tier 1 interpreter, which is already doing some smart things to optimize your bytecode. But what if we could do even better? What if we could take those bytecode instructions and turn them into something even more efficient? That’s where the Tier 2 interpreter comes in.

The Tier 2 interpreter is a new layer that sits on top of the Tier 1 interpreter. It takes the specialized bytecode instructions and translates them into something called micro-operations, or uops. These are simpler, lower-level instructions that are easier to optimize and closer to machine code. These uops are like the building blocks of your code, and they can be executed much faster than the original bytecode instructions.

Here’s how it works:
1. When your code is running in the Tier 1 interpreter, it keeps track of which bytecode instructions are being executed frequently. These are called "hot" instructions.
2. When a hot instruction is detected, the Tier 2 interpreter kicks in. It takes the bytecode instruction and translates it into a series of uops. These uops are designed to be more efficient and can be executed much faster than the original bytecode.
3. The Tier 2 interpreter then executes these uops instead of the original bytecode instruction. This means that your code can run much faster, especially for those hot paths that are executed frequently.

When you build Python with `--enable-experimental-jit`, you're enabling not just the JIT itself, but this entire Tier 2 machinery. 

### JIT Compilation: From uops to native machine code

Now that we have these uops, we can take it a step further. The JIT compiler in CPython takes these uops and compiles them into native machine code. This is where the real magic happens.

When your code runs in a JIT build of CPython, the JIT compiler does the following:
1. It monitors the execution of your code and identifies "hot" traces—sequences of uops that are executed frequently.
2. When a trace becomes hot enough, the JIT compiler kicks in. It takes the uops from that trace and compiles them into native machine code.
3. This native machine code is then executed directly by the CPU, bypassing the interpreter entirely. This means that your code can run at near-native speeds, significantly improving performance for those hot paths.
4. The JIT compiler uses precompiled stencil templates to generate this native code, which allows it to quickly patch in the specific values and addresses needed for your code.
This is a key part of the JIT compilation process. It allows Python to generate optimized machine code on the fly, tailored to the specific execution context of your code. This means that the JIT compiler can take advantage of the specific types and values used in your code, resulting in even better performance.

### How does the JIT compiler use precompiled stencil templates?
The JIT compiler uses precompiled stencil templates to generate native machine code quickly and efficiently. These templates are like blueprints for how to translate uops into machine code. They contain the general structure of the machine code needed for each uop, with placeholders for specific values that will be filled in at runtime.

When the JIT compiler detects a hot trace, it takes the relevant uops and uses the precompiled stencil templates to generate the native machine code. It fills in the placeholders with the actual values needed for your code, such as the addresses of variables, constants, and cached results. This allows the JIT compiler to produce optimized machine code that is tailored to the specific execution context of your code and can be executed directly by the CPU.

This process is efficient because it avoids the overhead of generating machine code from scratch every time a hot trace is detected. Instead, it reuses the precompiled templates, which have already been optimized for performance. This means that the JIT compiler can quickly generate native machine code that is ready to run, without the need for extensive compilation time.  

This is a key part of the JIT compilation process. It allows Python to generate optimized machine code on the fly, tailored to the specific execution context of your code. This means that the JIT compiler can take advantage of the specific types and values used in your code, resulting in even better performance.

## Putting it all together
So, to summarize, when you run your code in a JIT build of CPython, the following happens:
1. Your code is parsed into an AST.
2. The AST is compiled into bytecode.
3. The bytecode is executed by the Tier 1 interpreter, which may specialize some operations.
4. The Tier 2 interpreter monitors the execution and identifies hot bytecode instructions.
5. When a hot instruction is detected, the Tier 2 interpreter translates it into uops.
6. The JIT compiler compiles these uops into native machine code using precompiled stencil templates.
7. The native machine code is executed directly by the CPU, bypassing the interpreter.

This process allows Python to run your code much faster than in a regular build, especially for those hot paths that are executed frequently. The JIT compiler can optimize the execution of your code on the fly, resulting in hopefully[^performance] significant performance improvements.

[^performance]: Note that the performance improvements will vary depending on the specific code being executed and the workload. Not all code will benefit equally from JIT compilation, but for many workloads, the performance gains can be substantial. A topic for another post!

## Suggested readings & videos
Some other great talks, blog posts, etc. by other folks working on Python:
- Maybe watch one of Brandt's talks on this topic: here, here, or here
- ...Or maybe Diego's excellent talk from EuroPython this year
- Check out [PEP 744](https://www.python.org/dev/peps/pep-0744/), it's really not that scary!