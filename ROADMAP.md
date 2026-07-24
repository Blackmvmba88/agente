# BlackMamba Agent — Roadmap

## Development Strategy

BlackMamba Agent will evolve incrementally.

Each phase must remain usable independently.

No phase may invalidate canonical identities created by previous versions.

---

# Phase 0 — Foundation

Status: NEXT

Goal:

Establish repository architecture, invariants, schemas, and tests before processing the catalog.

Deliverables:

- README.md
- ROADMAP.md
- AGENTS.md
- source directory
- test directory
- registry schema
- canonical ID specification
- deterministic serialization rules

Exit condition:

Architecture is documented and testable.

---

# Phase 1 — Text Registry

Target: v0.1

Goal:

Convert text sources into canonical song records.

## 1.1 Text Reader

Implement:

```text
.txt
.md
plain text
```

Reader responsibilities:

- open file
- validate encoding
- return text
- preserve source
- report read errors

Reader MUST NOT interpret content.

---

## 1.2 Song Parser

Extract:

```text
title
artist
lyrics
```

Parser output must distinguish:

```text
known
missing
invalid
```

Missing metadata must not be invented.

---

## 1.3 Canonical IDs

Implement:

```text
bm_song_XXXXXX
bm_lyrics_XXXXXX
```

Requirements:

- stable
- unique
- deterministic allocation behavior
- collision detection
- immutable after assignment

---

## 1.4 Registry

Implement persistent registry.

Initial backend:

```text
JSON
```

Required operations:

```text
add
get
list
search
validate
```

Registry includes:

```text
schema_version
songs
```

Serialization must be deterministic.

---

## 1.5 Duplicate Detection

Prevent accidental duplicate indexing.

Initial signals may include:

```text
source path
content fingerprint
normalized title
lyrics fingerprint
```

Duplicate detection must NOT automatically merge ambiguous records.

Ambiguity must be reported.

---

## 1.6 CLI

Implement:

```bash
bm-agent scan
bm-agent list
bm-agent show
bm-agent search
bm-agent validate
```

CLI must remain usable without graphical interfaces.

---

## 1.7 Tests

Minimum test categories:

```text
reader
parser
identity
registry
duplicates
serialization
source preservation
CLI
```

Critical invariant:

```text
index(source)

assert source_before == source_after
```

---

# Milestone v0.1

Target:

```text
1000 text sources
→ indexed
→ canonical IDs
→ searchable
→ reproducible
→ zero source mutation
```

---

# Phase 2 — Catalog Integrity

Target: v0.2

Goal:

Make the registry resilient enough to become the authoritative catalog index.

Add:

- schema migrations
- stronger fingerprints
- conflict reporting
- duplicate review
- import reports
- failed-import reports
- registry backups
- integrity checks

Commands:

```bash
bm-agent doctor
bm-agent duplicates
bm-agent conflicts
bm-agent stats
```

No AI required.

---

# Phase 3 — Relationships

Target: v0.3

Goal:

Move from a flat song list to a graph of related music assets.

Introduce identities:

```text
bm_song_
bm_lyrics_
bm_audio_
bm_artwork_
bm_release_
```

Relationship example:

```text
bm_song_000001
 │
 ├── lyrics → bm_lyrics_000001
 ├── audio → bm_audio_000001
 ├── artwork → bm_artwork_000001
 └── release → bm_release_000001
```

The song remains the canonical root object.

---

# Phase 4 — Audio Catalog

Target: v0.4

Goal:

Index audio without changing original files.

Extract technical metadata only.

Possible fields:

```text
path
format
sample_rate
channels
duration
frames
file_size
fingerprint
```

Audio processing remains read-only.

No automatic musical interpretation is required.

---

# Phase 5 — Release Registry

Target: v0.5

Goal:

Represent published and planned releases.

Add:

```text
release_id
release_title
release_type
release_date
track_order
ISRC
UPC
platform_ids
distribution_status
```

External IDs remain metadata.

They never replace BlackMamba canonical identity.

---

# Phase 6 — Search Engine

Target: v0.6

Goal:

Provide fast catalog-wide retrieval.

Examples:

```bash
bm-agent find "Welcome to Dubai"
bm-agent lyrics bm_song_000001
bm-agent releases bm_song_000001
```

Potential backend migration:

```text
JSON
 ↓
SQLite
```

JSON export remains available for portability.

---

# Phase 7 — Local Agent

Target: v0.7+

Only after the catalog infrastructure is reliable.

Goal:

Allow a local model to reason over BlackMamba's structured catalog.

Architecture:

```text
                 USER
                   │
                   ▼
            BLACKMAMBA AGENT
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
       SEARCH    TOOLS    MEMORY
          │        │        │
          └────────┼────────┘
                   ▼
             CANONICAL DB
```

Potential local inference:

```text
Ollama
llama.cpp
other local runtimes
```

Cloud inference is not required.

---

# Phase 8 — Tool Execution

The agent may eventually receive controlled tools.

Read-only tools first:

```text
catalog.search
catalog.get
filesystem.read
git.status
git.diff
```

Mutation tools later:

```text
filesystem.write
catalog.update
git.commit
```

Destructive operations remain protected.

---

# Phase 9 — BlackMamba Music OS

Long-term direction.

```text
                         BLACKMAMBA CORE
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
           CATALOG            AUDIO            RELEASE
              │                 │                 │
        lyrics/assets       editor/deck      distribution
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                           ANALYTICS
                                │
                                ▼
                         LOCAL AGENT
```

The agent does not become the source of truth.

The catalog does.

---

# Non-Negotiable Invariants

Throughout every phase:

```text
canonical identity > filename
source data > generated assumptions
read operations != mutation operations
missing data != invented data
external platform ID != canonical ID
automation != uncontrolled destruction
```

And most importantly:

```text
ORIGINAL SOURCE FILES ARE PRESERVED.
```

---

# Immediate Next Milestone

Build v0.1 only.

Do not prematurely implement:

- local LLM
- web automation
- Spotify integration
- SoundCloud integration
- audio analysis
- image processing
- recommendation systems
- autonomous execution

First objective:

> Build a trustworthy map of the catalog.

Once BlackMamba Agent knows exactly what exists, everything else can be built on top of it.
