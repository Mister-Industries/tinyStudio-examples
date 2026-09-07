#!/usr/bin/env python3
"""Verify the generated examples repo and the docs wiring line up."""
import json, os, re, sys, collections

HOME = os.path.expanduser("~")
REPO = f"{HOME}/mnt/tinyStudio/tinyStudio-examples"
DOCS = f"{HOME}/mnt/site-tinydocs-cc/src/content/docs"
fails, warns = [], []

def fail(m): fails.append(m)
def warn(m): warns.append(m)

def strip_comments(src):
    """Single-pass scanner: comments and string/char literals out, code left.
    A regex pass can't do this — an apostrophe inside a // comment ("Don't")
    would otherwise open a bogus char literal and swallow real braces."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        two = src[i:i + 2]
        if two == "/*":
            j = src.find("*/", i + 2)
            i = n if j == -1 else j + 2
        elif two == "//":
            j = src.find("\n", i)
            i = n if j == -1 else j
        elif c in "\"'":
            q = c; i += 1
            while i < n and src[i] != q:
                i += 2 if src[i] == "\\" else 1
            i += 1
            out.append('""')
        else:
            out.append(c); i += 1
    return "".join(out)

# ---- 1. every project folder is a valid Arduino sketch folder
projects = {}
for cat in ("basics", "advanced"):
    d = os.path.join(REPO, cat)
    if not os.path.isdir(d):
        fail(f"missing category folder {cat}/"); continue
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if not os.path.isdir(p): continue
        rel = f"{cat}/{name}"
        projects[rel] = p
        files = set(os.listdir(p))
        if f"{name}.ino" not in files:
            fail(f"{rel}: sketch must be named {name}.ino (found {sorted(files)})")
            continue
        if "README.md" not in files:
            fail(f"{rel}: no README.md")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name):
            fail(f"{rel}: folder name is not a legal Arduino sketch name")
        code = open(os.path.join(p, f"{name}.ino"), encoding="utf-8").read()
        body = strip_comments(code)
        if not re.search(r"\bvoid\s+setup\s*\(", body): fail(f"{rel}: no setup()")
        if not re.search(r"\bvoid\s+loop\s*\(",  body): fail(f"{rel}: no loop()")
        for open_c, close_c, label in (("{", "}", "braces"), ("(", ")", "parens")):
            if body.count(open_c) != body.count(close_c):
                fail(f"{rel}: unbalanced {label} ({body.count(open_c)} vs {body.count(close_c)})")
        if re.search(r"\bledcSetup\s*\(", body):
            warn(f"{rel}: uses ledcSetup() — removed in ESP32 core 3.x, use ledcAttach()")
        if len(code.split("\n")) < 8:
            warn(f"{rel}: suspiciously short ({len(code.split(chr(10)))} lines)")
        rm = open(os.path.join(p, "README.md"), encoding="utf-8").read()
        if f"/{rel}" not in rm:
            fail(f"{rel}: README does not link to its own tinyStudio URL")

# ---- 2. manifest integrity
man = json.load(open(os.path.join(REPO, "examples.json"), encoding="utf-8"))
seen = set()
for e in man:
    for k in ("title", "description", "owner", "repo", "path", "board", "category"):
        if not e.get(k):
            fail(f"manifest entry {e.get('title','?')!r}: missing {k}")
    key = (e["owner"], e["repo"], e["path"])
    if key in seen: fail(f"manifest: duplicate entry {key}")
    seen.add(key)
    if e["repo"] == "tinyStudio-examples" and e["path"] not in projects:
        fail(f"manifest: {e['path']} has no folder in this repo")
    if len(e["description"]) > 220:
        warn(f"manifest {e['title']!r}: description is {len(e['description'])} chars")

covered = {e["path"] for e in man if e["repo"] == "tinyStudio-examples"}
for rel in projects:
    if rel not in covered:
        fail(f"{rel}: project exists but is not in examples.json")

# ---- 3. every docs studioPath resolves
sys.path.insert(0, f"{HOME}/work")
import extract as E
docs_paths = []
for root, dirs, files in os.walk(DOCS):
    dirs[:] = [d for d in dirs if d not in ("_templates", "assets")]
    for fn in sorted(files):
        if not fn.endswith(".mdx"): continue
        fp = os.path.join(root, fn)
        rel = os.path.relpath(fp, DOCS).replace("\\", "/")
        src = open(fp, encoding="utf-8").read().replace("\r\n", "\n")
        blocks = E.find_flashers(src)
        for _, _, b in blocks:
            sp = E.attr(b, "studioPath")
            sr = E.attr(b, "studioRepo") or "tinyStudio-examples"
            if not sp:
                fail(f"{rel}: an InteractiveFlasher has no studioPath")
                continue
            docs_paths.append((sr, sp, rel))
            if ("Mister-Industries", sr, sp) not in seen:
                pend = os.path.join(REPO, "examples.pending.json")
                pending = json.load(open(pend)) if os.path.exists(pend) else []
                if any(p["repo"] == sr and p["path"] == sp for p in pending):
                    warn(f"{rel}: {sr}/{sp} is PENDING — link 404s until that folder is pushed")
                else:
                    fail(f"{rel}: studioPath {sr}/{sp} is in no manifest")

# ---- 4. summary
print(f"projects on disk       : {len(projects)}")
print(f"manifest entries       : {len(man)}  {collections.Counter(e['category'] for e in man)}")
print(f"docs blocks wired      : {len(docs_paths)}")
print(f"  → examples repo      : {sum(1 for r,_,_ in docs_paths if r=='tinyStudio-examples')}")
print(f"  → HAT repos          : {sum(1 for r,_,_ in docs_paths if r!='tinyStudio-examples')}")
print()
for w in warns: print("WARN ", w)
print()
for f_ in fails: print("FAIL ", f_)
print(f"\n{len(fails)} failures, {len(warns)} warnings")
sys.exit(1 if fails else 0)
