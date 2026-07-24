# AGENTS.md — BlackMamba Agent Engineering Rules

This file defines mandatory engineering behavior for any human, coding agent, local model, automation, or external tool working in this repository.

These rules are architectural constraints, not suggestions.

---

## 1. Current Mission

The current project target is **BlackMamba Agent v0.1 — Text Song Registry**.

The only product objective for v0.1 is:

> Read supported text sources and build a trustworthy, deterministic canonical registry of songs and lyrics without modifying original source files.

Do not broaden scope unless the roadmap explicitly advances to a later phase.

---

## 2. Golden Rule

```text
IDENTITY FIRST.
INTELLIGENCE LATER.
```

The canonical registry is the source of truth for internal BlackMamba identities.

AI output, filenames, platform IDs, file locations, and display metadata must never silently redefine canonical identity.

---

## 3. v0.1 Scope

Allowed inputs:

```text
.txt
.md
plain text
```

Allowed responsibilities:

```text
read
parse
validate
fingerprint
assign canonical IDs
index
list
search
inspect
report errors
```

Forbidden v0.1 responsibilities:

```text
audio analysis
image processing
web automation
Spotify integration
SoundCloud integration
distribution automation
lyrics generation
lyrics rewriting
semantic interpretation
recommendation systems
LLM dependency
cloud API dependency
autonomous destructive actions
```

Do not add future-phase functionality merely because it is easy to implement.

---

## 4. Source Preservation

All user source files are read-only inputs.

Mandatory invariant:

```text
sourcePreserved = true
```

The indexing pipeline MUST NOT:

- overwrite source files
- truncate source files
- rename source files
- move source files
- delete source files
- normalize source files in place
- rewrite lyrics in place
- repair spelling in place
- alter line endings in place
- alter file metadata intentionally

Derived data belongs in the registry or explicitly generated output locations.

Never use a source file itself as mutable application state.

---

## 5. Canonical Identity

Initial namespaces:

```text
bm_song_XXXXXX
bm_lyrics_XXXXXX
```

Example:

```text
bm_song_000001
bm_lyrics_000001
```

Requirements:

1. IDs are unique within their namespace.
2. IDs are stable after assignment.
3. IDs are not derived solely from filenames.
4. Renaming a source file must not automatically create a new song identity.
5. External IDs do not replace canonical IDs.
6. Missing metadata does not justify inventing identity-bearing information.
7. Existing IDs must survive future schema migrations.

Never recycle an ID for another object.

---

## 6. Song and Lyrics Are Separate Objects

A song and its lyrics are related but conceptually distinct.

Do not collapse:

```text
song_id == lyrics_id
```

Instead maintain explicit relationships:

```text
bm_song_000001
    └── lyrics -> bm_lyrics_000001
```

This separation is required for future alternate lyrics, edits, translations, instrumentals, masters, and releases.

---

## 7. Missing Data Policy

Never invent missing metadata.

Parser state should explicitly distinguish:

```text
known
missing
invalid
ambiguous
```

Examples:

- Unknown artist -> store missing artist state.
- Missing title -> report missing title.
- Ambiguous duplicate -> report conflict.
- Unreadable encoding -> report read failure.

Do not guess merely to make a record pass validation.

---

## 8. Duplicate Policy

Duplicate detection may use signals such as:

```text
source path
content hash
lyrics hash
normalized title
artist metadata
```

However:

> Detection is not authorization to merge.

Automatic merge is forbidden when identity is ambiguous.

Safe outcomes:

```text
exact duplicate -> report existing canonical object
probable duplicate -> flag for review
ambiguous match -> do not merge
new object -> allocate identity
```

Prefer false-positive warnings over destructive consolidation.

---

## 9. Determinism

Behavior that affects persisted registry state must be deterministic and testable.

Given equivalent input and equivalent registry state, the system must produce equivalent persisted results.

Required properties include:

- stable serialization
- explicit schema version
- deterministic validation
- deterministic ID allocation rules
- reproducible fingerprints
- stable ordering where ordering is serialized

Do not depend on random UUIDs for v0.1 canonical IDs unless the architecture is explicitly revised.

Do not persist timestamps unless they serve a defined purpose and do not break deterministic snapshots/tests.

---

## 10. Registry Rules

Initial persistence backend:

```text
data/registry.json
```

The registry must include:

```text
schema_version
songs
```

Registry writes must be atomic enough to avoid leaving partially written state.

Before replacing registry state:

1. Build new state in memory.
2. Validate it.
3. Serialize deterministically.
4. Write safely.

Never silently discard a valid existing record because a new import failed.

---

## 11. Reader Contract

The text reader is intentionally dumb.

Reader responsibilities:

```text
path -> validated text content
```

It may:

- validate supported extension
- read bytes/text
- handle defined encodings
- report failures

It must NOT:

- infer title
- infer artist
- classify lyrics
- rewrite text
- assign IDs
- mutate registry state

Keep I/O separate from interpretation.

---

## 12. Parser Contract

The parser converts text into structured candidate metadata.

It may extract:

```text
title
artist
lyrics
```

It must return explicit uncertainty rather than fabricating values.

The parser must not:

- write files
- assign canonical IDs
- mutate the registry
- merge records
- modify original text

Parsing and persistence must remain separable.

---

## 13. Registry Contract

The registry layer owns canonical identity and persistence behavior.

Core operations:

```text
add
get
list
search
validate
```

The registry must enforce:

- unique IDs
- valid relationships
- schema validity
- duplicate policy
- canonical identity immutability

---

## 14. CLI Contract

The CLI is an interface, not the domain model.

Target commands:

```bash
bm-agent scan <path>
bm-agent list
bm-agent show <song_id>
bm-agent search <query>
bm-agent validate
```

CLI code should call domain functions rather than contain registry logic itself.

Commands must return non-zero exit codes for actual failures where appropriate.

Error output should identify the failing source without exposing unrelated data.

---

## 15. Testing Requirements

No core registry behavior is considered complete without tests.

Required test areas:

```text
text reader
parser
canonical identity
registry persistence
duplicate detection
deterministic serialization
source preservation
CLI behavior
failure handling
```

Critical source invariant test:

```python
before = source.read_bytes()
index(source)
after = source.read_bytes()
assert before == after
```

Critical determinism concept:

```text
same input + same state -> same registry representation
```

Regression tests should be added whenever a bug could affect identity, source preservation, or registry integrity.

---

## 16. Engineering Style

Prefer small modules with explicit responsibilities.

Target separation:

```text
reader -> parser -> validation -> identity -> registry -> CLI
```

Avoid:

- giant orchestration modules
- hidden global mutable state
- implicit filesystem side effects
- business logic inside CLI formatting
- network dependencies for core operation
- premature plugin systems
- premature abstractions with no current use

Implement the smallest complete architecture that preserves future extension points.

---

## 17. Dependencies

v0.1 should prefer the Python standard library where practical.

A dependency is justified only when it provides substantial correctness or maintainability value.

Do not introduce:

- LLM SDKs
- cloud clients
- database servers
- web frameworks
- background queues
- distributed systems

for v0.1.

The core registry must function offline.

---

## 18. Security and Destructive Actions

Read-only operations may be automated.

Destructive or irreversible behavior requires an explicit future design and user confirmation boundary.

Examples requiring protection:

```text
delete
source overwrite
mass rename
mass move
git force push
publishing
distribution
credential use
remote destructive actions
```

No v0.1 command should need destructive access to source material.

---

## 19. Git Discipline

Keep commits focused.

Preferred commit examples:

```text
docs: define canonical registry architecture
feat(reader): add read-only UTF-8 text reader
feat(registry): add canonical song identity allocation
test(registry): verify deterministic serialization
fix(parser): preserve lyrics whitespace exactly
```

Do not mix unrelated future-roadmap work into a v0.1 commit.

Before committing code, run relevant tests.

---

## 20. Architecture Change Rule

Changes to any of these require deliberate review:

```text
canonical ID format
identity semantics
source preservation rules
registry schema meaning
duplicate merge behavior
song/lyrics separation
serialization determinism
```

Do not casually change these because they affect long-lived catalog identity.

Prefer additive migrations over destructive schema replacement.

---

## 21. Definition of Done — v0.1

v0.1 is not complete because a demo works.

It is complete when the implementation can satisfy the following target:

```text
1000 text sources
      ↓
read without modifying originals
      ↓
parsed into explicit candidate records
      ↓
validated
      ↓
assigned stable canonical identities
      ↓
persisted deterministically
      ↓
searchable and inspectable
      ↓
0 source mutations
```

Correctness and recoverability outrank speed.

---

## 22. Final Constraint

When uncertain about a design choice, choose the option that best preserves:

```text
1. original source data
2. canonical identity
3. deterministic behavior
4. traceability
5. future compatibility
```

The agent may become intelligent later.

The catalog must become trustworthy first.
