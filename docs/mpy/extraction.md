# Dungeon Drifters MicroPython Library Extraction Audit

## 1. Executive conclusion

The strongest extraction candidate is **the dataclass metadata pipeline, not merely the dataclass runtime**.

The key distinction in Dungeon Drifters is the same one your brief emphasizes: MicroPython accepts annotation syntax but does not retain enough runtime annotation information to discover ordinary annotation-only dataclass fields.  MicroPython 1.29.0 still documents annotation behavior as deliberately reduced, and `udataclasses`, the strongest existing competitor I found, explicitly says MicroPython discards type annotations and consequently requires otherwise annotation-only fields to be assigned `field()` or a default. 

That means DD appears to solve a materially different problem:

> **Keep authoring conventional CPython-style dataclasses in source, recover the field model off-device, then supply that model to a constrained runtime.**

I did **not** find a mature existing MicroPython library implementing that same host-generated metadata architecture, particularly with DD's `(module, qualified class name)` identity and generated field manifest. I therefore classify the overlap for that specific capability as **NO MEANINGFUL EXISTING SOLUTION found in this audit**, with an important qualification: that is a research finding, not a proof of novelty.

My candidate recommendations are:

| Candidate | Recommendation |
|---|---|
| Generated dataclass/annotation metadata | **EXTRACT AFTER DD QUALIFICATION** |
| MicroPython dataclass runtime built around that metadata | **EXTRACT AFTER DD QUALIFICATION**, preferably as the runtime half of the same project |
| StrEnum | **PROMISING, RESEARCH FURTHER** |
| Read-only mapping | **KEEP INTERNAL / feature of another package** |
| `keyword.iskeyword()` | **REPLACE WITH EXISTING LIBRARY** |
| `re.fullmatch` shim | **KEEP INTERNAL** or contribute upstream; too small for a package |
| `collections.abc` shim | **KEEP INTERNAL** |
| One umbrella DD compatibility package | **Not presently justified** |

The most compelling package boundary is therefore close to your Option 3, but I would start with **two installable/runtime layers in one cohesive project**, not three unrelated packages:

```text
portable-dataclass-metadata
    host-side scanner/generator
    manifest format

portable-dataclasses-mpy
    MicroPython dataclass runtime
    consumes generated metadata
```

StrEnum should stay separate because its implementation mechanism and failure modes have almost nothing in common with generated dataclass metadata.

The recommendation should still be executed **after DD's MicroPython qualification is complete**, because the game is currently the only substantial integration corpus described in the supplied material. 

---

# 2. Gate-to-library map

I could verify the contemporary MicroPython ecosystem independently, but public search indexing did **not expose the contents of the `myp` branch or individual DD MYP commits sufficiently for a trustworthy independent diff audit**. Consequently, the mechanism descriptions below are grounded in the supplied gate record, rather than pretending I independently inspected code I could not retrieve. The repository itself is publicly indexed and was shown as updated in August 2026. 

| Gate | SHA | Problem | Mechanism | Reusability | Likely destination |
|---|---|---|---|---|---|
| MYP0 | `f39770a...` | Qualification infrastructure | Probe/test foundation | Medium | DD tooling, possibly reusable test pattern |
| MYP1 | `783f9dd...` | `MappingProxyType` absence | copied read-only mapping | Low–medium | implementation detail |
| MYP2 | `34f697d...` | Runtime cannot discover normal dataclass fields | contract/audit of annotation loss | **Very high** | metadata/dataclass project |
| MYP3 | `28b0e7e...` | Supply missing field model | CPython discovery + generated manifest + MicroPython decorator | **Very high** | primary extraction |
| MYP4 | `0a9677d...` | `StrEnum` absent | portable string-enum overlay | Medium–high | possible separate package |
| MYP5 | `2f656ba...` | `keyword.iskeyword` missing | narrow compatibility module | Low | replace |
| MYP6 | `a97def8...` | constructing enum from existing member | construction repair | Medium–high | StrEnum package feature |
| MYP7 | `6b4883a...` | no `re.fullmatch` | native `match()` + consumption check | Low | shim/internal |
| MYP8 | `bb99b7e...` | imports/`isinstance` expectations for ABCs | synthetic `collections.abc`, tuple-like type boundaries | Low | DD-specific |

Those classifications follow the behavioral descriptions in the supplied lineage. 

I found no reliably indexed evidence establishing a newer sealed MYP gate, so I would continue treating MYP8 as the audited completed baseline rather than guessing that MYP9 has landed.

---

# 3. Existing ecosystem comparison

## The important projects

### `udataclasses`

This is the closest serious competitor.

Its documentation directly confirms DD's underlying problem:

* MicroPython and CircuitPython discard annotation information.
* An annotation-only declaration such as `name: str` cannot be discovered.
* Users therefore must write `name: str = field()` or provide a default.
* Field source ordering is not recoverable, so `udataclasses` sorts fields alphabetically.
* Constructors are consequently keyword-only.
* `Field.type` is `object` because annotation metadata is unavailable. 

That is **STRONG OVERLAP** with DD's runtime goal but only **PARTIAL OVERLAP** with DD's overall architecture.

Crucially, it **does not solve the same source-compatibility problem**.

DD's generator exists specifically so this:

```python
@dataclass
class Product:
    name: str
    quantity: int = 0
```

can remain the authoritative source instead of requiring MicroPython-specific declarations such as:

```python
name: str = field()
```

That is the strongest evidence that DD's work has independent value.

### Official `micropython-dataclasses`

The PyPI package with that exact name is not a competitor. Its only release is `0.0.0` from September 7, 2018 and describes itself as a **dummy implementation** intended mainly to avoid import errors. It is MIT licensed. 

Classification: **SUPERFICIAL**.

### Small `udataclasses.py` implementations

There are lightweight community implementations—for example a 2025 gist that generates dataclass-like behavior from class attributes. 

These reinforce that there is demand for the concept, but they do not provide DD's metadata recovery architecture or a convincing compatibility/test story.

Classification: generally **PARTIAL OVERLAP**.

### CircuitPython NitroClass

`circuitpython-nitroclass` is a recent CircuitPython project described as providing dataclass-like class functionality. It depends on Adafruit CircuitPython. 

It is relevant ecosystem evidence, but it does not establish the DD requirement of preserving ordinary CPython dataclass source and recovering lost annotation fields externally.

Classification: **COMPLEMENTARY / PARTIAL OVERLAP**, depending on desired scope.

---

# 4. Dataclass / annotation analysis

## The actual gap

MicroPython 1.29.0 still does not list `dataclasses` among its built-in/micro-ified standard modules. 

More importantly, adding a `dataclasses.py` implementation by itself does not fix the underlying information loss.

`udataclasses` demonstrates this perfectly. It already supplies a MicroPython-specific runtime decorator but has to change source authoring conventions because the runtime cannot see annotation-only fields. 

That gives DD's architecture a meaningful differentiator.

### Approximate comparison

| Capability | DD MYP3 design | `udataclasses` | old `micropython-dataclasses` |
|---|---:|---:|---:|
| Normal `@dataclass`-style source | **Yes** | Mostly |
| annotation-only required fields | **Yes, through generated metadata** | **No** | No meaningful implementation |
| defaults | Yes | Yes | — |
| `default_factory` | Yes | supported conceptually | — |
| source field order | **Recoverable host-side** | No; alphabetic | — |
| frozen | Yes, DD subset | project-dependent | — |
| `__post_init__` | Yes | partial/implementation-specific | — |
| equality | Yes | Yes | — |
| field type metadata | generator can preserve it if designed to | `object` because annotations unavailable | — |
| host code generation | **Yes** | No | No |
| manifest | **Yes** | No | No |
| module + qualname identity | **Yes** | No comparable facility found | No |
| unchanged CPython authoring | **Core design goal** | Requires field markers for required fields | No |

The DD manifest reportedly covers about 74 production dataclasses.  That matters: this is substantially better evidence than a toy decorator supporting three test classes.

## Why the generator is more interesting than `dataclasses.py`

The host-side manifest mechanism can potentially serve other systems where the target Python runtime discards information that exists in source or on CPython:

* serializer schemas,
* attrs-like object models,
* command schemas,
* lightweight validation,
* generated RPC models,
* embedded object introspection,
* other constrained Python implementations.

But I would **not expose this as a generic annotation framework in version 1**.

That would prematurely turn a concrete solution into a framework.

The smallest defensible boundary is:

```text
"Recover dataclass field metadata on a host Python,
ship it as static data,
consume it on MicroPython."
```

Make the manifest format modular enough that other consumers can eventually use it, but keep the public use case dataclasses-first.

### Novelty assessment

For **“a MicroPython dataclass implementation”**: no novelty claim is justified.

For **“host-generated field metadata that lets conventional annotation-driven dataclass source survive a target runtime that loses annotations”**: I found no meaningful existing MicroPython analogue.

That is the extraction-worthy part.

---

# 5. StrEnum analysis

This is more ambiguous.

The old PyPI `micropython-enum` package is only a dummy module dating to 2017. 

However, the official `micropython-lib` ecosystem is now actively developing a real `enum` module. There is an open `python-stdlib: Add enum module` PR, and its CI was still active in April 2026. 

That changes the strategic answer.

## Existing CPython StrEnum packages are not enough

The well-known `StrEnum` project:

* targets Python 3.7+,
* inherits from CPython's `enum.Enum`,
* is MIT licensed,
* explicitly exists mainly as pre-3.11 CPython functionality. 

It is therefore **SUPERFICIAL overlap** for MicroPython.

A 2026 CircuitPython/MicroPython enum experiment also documents the exact structural difficulty: conventional Enum implementations depend on language machinery constrained runtimes may not provide, and its author resorts to a decorator-style transformation rather than normal enum class syntax. 

So DD does appear to be addressing a real pain point.

## DD's advantage

According to the supplied contract, DD preserves:

```python
class Example(StrEnum):
    VALUE = "value"
```

along with:

```python
Example("value") is Example.VALUE
Example(Example.VALUE) is Example.VALUE
isinstance(Example.VALUE, str)
Example.VALUE == "value"
```

and `.name`, `.value`, hashability and dictionary-key behavior. 

That is a useful and coherent subset.

## The problem: `__build_class__`

The implementation's biggest issue is its global hook of `builtins.__build_class__`.

The DD scope discipline helps—only direct portable `StrEnum` subclasses are transformed and unrelated classes delegate to the original function.  But this is still a process-wide interpreter hook.

For a game-controlled runtime, that can be reasonable.

For a public package loaded alongside arbitrary third-party modules, the risk profile is materially worse:

* import order becomes relevant;
* two packages could wrap `__build_class__`;
* reload/idempotence behavior matters;
* debugging class creation becomes harder;
* future MicroPython internals can invalidate assumptions;
* composability with other compatibility libraries becomes uncertain.

So I would **not release `micropython-strenum` yet solely because DD's tests pass**.

### What would change the recommendation

Before extraction, compare DD directly against the pending official `micropython-lib` enum implementation once that API settles.

Specifically test:

```text
str subclassing
raw-value construction
member-value construction
.name/.value
hashing
aliases
duplicate values
custom methods
iteration
class subscription
subclass behavior
memory footprint
```

If official `enum` supplies a workable `Enum` base from which StrEnum can be implemented **without** globally wrapping `__build_class__`, DD should probably adopt that foundation instead.

Current recommendation: **PROMISING, RESEARCH FURTHER**.

---

# 6. Secondary compatibility analysis

## MYP1 — read-only mapping

Useful internally, but not enough for a separate library.

The best packaging outcome is probably to keep `_ReadonlyMapping` private inside whichever compatibility component needs it.

**Classification:** feature of another library / internal detail.

---

## MYP5 — `keyword`

This is already solved.

`micropython-keyword` is an actual CPython keyword-module port, not a dummy package. Its latest listed PyPI release is `3.3.3.post1`, released November 10, 2018. 

It is old, but the required API is tiny and stable.

**Classification: REPLACE WITH EXISTING LIBRARY**, unless DD's implementation is deliberately smaller enough that dependency elimination is worth more than reuse.

There is no good case for publishing DD's own `keyword` library.

---

## MYP7 — `re.fullmatch`

MicroPython 1.29 still exposes `match`, `search`, `sub` and related regex-object methods, but no documented `fullmatch`. 

So DD's shim remains useful.

But:

```python
match(...)
+ verify entire input consumed
```

is too small and too closely coupled to native MicroPython regex semantics to merit its own package.

**Classification:** general compatibility utility at most.

A contribution to `micropython-lib` would be more valuable than `micropython-re-fullmatch` as a standalone project.

---

## MYP8 — `collections.abc`

The historical `micropython-collections.abc` package is another dummy implementation intended mostly to satisfy imports. 

DD's:

```python
Mapping = (dict, _ReadonlyMapping)
Sequence = (list, tuple)
```

isn't an ABC implementation either; it is an `isinstance()` compatibility boundary specialized to known DD types. 

That is a perfectly legitimate application shim.

It would be misleading as a public `collections.abc` library.

**Classification: KEEP INTERNAL.**

---

# 7. Recommended extraction boundaries

I would reject the umbrella-package option for now.

`dataclasses` and `StrEnum` happen to have arisen in the same portability campaign, but technically they have:

* different implementation strategies,
* different risks,
* different upstream competitors,
* different maintenance cycles,
* no meaningful dependency between them.

Putting them in `dd-micropython-compat` would couple unrelated features because of their history rather than their architecture.

The cleanest structure is:

```text
project: portable-dataclasses-mpy

host/
    scanner
    dataclass discovery
    manifest generation
    validation/freshness checks

runtime/
    dataclass
    field
    field metadata
    generated __init__
    frozen handling
    equality
    post-init support

manifest/
    schema/version
    class identity
    serialized field definition
```

Internally, make the metadata reader independent of the decorator. That preserves the possibility of extracting a generic metadata generator later without forcing that abstraction now.

Then separately, if research against the official enum PR remains favorable:

```text
project: micropython-strenum

strenum.py
tests/
compatibility matrix
```

No shared umbrella dependency is needed.

---

# 8. Generalization work required

## Dataclass extraction — **MODERATE**

### Required for extraction

1. **Remove DD package-root assumptions.**

   Scanner input must be explicit package/module roots rather than knowing Dungeon Drifters' directory structure.

2. **Version the manifest format.**

   Generated metadata becomes an API once another project consumes it.

3. **Define manifest freshness behavior.**

   A stale manifest is more dangerous than an obvious missing dependency because code can continue running with the wrong constructor contract.

   Consider storing a deterministic fingerprint of source-discovered field metadata.

4. **Make module + qualname identity formally specified.**

   DD already has a good basis here. 

5. **Remove import side effects from discovery where feasible.**

   Importing arbitrary application modules simply to enumerate dataclasses can execute application initialization. Prefer AST/source discovery if it can preserve the needed semantics; otherwise document host-import requirements clearly.

6. **Separate generator dependencies from runtime dependencies.**

   Embedded devices should not need AST/parser/build dependencies.

7. **Build dual-runtime tests.**

   The same fixture classes should run under CPython and MicroPython and have explicitly compared supported behavior.

8. **Declare the compatibility subset precisely.**

   Do not market this as “Python dataclasses for MicroPython” without an explicit unsupported-feature table.

### Good generalization

* pluggable output path;
* multiple package roots;
* deterministic manifests;
* useful stale/missing-entry errors;
* optional inspection/debug command;
* CI against several supported MicroPython releases.

### Optional

* external consumers of the manifest;
* JSON versus Python-module manifest formats;
* type serialization;
* incremental generation.

### Do not generalize yet

* arbitrary annotation preservation;
* Pydantic-style validation;
* attrs compatibility;
* serializers;
* schema languages;
* plugin ecosystems.

Those would turn a crisp portability mechanism into a framework before external users demonstrate demand.

---

## StrEnum extraction — **MODERATE to HIGH**

The code may be smaller than the dataclass system, but the generalization risk is higher because it modifies global class construction.

Required work would include:

* idempotent install/uninstall behavior;
* wrapping an existing third-party wrapper safely;
* reload tests;
* multiple StrEnum modules loaded simultaneously;
* custom methods;
* nested classes;
* subclass-of-subclass behavior;
* duplicate values and aliases;
* exceptions during class construction;
* interaction with official `enum`;
* CPython no-op/native path;
* explicit MicroPython release matrix.

I would not publish until these questions are resolved.

---

# 9. Risks and reasons not to extract

## Dataclass system

The strongest argument against extraction is **build-system complexity**.

A library whose selling point is source compatibility now requires:

```text
normal source
   ↓
host-side analysis
   ↓
generated artifact
   ↓
deploy both source + artifact
```

That is substantially more operational machinery than `udataclasses`.

For small embedded programs, users may prefer:

```python
x: int = field()
```

over adopting a generator.

So the target user is not “every MicroPython programmer.”

It is specifically projects that:

* share source with CPython,
* have many dataclasses,
* strongly value unchanged source syntax,
* already have a host-side build/deployment step.

DD itself appears to fit that profile unusually well.

Other risks:

**Manifest authority.** If the generated file contradicts source, which wins? The answer must always be explicit.

**Source execution.** If discovery imports modules, generation can produce side effects.

**Identity collisions.** `(module, qualname)` is a sensible key, but dynamic classes/redefinitions remain edge cases.

**Inheritance.** Unsupported inheritance can become surprisingly visible once third parties use the library.

**Future MicroPython changes.** If future MicroPython versions preserve sufficient metadata, the generator could become unnecessary. That would be a success condition, not a failure—but the package should detect it cleanly.

---

## StrEnum

The strongest argument against publishing it is the global runtime mutation.

A narrow `__build_class__` interceptor can be controlled within DD because DD owns its import environment.

A package cannot assume that.

The upcoming official `micropython-lib` `enum` implementation also means a standalone DD solution may have a short useful life if the official module provides a safer foundation. 

That is why dataclasses and StrEnum should not receive the same extraction decision.

---

# 10. Licensing

MicroPython itself is MIT licensed.  `micropython-lib` also describes its contributions as MIT-oriented, although individual stdlib ports can include relevant upstream licensing. 

Other notable facts:

* `micropython-dataclasses`: MIT. 
* `micropython-enum`: MIT. 
* `StrEnum`: MIT. 
* `micropython-keyword`: listed under the Python license because it is a CPython stdlib port. 

I could **not independently retrieve the Dungeon Drifters LICENSE file from the indexed repository results**, so I would not assert its exact license from incomplete evidence. Before extraction, that is a mandatory check: the extracted code needs a clear license, and any code directly derived from CPython or another compatibility implementation must retain whatever notices its source license requires.

That is a licensing-fact check, not legal advice.

---

# Final recommendation

### Dataclass generator + runtime
**EXTRACT AFTER DD QUALIFICATION**

This is the part that appears to have become a genuinely reusable library.

The strongest existing competitor, `udataclasses`, actually validates DD's premise: it explicitly cannot recover annotation-only fields and therefore changes the user's source model. DD's generated-manifest approach attacks that limitation directly. 

The valuable abstraction is **not “yet another dataclass decorator.”**

It is:

> **Host-side recovery of information that MicroPython deliberately does not retain, feeding a small deterministic runtime while preserving conventional CPython source.**

That is a useful architectural idea.

### StrEnum
**PROMISING, RESEARCH FURTHER**

The behavioral subset is coherent, and existing CPython `StrEnum` libraries do not solve the MicroPython problem. But the global `__build_class__` interception is a real public-library concern, and official `micropython-lib` enum work is now underway. 

Re-evaluate after testing against that implementation.

### MYP1 read-only mapping
**KEEP INTERNAL**

Useful implementation machinery, not an independent product.

### MYP5 keyword
**REPLACE WITH EXISTING LIBRARY**

Already solved by the official historical MicroPython stdlib port. 

### MYP7 fullmatch
**KEEP INTERNAL**

The gap still exists in MicroPython 1.29's documented regex API, but the fix is too small for an independent library. 

### MYP8 collections.abc
**KEEP INTERNAL**

DD's representation is intentionally a compatibility trick rather than an ABC implementation. The old public MicroPython package is itself only a dummy placeholder. 

## Bottom line

Dungeon Drifters probably did accidentally produce **one particularly interesting reusable MicroPython system**: the **generated dataclass metadata + embedded runtime combination**.

The unusual part is exactly the part you suspected. A dataclass decorator on MicroPython already exists. What remains conspicuously underserved is preserving ordinary annotation-driven source when the target runtime has thrown away the information that decorator needs.

That is a substantially better extraction thesis than “DD has a useful `dataclasses.py`.”

StrEnum may be the second library, but the ecosystem is moving underneath it in 2026, so I would require another qualification round before committing to it.

---

Yeah, this is actually a very useful independent check because it lands almost exactly where we were landing, but for better-defined reasons.

The biggest confirmation is that the **dataclass work is not interesting because it is “dataclasses on MicroPython.”** That already exists. The interesting part is the **host-generated metadata architecture** that preserves ordinary CPython-style annotation-driven source even though MicroPython throws away the runtime information a decorator would normally need. The audit specifically says it found no mature equivalent using the same host-generated field model, especially with `(module, qualified class name)` identity and a generated manifest. 

That is a much stronger extraction thesis than what we started with:

```text
Not:
"we made dataclasses work"

But:
"we recover metadata off-device that the constrained runtime discards,
then feed a deterministic runtime representation back to MicroPython."
```

And the audit independently found `udataclasses`, which is probably the most important comparison. Its limitation basically validates why our approach exists: annotation-only fields cannot be discovered, field order is lost, and users have to change how they author classes. 

So on that one I’d upgrade my confidence considerably:

```text
MYP2 + MYP3
Dataclass metadata generator + runtime

→ very likely worth extracting
→ after DD qualification finishes
```

The auditor even arrives at essentially the same package boundary we were circling: metadata generation and runtime belong together conceptually, while keeping the metadata reader internally separable so we don't prematurely turn it into some giant annotation framework. 

The **StrEnum result is more interesting**, because the independent audit is noticeably more cautious than I was initially. It agrees the functionality is useful and that existing CPython `StrEnum` packages don't solve this MicroPython problem, but it flags the same ugly part we already knew about: the process-wide `__build_class__` interception is much easier to justify inside DD than inside an arbitrary user's runtime. 

And the important new information is that **official `micropython-lib` enum work is actively moving**. That means before we extract MYP4/MYP6, we'd want to test our exact contract against whatever that implementation becomes. If it gives us a safe Enum foundation, we may be able to keep the nice DD `StrEnum` semantics while deleting the sketchiest part of our implementation.  

So I'd now classify them:

```text
Dataclass metadata/runtime:
VERY LIKELY LIBRARY

StrEnum:
POSSIBLE LIBRARY
but wait for DD qualification + official enum comparison
```

The secondary findings also fit beautifully with what MYP9 and MYP10 are teaching us. The audit says read-only mapping should stay internal, `keyword` already has an existing implementation, `re.fullmatch` is useful but too tiny for its own package, and our `collections.abc` solution is intentionally not a real ABC implementation and therefore should stay DD-specific. 

And now we've subsequently added:

```text
MYP9
str.isascii / str.isdecimal
→ don't build a string compatibility framework
→ rewrite the source portably

MYP10
Counter
→ don't build a Counter compatibility framework
→ rewrite the source portably
```

Which makes the extraction boundary even clearer.

We're effectively discovering three categories:

```text
1. Fundamental missing capability
   → potentially extract
   dataclass metadata
   StrEnum maybe

2. Tiny missing stdlib behavior
   → local shim
   regex fullmatch
   keyword

3. CPython convenience with an equally clean portable expression
   → rewrite production source
   string validation
   Counter
```

That's a really healthy result because it means we're **not accidentally constructing `dd-micropython-everything`**.

The other thing I like is that the auditor actively tried to argue against extraction. Their strongest objection to the dataclass system is the host build step. For a tiny embedded script, requiring a generator is absolutely worse than simply writing `field()`. But for projects sharing substantial source between CPython and MicroPython, especially with dozens of dataclasses, the economics reverse. 

DD is basically the ideal stress case:

```text
74 dataclasses
normal CPython source stays authoritative
same gameplay code across runtimes
generated artifact already acceptable
CI/build tooling already exists
```

So the library shouldn't be marketed as:

```text
"Best dataclasses for every MicroPython project"
```

It should be something closer to:

```text
"Preserve normal dataclass source across CPython and MicroPython
when MicroPython discards the annotation metadata your models require."
```

That is a much sharper product.

One caveat with the audit: it explicitly says it couldn't independently inspect the live `myp` branch/commits well enough and therefore treated **MYP8 as the last sealed gate**. 

So its ecosystem analysis is valuable, but its DD lineage is now stale. We know the actual state is:

```text
MYP9
d78c07293219116f04f9c203b6654bf8b9728e35
SEALED

MYP10
Counter removal
READY
```

That doesn't undermine its conclusion at all. If anything, MYP9 and MYP10 strengthen the conclusion that **only the genuinely hard compatibility mechanisms should become libraries**.

The independent audit's bottom line is basically the one I'd adopt now:

```text
Dataclass generator + runtime
→ EXTRACT AFTER DD QUALIFICATION

StrEnum
→ RESEARCH FURTHER
→ specifically compare against evolving official enum support

MappingProxy fallback
→ KEEP INTERNAL

keyword
→ DON'T PUBLISH OUR OWN

re.fullmatch
→ KEEP INTERNAL / maybe upstream contribution

collections.abc
→ KEEP INTERNAL

umbrella compatibility package
→ NO
```

That last one is important. The audit explicitly rejects bundling dataclasses and StrEnum merely because they were discovered during the same portability campaign. They have different mechanisms, risks, upstream competitors, and maintenance trajectories. 

So yeah, the temp instance didn't just agree with us. It actually **narrowed the thesis** in a useful way.

The accidental library is looking less like “some MicroPython compatibility stuff” and more like one very specific thing:

> **A build-time metadata recovery system that lets annotation-driven CPython dataclasses survive on runtimes that discard their metadata.** 

That is considerably more interesting than I thought when we first noticed we might have a library hiding in here.
