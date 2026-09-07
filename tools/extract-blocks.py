#!/usr/bin/env python3
"""Extract every Arduino code block out of the tinyDocs .mdx content."""
import json, os, re, sys, textwrap

DOCS = os.path.expanduser("~/mnt/site-tinydocs-cc/src/content/docs")

def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")

def frontmatter(src):
    m = re.match(r"^---\n(.*?)\n---\n", src, re.S)
    if not m: return {}, src
    fm = {}
    for line in m.group(1).split("\n"):
        mm = re.match(r'^(\w+):\s*"?(.*?)"?\s*$', line)
        if mm: fm[mm.group(1)] = mm.group(2)
    return fm, src

JS_ESC = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v",
          "0": "\0", "\\": "\\", "`": "`", "$": "$", "'": "'", '"': '"', "\n": ""}


def js_unescape(raw):
    """Turn the RAW text of a JS template literal into the string JS produces.

    The docs write sketches inside code={`...`}, so a C++ `\r\n` has to be typed
    as `\\r\\n` in the .mdx and a C++ `\"` as `\\"`. Copying the raw text into a
    .ino leaves the doubled backslashes in place, which the compiler reads as a
    literal backslash followed by r — hence errors like `unable to find string
    literal operator 'operator""file'`. Decoding the escapes here yields exactly
    what the page displays and what its Copy button puts on the clipboard.
    """
    out = []
    i, n = 0, len(raw)
    while i < n:
        c = raw[i]
        if c != "\\" or i + 1 >= n:
            out.append(c); i += 1; continue
        e = raw[i + 1]
        if e == "u":
            m = re.match(r"u\{([0-9a-fA-F]{1,6})\}|u([0-9a-fA-F]{4})", raw[i + 1:])
            if m:
                out.append(chr(int(m.group(1) or m.group(2), 16)))
                i += 1 + m.end(); continue
        elif e == "x":
            m = re.match(r"x([0-9a-fA-F]{2})", raw[i + 1:])
            if m:
                out.append(chr(int(m.group(1), 16)))
                i += 1 + m.end(); continue
        out.append(JS_ESC.get(e, e))
        i += 2
    return "".join(out)


def dedent(code):
    """Strip the block's common indent.

    The docs indent most sketches inside the JSX template literal, but often
    leave the first line (a `//` banner) flush left. A plain min() over all
    lines would then find 0 and dedent nothing, so an indent shared by the
    overwhelming majority of lines wins instead — lines already shallower than
    that are left where they are rather than being sliced into.
    """
    code = code.strip("\n")
    lines = code.split("\n")
    ind = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    if not ind:
        return code.rstrip() + "\n"
    base = min(ind)
    outliers = max(1, len(ind) // 10)
    if ind.count(base) <= outliers:
        deeper = [x for x in ind if x > base]
        if deeper:
            base = min(deeper)
    out = []
    for l in lines:
        if not l.strip():
            out.append("")
        elif len(l) - len(l.lstrip()) >= base:
            out.append(l[base:])
        else:
            out.append(l)
    return "\n".join(out).rstrip() + "\n"

def find_flashers(src):
    """Yield dicts for each <InteractiveFlasher .../> element."""
    out = []
    for m in re.finditer(r"<InteractiveFlasher\b", src):
        start = m.start()
        # scan forward to the closing '/>' at depth 0, respecting {} and backticks
        i = m.end(); depth = 0; n = len(src)
        while i < n:
            c = src[i]
            if c == "{":
                depth += 1; i += 1
                continue
            if c == "}":
                depth -= 1; i += 1
                continue
            if c == "`" and depth > 0:
                i += 1
                while i < n:
                    if src[i] == "\\": i += 2; continue
                    if src[i] == "`": break
                    i += 1
                i += 1
                continue
            if c == "/" and depth == 0 and src[i:i+2] == "/>":
                i += 2
                break
            i += 1
        block = src[start:i]
        out.append((start, i, block))
    return out

def attr(block, name):
    # string attr:  name="value"
    m = re.search(name + r'\s*=\s*"([^"]*)"', block)
    if m: return m.group(1)
    # brace attr with backtick template: name={`...`}
    m = re.search(name + r"\s*=\s*\{\s*`", block)
    if m:
        i = m.end(); n = len(block); buf = []
        while i < n:
            if block[i] == "\\":
                buf.append(block[i:i+2]); i += 2; continue
            if block[i] == "`": break
            buf.append(block[i]); i += 1
        return "".join(buf)
    # brace attr plain: name={value}
    m = re.search(name + r"\s*=\s*\{([^}`]*)\}", block)
    if m: return m.group(1).strip()
    return None

HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.M)

def heading_before(src, pos):
    best = None
    for m in HEADING.finditer(src, 0, pos):
        best = m
    return (best.group(2).strip() if best else None)

def heading_path(src, pos):
    """Ancestor headings (shallowest -> deepest) in effect at pos."""
    stack = []
    for m in HEADING.finditer(src, 0, pos):
        lvl = len(m.group(1)); txt = m.group(2).strip()
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        stack.append((lvl, txt))
    return [t for _, t in stack]

def prose_before(src, pos, max_chars=900):
    """Grab the prose paragraphs immediately preceding pos, minus JSX/fences."""
    chunk = src[max(0, pos - 2500):pos]
    # drop anything inside a prior JSX component or code fence
    chunk = re.sub(r"<InteractiveFlasher[\s\S]*?/>", "", chunk)
    chunk = re.sub(r"```[\s\S]*?```", "", chunk)
    lines = chunk.split("\n")
    kept = []
    for line in reversed(lines):
        s = line.strip()
        if not s:
            if kept: kept.append("")
            continue
        if s.startswith("#"):
            break
        if s.startswith(("import ", "export ", "<", "/>", ":::")):
            continue
        kept.append(line.rstrip())
        if sum(len(x) for x in kept) > max_chars:
            break
    text = "\n".join(reversed(kept)).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def prose_after(src, pos, max_chars=600):
    """Prose immediately following a block, up to the next heading/fence/component."""
    chunk = src[pos:pos + 2500]
    lines = chunk.split("\n")
    kept = []
    for line in lines:
        st = line.strip()
        if st.startswith("#") or st.startswith("```") or st.startswith("<Interactive"):
            break
        if st.startswith(("import ", "export ", ":::", "![", "|")):
            continue
        kept.append(line.rstrip())
        if sum(len(x) for x in kept) > max_chars:
            break
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept).strip())

def is_complete(code):
    return bool(re.search(r"\bvoid\s+setup\s*\(", code)) and bool(re.search(r"\bvoid\s+loop\s*\(", code))

def collect():
    items = []
    for root, dirs, files in os.walk(DOCS):
        dirs[:] = [d for d in dirs if d not in ("_templates", "assets")]
        for fn in sorted(files):
            if not fn.endswith(".mdx"): continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, DOCS).replace("\\", "/")
            src = read(path)
            fm, _ = frontmatter(src)
            page_title = fm.get("title", fn[:-4])

            for start, end, block in find_flashers(src):
                code = attr(block, "code")
                if not code: continue
                code = js_unescape(code)
                items.append(dict(
                    kind="flasher", file=rel, page_title=page_title,
                    title=attr(block, "title") or "", manifestPath=attr(block, "manifestPath") or "",
                    aiGenerated=attr(block, "aiGenerated") or "", aiModel=attr(block, "aiModel") or "",
                    heading=heading_before(src, start), hpath=heading_path(src, start), prose=prose_before(src, start), after=prose_after(src, end),
                    code=dedent(code), pos=start,
                    complete=is_complete(code),
                ))

            # fenced cpp blocks not inside a flasher
            flasher_spans = [(s, e) for s, e, _ in find_flashers(src)]
            for m in re.finditer(r"^([ \t]*)```(cpp|c\+\+|arduino|ino|c)[ \t]*\n([\s\S]*?)\n[ \t]*```", src, re.M):
                p = m.start()
                if any(s <= p < e for s, e in flasher_spans): continue
                code = dedent(m.group(3))
                items.append(dict(
                    kind="fence", file=rel, page_title=page_title,
                    title="", manifestPath="", aiGenerated="", aiModel="",
                    heading=heading_before(src, p), hpath=heading_path(src, p), prose=prose_before(src, p), after=prose_after(src, m.end()),
                    code=code, pos=p, complete=is_complete(code),
                ))
    items.sort(key=lambda x: (x["file"], x["pos"]))
    return items

if __name__ == "__main__":
    items = collect()
    with open(os.path.expanduser("~/work/blocks.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, indent=1)
    tot = len(items)
    comp = sum(1 for i in items if i["complete"])
    fl = sum(1 for i in items if i["kind"] == "flasher")
    print(f"total blocks: {tot}   flashers: {fl}   fences: {tot-fl}")
    print(f"complete sketches: {comp}   fragments: {tot-comp}")
    print()
    print("flashers that are NOT complete sketches:")
    for i in items:
        if i["kind"] == "flasher" and not i["complete"]:
            print(f"   {i['file']:55s} {i['title']}")
