#!/usr/bin/env python3
"""
Escape two sketches that were pasted into the docs without escaping.

Inside code={`...`} the text is a JS template literal, so a backslash has to be
written twice for one to survive. Two blocks were pasted raw:

  motion-tracker.mdx           Motion-Tracker.ino   16 escaped JSON quotes
  tinyspeak/example-code.mdx   tinyWebSynth         newlines, quotes, unicode

The page therefore renders (and its Copy button hands out) code where
the JSON quote escapes vanish and every printf newline becomes a real line
break inside the string literal. Neither compiles. Every other
flasher block in the docs is correctly double-escaped, so this just brings
these two in line.
"""
import os, sys
sys.path.insert(0, os.path.expanduser("~/work"))
import extract as E

DOCS = os.path.expanduser("~/mnt/site-tinydocs-cc/src/content/docs")
TARGETS = [("1_get-started/motion-tracker.mdx", "Motion-Tracker.ino"),
           ("3_tiny-hats/tinyspeak/example-code.mdx", "tinyWebSynth")]

for rel, title in TARGETS:
    path = os.path.join(DOCS, rel)
    raw = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    src = raw.replace("\r\n", "\n")

    edits = []
    for start, end, block in E.find_flashers(src):
        if (E.attr(block, "title") or "") != title:
            continue
        code = E.attr(block, "code")
        if code is None:
            continue
        if "\\\\" in code:
            print(f"{rel} [{title}]: already contains escaped backslashes — skipping")
            continue
        if "`" in code or "${" in code:
            print(f"{rel} [{title}]: contains a backtick or ${{ — needs a human")
            continue
        edits.append((start, end, block, code, code.replace("\\", "\\\\")))

    if not edits:
        print(f"{rel} [{title}]: nothing to do")
        continue
    for start, end, block, old, new in reversed(edits):
        src = src[:start] + block.replace(old, new, 1) + src[end:]
    open(path, "w", encoding="utf-8", newline="").write(
        src.replace("\n", nl) if nl == "\r\n" else src)
    n = sum(e[3].count("\\") for e in edits)
    print(f"{rel} [{title}]: escaped {n} backslashes")
