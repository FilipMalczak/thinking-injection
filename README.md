# thinking-injection

[![CI](https://github.com/FilipMalczak/thinking-injection/actions/workflows/ci.yml/badge.svg)](https://github.com/FilipMalczak/thinking-injection/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/thinking-injection.svg)](https://badge.fury.io/py/thinking-injection)
[![codecov](https://codecov.io/github/FilipMalczak/thinking-injection/graph/badge.svg?token=X5HGHMQXAP)](https://codecov.io/github/FilipMalczak/thinking-injection)

> Part of [thinking](https://github.com/FilipMalczak/thinking-rationale) family.

Pythonic DI for AI, as funny as it sounds.

> Requires python 3.12. Is properly typed.

> Better docs pending. For now, see "long story short" and an example

## Long story short

> TODO API changed, rewrite this

 - put your code in a root package (let's call it `root`) with any number and depth of subpackages
 - mark the types that should be picked up by framework with `@discover`
   - `from thinking_injection.discovery import discover`
 - mark your protocols and ABCs with `@interface`
   - `from thinking_injection.interfaces import interface`
 - make the classes that should be managed extend `Injectable`
   - in Java you'd call these "beans", but I wanted to avoid that kind of copycating
   - `from thinking_injection.injectable import Injectable`
 - implement `inject_requirements(self, ...)` and make sure to annotate the arguments
   - `class X(Injectable): def inject_requirements(self, a: A, b: list[B], c: C | None: ...`
   - in that case, instance of `X` will be created for you, and that method will be called with auto-created instances
     of `A`, list of all known instances of `B` and instance of `C` if there is one
   - `A` is a `SIMPLE` dependency, `B` - a `COLLECTIVE` one, `C` - an optional one
   - there is a notion of `primary` implementation, which works as you'd expect it (the type itself for non-interface
     types, the subclass if there is only one subclass, but you can also force one, e.g. with decorator)
     - `from thinking_injection.discovery import PrimaryImplementation` - use `@PrimaryImplementation(Supertype)` on the subtype
   - simple dependencies will use the primary implementation
   - optional dependencies can be phrased any way you like: `C | None`, `Optional[C]` or `Union[C, None]`, etc
     - if there is no primary implementation, `None` will be injected, even if there are multiple implementations
   - collective dependencies can only be phrased as lists of supertype (interface or not) 
   - framework will only call that method for you with proper args, you should store them in `self` on your own - or
     act on them in any way you'd like
 - make a `ContextScope` using `of` factory method:
   - `from thinking_injection.scope import ContextScope`
   - `ContextScope.of(*from_package("root"))`
   - more readable factory methods pending
   - generally, it's `ContextScope.of(Type1, Type2, ...)`
   - you can also define which implementations should be primary with `defaults` and `forced` kw-only args
     - > todo document this
   - there is also `from_module("root.some.submodule")` function, as well as `types(Type1, Type2, ...)`
   - see [`thinking_injection.typeset`](./thinking_injection/typeset.py)

The entrypoint to your program should boil down to:

```python
if __name__=="__main__":
    scope = ContextScope.of(...)
    ctx = BasicContext.build(scope)
    with ctx.lifecycle():
        instance = ctx.instance(SomeType)
        instance.foo(...)
```

## An example

There is an example app in this repo. It's short, but showcases most of the basic features.

See the [./calculator](./calculator/README.md) directory.

## Local development

There are 2 useful scripts in this repo. They both work based on [`./thinking-dependencies.txt`](./thinking-dependencies.txt)
file, which lists other `thinking` projects used by this one.

 - [`install_develop.sh`](./install_develop.sh)
   - will install all the `thinking` dependencies from their `develop` branches
 - [`./install_local_thinking.sh`](./install_local_thinking.sh)
   - aligned to my personal layout of home directory
   - assumes you clone repositories to `~/repos`
   - expects all the `thinking` dependencies to be cloned there
   - will create venv for you if missing or use an existing one
   - will remove currently installed `thinking` dependencies
   - and will install them again from the cloned repos
   - useful when you're making complimentary changes across repos