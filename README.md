# BlackMamba Agent

Local-first music catalog and automation system for BlackMamba Records.

BlackMamba Agent begins with one deliberately narrow responsibility:

> Read text files and build a deterministic canonical registry of songs.

The first version does not generate music, interpret lyrics, modify source files, or require an AI model.

The foundation is identity, traceability, and reproducibility.

---

## 1. Core Principle

> Identity first. Intelligence later.

Before an agent can reason about a music catalog, it must know exactly what exists.

Every song receives a stable canonical identity independent from filename, folder, title changes, platform, distribution service, or future metadata.

Example:

```json
{
  "song_id": "bm_song_000001",
  "title": "Welcome to Dubai",
  "artist": "Iyari Gomez",
  "lyrics_id": "bm_lyrics_000001",
  "lyrics": "...",
  "source": "text",
  "status": "indexed"
}
```

`bm_song_000001` remains the same song even if its filename or metadata changes.

---

## 2. v0.1 — Song Registry

The first milestone accepts text and produces a canonical song registry.

### Accepted input

- `.txt`
- `.md`
- plain text

### Extracted fields

Minimum canonical fields:

- `song_id`
- `title`
- `artist`
- `lyrics_id`
- `lyrics`
- `source`
- `status`

Additional metadata may be added later without changing canonical identity.

---

## 3. Pipeline

```text
TEXT SOURCE
    │
    ▼
TEXT READER
    │
    ▼
SONG PARSER
    │
    ▼
VALIDATION
    │
    ▼
IDENTITY ASSIGNMENT
    │
    ▼
CANONICAL REGISTRY
```

The pipeline must remain deterministic.

The same valid source processed under the same registry state must not silently create a second identity for the same indexed object.

---

## 4. Repository Structure

```text
agente/
├── README.md
├── ROADMAP.md
├── AGENTS.md
├── src/
│   ├── reader/
│   │   └── text_reader.py
│   ├── parser/
│   │   └── song_parser.py
│   ├── registry/
│   │   ├── song.py
│   │   └── registry.py
│   └── cli.py
├── data/
│   ├── songs/
│   └── registry.json
└── tests/
```

---

## 5. Canonical Identity

Two identities are initially maintained.

### Song ID

```text
bm_song_000001
bm_song_000002
bm_song_000003
```

Represents the musical work inside BlackMamba Agent.

### Lyrics ID

```text
bm_lyrics_000001
bm_lyrics_000002
bm_lyrics_000003
```

Represents a specific lyrics object.

Song identity and lyrics identity MUST remain separate.

This allows future relationships such as:

```text
bm_song_000001
├── bm_lyrics_000001
├── bm_audio_000001
├── bm_artwork_000001
├── bm_release_000001
└── external platform identities
```

---

## 6. Source Preservation

Original source files are immutable from the perspective of the indexing pipeline.

BlackMamba Agent v0.1 MUST NOT:

- overwrite source files
- rename source files
- move source files
- delete source files
- rewrite lyrics
- correct lyrics automatically

The registry describes the source.

It does not own the source.

---

## 7. v0.1 Boundaries

### The system DOES

- read text
- detect supported files
- extract song information
- assign canonical IDs
- validate records
- detect already-indexed material
- persist registry data
- retrieve records by ID
- list indexed songs

### The system DOES NOT

- analyze audio
- open images
- generate lyrics
- rewrite lyrics
- interpret lyrics
- publish music
- access distribution platforms
- require cloud AI
- require tokens or API credits

---

## 8. Registry

Initial persistence:

```text
data/registry.json
```

Example:

```json
{
  "schema_version": 1,
  "songs": [
    {
      "song_id": "bm_song_000001",
      "title": "Welcome to Dubai",
      "artist": "Iyari Gomez",
      "lyrics_id": "bm_lyrics_000001",
      "lyrics": "...",
      "source": {
        "type": "text",
        "path": "songs/welcome_to_dubai.txt"
      },
      "status": "indexed"
    }
  ]
}
```

The registry format must be deterministic and versioned.

Future migrations MUST preserve canonical IDs.

---

## 9. CLI Target

The system will initially be operated through a local CLI.

Target interface:

```bash
python -m src.cli scan ./songs
python -m src.cli list
python -m src.cli show bm_song_000001
python -m src.cli search "Dubai"
python -m src.cli validate
```

No graphical interface is required for v0.1.

---

## 10. Safety Invariants

```text
sourcePreserved = true
canonical identity > filename
read != modify
missing data != invented data
external platform ID != canonical ID
automation != uncontrolled destruction
```

Once assigned, an ID cannot silently represent another object.

Any future operation capable of modifying or deleting user data must be separated from read/index operations.

Registry serialization and identity behavior must be testable and reproducible.

---

## 11. Initial Success Criteria

v0.1 is considered successful when:

```text
1000 text files
      ↓
1000 correctly indexed song records
      ↓
stable canonical identities
      ↓
0 original files modified
      ↓
deterministic registry
```

Correctness is more important than intelligence.

---

## 12. Long-Term Model

```text
SONG
 │
 ├── LYRICS
 ├── AUDIO
 │    ├── source
 │    ├── mix
 │    └── master
 │
 ├── ARTWORK
 ├── RELEASE
 ├── DISTRIBUTION
 │    ├── Spotify
 │    ├── Apple Music
 │    ├── SoundCloud
 │    └── others
 │
 └── ANALYTICS
```

These systems are future extensions.

They must not compromise the simplicity or integrity of the canonical registry.

---

# Philosophy

BlackMamba Agent is not initially an AI chatbot.

It is infrastructure.

First it learns what exists.

Then it learns how those objects relate.

Only then does intelligence become useful.
