---
title: "What the heck is a trampoline, anyway?"
date: "2025-11-04"
summary: "You don't have to be a compiler engineer to understand that trampolines are small hops to far destinations."
description: "You don't have to be a compiler engineer to understand that trampolines are small hops to far destinations."
tags: ["Python", "JIT", "CPython", "You don't have to be a compiler engineer"]
---

>  This is a post in a series around making CPython internals more approachable. If I missed something or you’d like to request a topic, feel free to drop me a line via [email](mailto:savannah@python.org). You can also read other posts in the series [here](https://savannah.dev/tags/you-dont-have-to-be-a-compiler-engineer/).

So, this post is going to be ~~potentially~~ probably very niche, but I just spent _a lot_ of time going down a rabbit hole working on [CPython's JIT LLVM 20 upgrade](https://github.com/python/cpython/pull/140329), and I learned a thing or two and figured maybe other folks might be interested as well. I am also a firm believer in teaching to solidify your learning, so I decided to write this post. It'll be one part diary entry to commemorate a sort of wild debugging chain at the Paris airport (twice!!), and one part educational!

Cool, cool…alright, so I've worked on our LLVM upgrades for the JIT for our last three version bumps. When you think about updating a dependency, you might think, "go into some manifest file, change a 1 to a 2, and boom, you're done." However, it's become somewhat of a running joke amongst the team that I take on this seemingly trivial task and then end up opening a can of worms because there is almost always some catch or some weird thing that breaks.

This time around…there was a new worm in the can…and it was called a trampoline. But before we get into that, I want to walk you through how I stumbled upon doing this work and why it was necessary for this version of LLVM.

## But first, more about stencils

If you recall from [this post](https://savannah.dev/posts/how-your-code-runs-in-a-jit-build/), before Python even runs with the JIT, we generate stencil files at build time using LLVM. These stencil files are really just a very long list of C functions (one per bytecode) compiled into machine code templates. The stencil file contains the raw machine code bytes for each operation, relocation information (where we need to patch things at runtime), which symbols (external functions) each stencil needs, and which stencils need trampolines.

Now, you might be asking, "Savannah, I want to see a stencil file," and then I'd tell you that you'll have to [build Python with the JIT enabled](https://github.com/python/cpython/blob/main/Tools/jit/README.md). Or, if you're less inclined, you can see [this stencil for the LOAD_FAST instruction](https://gist.github.com/savannahostrowski/a37e1c407d8e3b3c2571bf7d24eaeb7a). Gibberish? That's okay. The important part is that at runtime, we compile traces for a sequence of instructions that represent your program. For each operation, we get its precompiled stencil, copy it into executable memory, patch in the actual addresses we need, and then combine everything together into runnable machine code.

Now, when we generate these stencils, we use a bunch of compiler flags to tell LLVM how we want the stencils generated. You don't need to care too much about the specific flags or what they all mean at this point, but there are a lot of them. In a way, it's kind of like passing some kind of special incantation to the compiler…or at least it feels like that when things are broken and you are hitting random assertion errors in our instructions like I was.

## Alright, now let's talk about upgrading to LLVM 20!

So this time, when I bumped the version, everything worked, except on [x86_64 Darwin debug builds](https://github.com/savannahostrowski/cpython/actions/runs/18438327725/job/52537027963?pr=10#step:5:1584)! 

Curious, right…well, there are a couple of reasons for this. For one, we were previously using a compiler flag (`-fno-plt`), which I discovered through some trial and error (and compiler warnings) isn't supported on macOS in LLVM 20, so that had to go. Second, our debug builds are not optimized, so code can be naturally further apart in memory than in release builds. Without optimizations, the compiler doesn't pack things tightly, which means our generated machine code and the runtime symbols it needs to call can end up separated by more than 2GB in memory. So basically, when I hit the assertion error saying that `patch_32r` for x86_64 was more than 2GB away, I had two options: 1) the simpler option - find the right combination of compiler flags to make it work (`-mcmodel=medium,large`; `-fno-pic` etc.) or 2) implement a trampoline (we will get back to this in a second).

So naturally, I tried the simplest option first. I started down this rabbit hole in earnest during a layover at 8 am in the Paris airport on my way to Spain for a team offsite, delirious and running on about 45 minutes of sleep.

Unfortunately, that didn't work!

{{< figure src="../tired-dw.jpg" alt="A meme of DW from Arthur looking extremely tired while smiling" width="600" >}}

> *Live footage of me passing `-mcmodel=large` into the compiler for the fifth time, hoping it fixes all my problems*

So, I gave up…not really…But I did take a week break for the offsite and PyCon Spain.
However, on the way home from Spain, I had six whole hours in the Paris airport during my layover to get back at it. Thinking more about this problem, I remembered that [Diego had implemented trampolines for aarch64](https://github.com/python/cpython/pull/123872) a while back. I decided to give up on compiler flags and really go down the rabbit hole. What ensued next was a long while of reading [x86_64 instruction encoding](https://wiki.osdev.org/X86-64_Instruction_Encoding) to figure out how I could maybe handwrite x86-64 machine code byte-by-byte…a dark, dark place.

## Okay, so what the heck is a trampoline…

Okay, she's said the title of the blog post. We must be getting close! Yes, okay…so this is what a trampoline is - it's a small piece of code that acts as a bridge to another place in memory, some place we cannot directly reach. In this case, we need to access some symbol that's more than 2GB away from where we currently are in memory.

In the stencil snippet I linked to above, you'll notice some lines that say `patch_x86_64_trampoline`. Let's look at the actual patch instruction for the trampoline and walk through it.
```c
// Generate and patch x86_64 trampolines.
void
patch_x86_64_trampoline(unsigned char *location, int ordinal, jit_state *state)
{
    uint64_t value = (uintptr_t)symbols_map[ordinal];
    int64_t range = (int64_t)value - 4 - (int64_t)location;

    // If we are in range of 32 signed bits, we can patch directly
    if (range >= -(1LL << 31) && range < (1LL << 31)) {
        patch_32r(location, value - 4);
        return;
    }

    // Out of range - need a trampoline
    unsigned char *trampoline = get_trampoline_slot(ordinal, state);

    /* Generate the trampoline (14 bytes, padded to 16):
       0: ff 25 00 00 00 00    jmp *(%rip)
       6: XX XX XX XX XX XX XX XX   (64-bit target address)

       Reference: https://wiki.osdev.org/X86-64_Instruction_Encoding#FF (JMP r/m64)
    */
    trampoline[0] = 0xFF;
    trampoline[1] = 0x25;
    memset(trampoline + 2, 0, 4);
    memcpy(trampoline + 6, &value, 8);

    // Patch the call site to call the trampoline instead
    patch_32r(location, (uintptr_t)trampoline - 4);
}
```

Here's what's happening:

First, we get the `value` - this is the memory address of the actual symbol we need to jump to. The `ordinal` is just an index that identifies which symbol we're dealing with (like "symbol #5" or "symbol #37"). A symbol is an external function that the JIT-compiled code needs to call at runtime, things like `PyObject_GetAttr` (to get an attribute from a Python object) or `PyDict_GetItem` (to get an item from a dictionary). Every external function is assigned an ordinal number.

Then we calculate the `range`, which is the distance in memory between our current location (`location`) and where we want to reach (`value`).
Next, we check if the symbol is reachable - in this case, within 2GB in memory (this is the assertion that failed in the first place!). If it's reachable, we just use the standard patch function, `patch_32r`, and we're done.

If not, we need a trampoline! We call `get_trampoline_slot` to get a memory location for our trampoline.

Then we generate the trampoline itself; this is where I had to read some wild x86-64 encoding instructions to figure out the machine code for a jump instruction. The trampoline is just 14 bytes (padded to 16): the first 6 bytes are the jump instruction (`jmp *(%rip)`), and the next 8 bytes are the 64-bit address we're jumping to.

Finally, we patch the original call site to point to the trampoline instead of trying to reach the far-away symbol directly.

Let's go down the rabbit hole a bit more and dissect the `get_trampoline_slot` function. This is sort of clever, so bear with me.

The problem we're solving: we have a pool of trampolines (basically an array of memory slots), and we need to figure out "for symbol X, which slot in the pool should I use?" However, not every symbol needs a trampoline. Remember, we only need trampolines when the symbol is too far to reach.
So we can't just use the symbol's ordinal as the array index, because that would waste a ton of memory. If we have 100 symbols but only 5 need trampolines, we don't want to allocate 100 trampoline slots!

The solution is to use a bitmask to track which symbols need trampolines and calculate their slot positions on the fly. Bitmasks kind of break my brain a bit, so I'll try to break this down for folks who feel similarly 😭

```c
// Get the trampoline memory location for a given symbol ordinal.
static unsigned char *
get_trampoline_slot(int ordinal, jit_state *state)
{
    const uint32_t symbol_mask = 1 << (ordinal % 32);
    const uint32_t trampoline_mask = state->trampolines.mask[ordinal / 32];
    assert(symbol_mask & trampoline_mask);

    // Count the number of set bits in the trampoline mask lower than ordinal
    int index = _Py_popcount32(trampoline_mask & (symbol_mask - 1));
    for (int i = 0; i < ordinal / 32; i++) {
        index += _Py_popcount32(state->trampolines.mask[i]);
    }

    unsigned char *trampoline = state->trampolines.mem + index * TRAMPOLINE_SIZE;
    assert((size_t)(index + 1) * TRAMPOLINE_SIZE <= state->trampolines.size);
    return trampoline;
}
```
Here's the key idea: we need to answer "how many trampolines come before this symbol?" The answer tells us which slot in our array to use.
We store our bitmask as an array of 32-bit integers, where each bit represents whether a symbol needs a trampoline. Let's walk through an example. Say we have symbols 3, 7, 15, 37, and 42 that need trampolines (the only bits set to 1 in our bitmask). If we're looking for symbol 37's slot:

**Step 1: Find which bit represents our symbol**  
Symbol 37 is bit 5 in the second 32-bit chunk (37 % 32 = 5). We create a mask with just that bit set: `1 << 5`.

**Step 2: Count all trampolines in earlier chunks**  
Symbol 37 is in chunk 1 (37 / 32 = 1, integer division), so we need to count all set bits in chunk 0. That's symbols 3, 7, and 15 - giving us 3 trampolines. We use `_Py_popcount32`, which counts set bits in a 32-bit integer.

**Step 3: Count trampolines before us in our own chunk**  
We use `(symbol_mask - 1)` to create a mask of all bits lower than ours (for bit 5, this gives us bits 0-4), then AND it with the trampoline mask to see which of those lower bits are actually set, then count them. In our example, there are no symbols between 32 and 37 that need trampolines, so this adds 0.

**Step 4: Calculate the final position**  
Symbol 37 gets index 3 (the 4th slot, since we're 0-indexed). We take our base memory address (`state->trampolines.mem`) and add `index * TRAMPOLINE_SIZE` to get to the right slot.

Break your brain a bit? Same! However, the beauty of this approach is that our trampoline pool is densely packed. We only allocate as many slots as we actually need, but we can still quickly calculate where any symbol's trampoline lives.

## Putting it all together

So, TL;DR, this is what’s happening:
```
Original code:     [call instruction] --X--> [target] (too far, >2GB away)

With trampoline:   [call instruction] -----> [trampoline] -----> [target]
                                          |                   	 |
                                          | jmp *(%rip)          |
                                          | [64-bit address] ----+
```
The trampoline is just a tiny piece of code that lives close enough to our call site (within 2GB) that we can reach it with a normal 32-bit relative jump, and it contains an instruction that can jump to the full 64-bit address of our actual target.

## And that's that!

If you made it this far, congrats! You now know way more about trampolines than you probably ever wanted to, and hey! You didn't need to be a compiler engineer to understand it (hopefully!)

> If you enjoyed this post, please consider sharing it with anyone you think might find it interesting. If you have any questions or feedback, feel free to reach out to me via [email](mailto:savannah@python.org).

