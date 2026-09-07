# The examples pipeline

How code written on **tinyDocs** becomes a project you can open in
**tinyStudio**, and how the two stay in sync.

```
tinyDocs (.mdx)                tinyStudio-examples              tinyStudio
─────────────────              ───────────────────              ──────────
<InteractiveFlasher            basics/<name>/<name>.ino         Examples tab
  code={`…`}          ──►      basics/<name>/README.md    ──►   reads examples.json
  studioPath="…" />            examples.json                    /<owner>/<repo>/<path>
        ▲                                                              │
        └──────────── green pencil button links straight here ─────────┘
```

The docs page is the **source of truth**. Everything in `basics/` and
`advanced/` is generated from it; a hand edit to a `.ino` here is erased on the
next build. Fix the docs, rebuild.

---

## 1. Why this shape

tinyStudio can already open any folder of a public GitHub repo:

- `src/renderer/src/lib/projectRouting.ts` parses `/<owner>/<repo>/<path>` off
  `window.location` and calls `LoadGitHubProjectCommand`.
- `src/renderer/src/lib/github.ts` → `fetchRepoFolder()` pulls that folder as a
  flat `{ relpath: content }` map from `raw.githubusercontent.com`.
- On desktop the project is materialized into *Documents/tinyStudio Examples/
  &lt;folder&gt;* so `arduino-cli` can compile it from a real path; in the browser
  it opens as an in-memory `mem://` workspace.

Two consequences shape the layout:

1. **The folder name becomes the sketch folder name.** `arduino-cli` requires
   the folder and the `.ino` to share a name, so every project here is
   `<name>/<name>.ino`.
2. **`owner`/`repo`/`path` are per manifest entry**, so one manifest can span
   many repos. That's what lets the tinyHATs stay in their own repos.

## 2. Repos, and what lives where

| Repo | Holds | Why |
|---|---|---|
| `tinyStudio-examples` (this one) | `basics/`, `advanced/`, `examples.json` | Generated from tinyDocs. Keeps churn out of the IDE repo. |
| `tinySniff`, `tinySpeak` | `Software/Arduino/Examples/<Name>/<Name>.ino` | Board code belongs with the board. Already in the layout tinyStudio loads — **linked, never copied.** |
| `tinyStudio` | `demo/` | The three demos with `diagram.json` + `visual.js`, which exercise the Circuit and Visual views. |

`examples.json` here is the single manifest covering all three.

## 3. Manifest

```jsonc
{
  "title":       "Basic Blink Program",
  "description": "…one sentence, from the docs prose or the sketch banner…",
  "owner":       "Mister-Industries",
  "repo":        "tinyStudio-examples",   // or tinySniff / tinySpeak / tinyStudio
  "path":        "basics/blink-basic",
  "board":       "tinyCore (ESP32-S3)",
  "category":    "basics",                // demos | basics | advanced | hats
  "docsUrl":     "https://tinydocs.cc/2_tiny-core/basics/blink-led/"
}
```

`category` and `docsUrl` are additions — the Examples tab groups by `category`
and puts a **Docs** button on each card. Older builds ignore both.

tinyStudio reads the manifest from this repo first and falls back to
`tinyStudio/main/examples.json`, so nothing breaks if this repo is briefly
unreachable. `localStorage["tinystudio.examples.url"]` overrides both for
testing a fork or branch.

## 4. The green pencil button

`InteractiveFlasher` (in the docs repo) gained four optional props:

| Prop | Default | Meaning |
|---|---|---|
| `studioPath` | — | Repo-relative project path. **No path, no button.** |
| `studioRepo` | `tinyStudio-examples` | For HAT blocks, e.g. `tinySpeak`. |
| `studioOwner` | `Mister-Industries` | Escape hatch for forks. |
| `studioUrl` | — | Full URL override; wins over the other three. |

It renders a green **Edit in tinyStudio** button beside Copy and Flash, opening
`https://app.tinystudio.cc/<owner>/<repo>/<path>` in a new tab. Each path
segment is encoded separately so folder names with spaces still resolve.

## 5. Rebuilding

```bash
python3 tools/extract-blocks.py       # parse every code block out of the docs
python3 tools/build-examples.py       # write basics/ + advanced/ projects
python3 tools/build-manifest.py       # link the HATs, write examples.json
python3 tools/inject-docs-links.py    # write studioPath back into the .mdx
python3 tools/verify.py               # check the whole thing lines up
```

The scripts expect both repos checked out side by side; the paths are constants
at the top of each file.

### What the extractor takes

- Every `<InteractiveFlasher>` `code={\`…\`}` block.
- Every fenced ```` ```cpp ```` block that is a **complete sketch** — it defines
  both `setup()` and `loop()`.
- A `loop()`-only flasher (the docs' "replace your `loop()` with this" pattern)
  is grafted onto the preceding complete sketch on the same page, so it becomes
  a project that actually runs.

It skips fragments — a three-line API snippet or a bare `loop()` body with no
parent sketch can't compile alone, and shipping it as a project would only
produce a broken Verify.

### Naming

`<page topic>-<section heading>`, stopwords dropped, capped at four words from
the heading, with an override table in `build-examples.py` for the cases where
the docs heading reads badly as a folder name. Names are stable: rerunning
produces the same folders, so links don't rot.

### Verification

`tools/verify.py` fails the build if any project isn't a legal Arduino sketch
folder, has unbalanced braces, lacks `setup()`/`loop()`, is missing from the
manifest, or is referenced by a `studioPath` that resolves nowhere. It warns on
sketches using `ledcSetup()`, which the ESP32 core dropped in 3.0.7.

## 6. Keeping the HAT repos honest

`_hat-updates/` mirrors each HAT repo's layout and holds the **docs-current**
version of every HAT sketch. Copy it over a HAT checkout and `git diff` shows
exactly where the published docs and the board repo have drifted:

```bash
cp -r _hat-updates/tinySniff/. ../tinySniff/
cd ../tinySniff && git diff
```

Anything in `examples.pending.json` is a manifest entry whose folder isn't on
the HAT repo yet — its docs link 404s until you push. Move entries from
`examples.pending.json` into `examples.json` once the folder is live.
