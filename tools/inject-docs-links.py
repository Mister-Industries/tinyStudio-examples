#!/usr/bin/env python3
"""
Add studioPath / studioOwner / studioRepo to every <InteractiveFlasher> in the
tinyDocs .mdx content, so each smart code block's green pencil button opens the
matching real project in tinyStudio.

Idempotent: an existing studio* attribute on a block is replaced, not appended.
"""
import json, os, re, sys, collections
HOME = os.path.expanduser("~")
sys.path.insert(0, f"{HOME}/work")
import generate as G
import finish as F
import extract as E

DOCS = os.path.expanduser("~/mnt/site-tinydocs-cc/src/content/docs")

def build_map():
    """(file, nth flasher in that file) -> (owner, repo, path)"""
    items = F.load_blocks()
    per_file = collections.defaultdict(list)
    for i in sorted(items, key=lambda x: (x["file"], x["pos"])):
        if i["kind"] == "flasher":
            per_file[i["file"]].append(i)

    # replay the exact naming the generator used, for the non-HAT blocks
    used, names = collections.Counter(), {}
    for i in sorted(items, key=lambda x: (x["file"], x["pos"])):
        if not i["complete"] or G.category(i["file"]) == "hat":
            continue
        n = G.target_name(i)
        used[n] += 1
        if used[n] > 1:
            n = f"{n}-{used[n]}"
        names[(i["file"], i["pos"])] = (G.category(i["file"]), n)

    out = {}
    for f, blocks in per_file.items():
        for idx, i in enumerate(blocks):
            if G.category(f) == "hat":
                key = (i.get("title") or "").strip()
                if key not in F.HAT_MAP:
                    continue
                repo, folder = F.HAT_MAP[key]
                out[(f, idx)] = (G.OWNER, repo, f"{F.HAT_ROOT}/{folder}")
            else:
                hit = names.get((i["file"], i["pos"]))
                if not hit:
                    continue
                cat, n = hit
                out[(f, idx)] = (G.OWNER, G.EX_REPO, f"{cat}/{n}")
    return out

ATTR = re.compile(r'\s+studio(?:Path|Owner|Repo|Url)\s*=\s*"[^"]*"')

def main():
    mapping = build_map()
    touched = added = skipped = 0
    for root, dirs, files in os.walk(DOCS):
        dirs[:] = [d for d in dirs if d not in ("_templates", "assets")]
        for fn in sorted(files):
            if not fn.endswith(".mdx"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            raw = open(path, encoding="utf-8", newline="").read()
            nl = "\r\n" if "\r\n" in raw else "\n"
            src = raw.replace("\r\n", "\n")

            spans = E.find_flashers(src)
            if not spans:
                continue
            # rewrite back-to-front so earlier offsets stay valid
            new = src
            for idx in range(len(spans) - 1, -1, -1):
                start, end, block = spans[idx]
                hit = mapping.get((rel, idx))
                if not hit:
                    skipped += 1
                    continue
                owner, repo, p = hit
                clean = ATTR.sub("", block)
                attrs = f'\n  studioPath="{p}"'
                if repo != G.EX_REPO:
                    attrs += f'\n  studioRepo="{repo}"'
                if owner != G.OWNER:
                    attrs += f'\n  studioOwner="{owner}"'
                # insert right after the component name
                patched = clean.replace("<InteractiveFlasher", "<InteractiveFlasher" + attrs, 1)
                new = new[:start] + patched + new[end:]
                added += 1
            if new != src:
                open(path, "w", encoding="utf-8", newline="").write(
                    new.replace("\n", nl) if nl == "\r\n" else new)
                touched += 1
    print(f"files touched: {touched}   blocks wired: {added}   blocks with no project: {skipped}")

if __name__ == "__main__":
    main()
