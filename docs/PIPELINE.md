# The examples pipeline

How code written on **tinyDocs** becomes a project you can open in **tinyStudio**
and a binary you can flash from the browser — and how all three stay in sync.

```
tinyDocs (.mdx)              tinyStudio-examples                consumers
───────────────              ───────────────────                ─────────
<InteractiveFlasher          basics/<name>/<name>.ino     ──►   tinyStudio
  code={`…`}          ──►    basics/<name>/README.md            (Examples tab,
  studioPath="…"             firmware/basics/<name>/             deep links)
  firmwarePath="…" />          firmware.bin
        ▲                      manifest.json          ──►      the Flash button
        │                    examples.json                     on the docs page
        └──── pencil button links back to the source ──────────────┘
```

The docs page is the **source of truth**. Everything in `basics/`, `advanced/`
and `firmware/` is generated from it; a hand edit to a `.ino` here is erased on
the next build. Fix the docs, rebuild.

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
| `tinyStudio-examples` (this one) | `basics/`, `advanced/`, `firmware/`, `examples.json` | Generated from tinyDocs. Keeps churn out of the IDE repo, and keeps code and binaries in one place. |
| `tinySniff`, `tinySpeak` | `Software/Arduino/Examples/<Name>/<Name>.ino` | Board code belongs with the board. Already in the layout tinyStudio loads — **linked, never copied.** |
| `tinyStudio` | `demo/` | The three demos with `diagram.json` + `visual.js`, which exercise the Circuit and Visual views. |

`examples.json` here is the single manifest covering all three. HAT *sources*
stay in the HAT repos; HAT *firmware* is built here under `firmware/hats/`,
because that is the one place the flasher looks.

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

## 4. Firmware

Sources are only half of it — every example is also compiled to a flashable
image so a reader never has to install anything. That half has its own
document: **[FIRMWARE.md](FIRMWARE.md)**. In short, `tools/build-firmware.py`
turns each sketch into `firmware/<category>/<name>/{firmware.bin,manifest.json}`,
and a docs block points at it with `firmwarePath`.

## 5. The two buttons on a docs code block

`InteractiveFlasher` (in the docs repo) takes:

| Prop | Default | Meaning |
|---|---|---|
| `studioPath` | — | Repo-relative project path. **No path, no pencil button.** |
| `studioRepo` | `tinyStudio-examples` | For HAT blocks, e.g. `tinySpeak`. |
| `studioOwner` | `Mister-Industries` | Escape hatch for forks. |
| `studioUrl` | — | Full URL override; wins over the other three. |
| `firmwarePath` | — | Path under `firmware/` here, e.g. `hats/tinySpeak/tinyTheremin`. |
| `manifestPath` | — | Legacy: a manifest served from the docs site itself. |

The green **Edit in tinyStudio** button opens
`https://app.tinystudio.cc/<owner>/<repo>/<path>` (each segment encoded
separately, so folder names with spaces still resolve). The orange **Flash
tinyCore** button reads `${FIRMWARE_BASE}/<firmwarePath>/manifest.json`.

## 6. Rebuilding

```bash
python3 tools/extract-blocks.py       # parse every code block out of the docs
python3 tools/build-examples.py       # write basics/ + advanced/ projects
python3 tools/build-manifest.py       # link the HATs, write examples.json
python3 tools/inject-docs-links.py    # write studioPath + firmwarePath into the .mdx
python3 tools/verify.py               # check the whole thing lines up
python3 tools/build-firmware.py       # compile every sketch to a flashable image
```

The scripts expect both repos checked out side by side; paths are constants at
the top of each file.

### What the extractor takes

- Every `<InteractiveFlasher>` `code={`…`}` block.
- Every fenced ```` ```cpp ```` block that is a **complete sketch** — it defines
  both `setup()` and `loop()`.
- A `loop()`-only flasher (the docs' "replace your `loop()` with this" pattern)
  is grafted onto the preceding complete sketch on the same page, so it becomes
  a project that actually runs.

It skips fragments — a three-line API snippet or a bare `loop()` body with no
parent sketch can't compile alone.

**Escapes matter.** The code lives in a JS template literal, so a C++ `\r\n` has
to be typed `\\r\\n` in the .mdx and a C++ `\"` as `\\"`. The extractor decodes
those the way JavaScript does, which is exactly what the page displays and what
its Copy button hands out. Two blocks had been pasted in raw and were shipping
broken code to readers; `tools/oneoff-fix-template-escapes.py` is the fix that
was applied, kept here as a reference for diagnosing the same symptom again
(errors like *unable to find string literal operator*, or a `printf` string that
suddenly spans two lines).

### Naming

`<page topic>-<section heading>`, stopwords dropped, capped at four words from
the heading, with an override table in `build-examples.py` for the cases where
the docs heading reads badly as a folder name. Names are stable: rerunning
produces the same folders, so links don't rot.

### Verification

`tools/verify.py` fails the build if any project isn't a legal Arduino sketch
folder, has unbalanced braces, lacks `setup()`/`loop()`, is missing from the
manifest, or is referenced by a `studioPath` that resolves nowhere.

## 7. Keeping the HAT repos honest

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
