#!/usr/bin/env python3
"""
Build the tinyStudio-examples repo tree from the tinyDocs .mdx content.

Reads  ~/work/blocks.json  (produced by extract.py)
Writes <STAGING>/  — a complete, ready-to-push repo.

Run extract.py first, then this. Both are idempotent: the output tree is
deleted and rebuilt from scratch every run, so the docs stay the source of
truth and nothing hand-edited in the output survives (edit the docs instead).
"""
import json, os, re, shutil, collections

HOME     = os.path.expanduser("~")
BLOCKS   = f"{HOME}/work/blocks.json"
STAGING  = f"{HOME}/work/out/tinyStudio-examples"

DOCS_BASE   = "https://tinydocs.cc"                 # tinyDocs published site
STUDIO_BASE = "https://app.tinystudio.cc"           # tinyStudio web IDE
OWNER       = "Mister-Industries"
EX_REPO     = "tinyStudio-examples"

# ---------------------------------------------------------------- categories
CATMAP = [
    ("3_tiny-hats/",        "hat"),
    ("1_get-started/",      "basics"),
    ("2_tiny-core/basics/", "basics"),
    ("2_tiny-core/advanced/", "advanced"),
    ("5_reference/basics/", "basics"),
    ("5_reference/advanced/", "advanced"),
    ("6_community-projects/", "advanced"),
    ("docs-explorer/",      "basics"),
]
def category(f):
    for pre, c in CATMAP:
        if f.startswith(pre):
            return c
    return "basics"

# Headings that say nothing about the sketch — skip them when naming.
GENERIC = {
    "the code", "code", "the sketch", "sketch", "example", "examples",
    "try it out", "try it out!", "what's happening?", "the full code",
    "complete code", "full code", "putting it together",
}

STOP = {"a","an","the","to","on","in","of","at","and","with","your","you","for",
        "it","is","are","from","this","that","using","use","real","just","its"}

def slugify(s):
    s = re.sub(r"\.ino$", "", (s or "").strip(), flags=re.I)
    s = re.sub(r"^(Step|Part|Example)\s*\d*\s*[:.\-]?\s*", "", s, flags=re.I)
    s = re.sub(r"^\d+[.)]\s*", "", s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace("&", " and ").replace("+", " plus ")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return re.sub(r"-{2,}", "-", s)

def tokens(s, drop_stop=True):
    ts = [t for t in slugify(s).split("-") if t]
    return [t for t in ts if not (drop_stop and t in STOP)] or ts

def titleize(s):
    s = re.sub(r"\.ino$", "", (s or "").strip(), flags=re.I)
    s = re.sub(r"^(Step|Part|Example)\s*\d*\s*[:.\-]?\s*", "", s, flags=re.I)
    s = re.sub(r"^\d+[.)]\s*", "", s)
    return s.strip().rstrip(":!").strip()

def page_topic(f):
    return slugify(os.path.basename(f)[:-4])

def pick_heading(item):
    """Deepest non-generic heading, else the block title, else the page."""
    for h in reversed(item.get("hpath") or []):
        if h.strip().lower().rstrip("!?:") not in GENERIC:
            return h
    return item.get("title") or item.get("page_title") or ""

# Hand-picked names where the auto rule reads badly. key = (file, heading)
OVERRIDE = {
    ("2_tiny-core/basics/blink-led.mdx", "Basic Blink Program"):        "blink-basic",
    ("2_tiny-core/basics/blink-led.mdx", "Alternating Blink Pattern"):  "blink-alternate",
    ("2_tiny-core/basics/blink-led.mdx", "Smooth Breathing Effect"):    "blink-breathing",
    ("2_tiny-core/basics/blink-led.mdx", "Manual Brightness Control"):  "blink-brightness",
    ("2_tiny-core/basics/blink-led.mdx", "Code for External LED"):      "blink-external-led",
    ("2_tiny-core/basics/blink-led.mdx", "PWM Control for All Three LEDs"): "blink-pwm-wave",
    ("2_tiny-core/basics/blink-led.mdx", "SOS Signal"):                 "blink-sos",
    ("1_get-started/imu.mdx",            "2. Flash the tinyCore"):      "imu-serial-plotter",
    ("2_tiny-core/basics/detect-motion.mdx", "2. Flash the tinyCore"):  "imu-motion-plotter",
    ("1_get-started/motion-tracker.mdx", "The Complete Motion Tracker Code"): "motion-tracker",
    ("2_tiny-core/basics/i2c-display.mdx", "4. Interactive Physics: The IMU Digital Hourglass"): "i2c-display-imu-hourglass",
    ("2_tiny-core/basics/button-press.mdx", "Step 5: Toggle behavior vs direct control"): "button-press-toggle-vs-direct",
    ("2_tiny-core/basics/button-press.mdx", "Step 6: Multiple buttons, multiple behaviors"): "button-press-multiple-buttons",
    ("5_reference/basics/imu.mdx", "Using It in Code"): "imu-read-orientation",
    ("5_reference/basics/i2c.mdx", "The I2C Scanner: Your Best Debugging Tool"): "i2c-scanner",
    ("5_reference/basics/esp-now.mdx", "On the tinyCore"): "esp-now-basic",
    ("5_reference/basics/sd-card.mdx", "Basic Code: Write and Read a File"): "sd-card-write-and-read",
    ("5_reference/advanced/wifi.mdx", "Basic Connection Code"): "wifi-connect-reference",
    ("2_tiny-core/basics/serial-monitor-plotter.mdx", "Memory and performance monitoring"): "serial-monitor-memory-stats",
    ("2_tiny-core/basics/serial-monitor-plotter.mdx", "Real sensor data visualization"): "serial-plotter-sensor-data",
    ("2_tiny-core/basics/serial-monitor-plotter.mdx", "Debugging with timestamps"): "serial-monitor-timestamps",
    ("2_tiny-core/basics/serial-monitor-plotter.mdx", "Single variable plotting"): "serial-plotter-single-variable",
    ("2_tiny-core/basics/serial-monitor-plotter.mdx", "Multiple variable plotting"): "serial-plotter-multi-variable",
    ("2_tiny-core/basics/serial-monitor-plotter.mdx", "Basic output example"): "serial-monitor-basic-output",
    ("2_tiny-core/basics/serial-monitor-plotter.mdx", "Reading input from Serial Monitor"): "serial-monitor-read-input",
    ("2_tiny-core/basics/bluetooth.mdx", "Basic BLE Server Example"): "bluetooth-ble-server",
    ("2_tiny-core/basics/bluetooth.mdx", "1. RGB Mood Light Controller"): "bluetooth-rgb-mood-light",
    ("2_tiny-core/basics/read-sensor-value.mdx", "Step 5: Multiple sensors at once"): "read-sensor-multiple-sensors",
    ("2_tiny-core/basics/read-sensor-value.mdx", "Step 2: Reading a potentiometer"): "read-sensor-potentiometer",
    ("2_tiny-core/basics/read-sensor-value.mdx", "Step 3: Visualizing with Serial Plotter"): "read-sensor-plotter",
    ("2_tiny-core/basics/read-sensor-value.mdx", "Step 4: Light sensor (photoresistor)"): "read-sensor-photoresistor",
    ("2_tiny-core/basics/read-sensor-value.mdx", "Step 6: Smart LED control"): "read-sensor-smart-led",
    ("2_tiny-core/basics/buzz-buzzer.mdx", "Step 2: Basic beeping code"): "buzzer-basic-beep",
    ("2_tiny-core/basics/buzz-buzzer.mdx", "Step 3: Playing different tones"): "buzzer-tones",
    ("2_tiny-core/basics/buzz-buzzer.mdx", "Step 4: Play a real song!"): "buzzer-song",
    ("2_tiny-core/basics/buzz-buzzer.mdx", "Step 5: Interactive buzzer"): "buzzer-interactive",
    ("2_tiny-core/basics/button-press.mdx", "Step 2: Basic button reading"): "button-press-basic",
    ("2_tiny-core/basics/button-press.mdx", "Step 3: Detecting button events"): "button-press-events",
    ("2_tiny-core/basics/button-press.mdx", "Step 4: Understanding NOT logic"): "button-press-not-logic",
    ("2_tiny-core/basics/save-data-to-sdcard.mdx", "Example 1: Initializing the SD Card"): "sdcard-init",
    ("2_tiny-core/basics/save-data-to-sdcard.mdx", "Example 2: Writing to a File"): "sdcard-write-file",
    ("2_tiny-core/basics/save-data-to-sdcard.mdx", "Example 3: Reading from a File"): "sdcard-read-file",
    ("2_tiny-core/basics/save-data-to-sdcard.mdx", "Example 4: Appending to a File"): "sdcard-append-file",
    ("2_tiny-core/basics/save-data-to-sdcard.mdx", "Example 5: CSV Data Logging"): "sdcard-csv-logger",
    ("2_tiny-core/basics/save-data-to-sdcard.mdx", "Example 6: Delete and List Files"): "sdcard-delete-and-list",
    ("2_tiny-core/basics/i2c-display.mdx", "3. Hello World (Text on Screen!)"): "i2c-display-hello-world",
    ("5_reference/advanced/adc.mdx", "Reading an Analog Value"): "adc-read-analog",
    ("5_reference/advanced/dac.mdx", "MCP4725 (I2C, 12-bit)"): "dac-mcp4725",
}

def target_name(item):
    key = (item["file"], pick_heading(item))
    if key in OVERRIDE:
        return OVERRIDE[key]
    topic = tokens(os.path.basename(item["file"])[:-4])
    base  = [t for t in tokens(pick_heading(item)) if t not in topic]
    name  = "-".join(topic + base[:4]) or "-".join(topic)
    return re.sub(r"-{2,}", "-", name).strip("-")

def human_title(item):
    t = titleize(item.get("title") or "")
    h = titleize(pick_heading(item))
    # doc titles are copy-pasted in places (four "sos.ino" on the buzzer page),
    # so the heading wins whenever it is meaningful
    return h or t or page_title(item)

EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2190-\u2BFF\uFE0F]")

def page_title(i):
    t = (i.get("page_title") or "").strip()
    t = EMOJI.sub("", t).strip().strip("'\"" ).strip()
    return re.sub(r"\s{2,}", " ", t)

def docs_url(f):
    return f"{DOCS_BASE}/{f[:-4]}/"

# ------------------------------------------------------- fragment stitching
LOOP_RE = re.compile(r"\bvoid\s+loop\s*\(\s*\)\s*\{", re.M)

def strip_loop(code):
    """Remove the void loop(){...} body from a sketch (brace-matched)."""
    m = LOOP_RE.search(code)
    if not m:
        return code
    i = m.end(); depth = 1
    while i < len(code) and depth:
        if code[i] == "{": depth += 1
        elif code[i] == "}": depth -= 1
        i += 1
    return (code[:m.start()] + code[i:]).rstrip() + "\n"

def stitch(fragment, base_code):
    """Graft a loop()-only fragment onto the preceding complete sketch."""
    return strip_loop(base_code).rstrip() + "\n\n" + fragment.strip() + "\n"

# ------------------------------------------------------------------ readme
def readme(item, name, cat, studio_url):
    title = human_title(item)
    crumbs = " › ".join(item.get("hpath") or [])
    body = []
    body.append(f"# {title}\n")
    intro = (item.get("prose") or "").strip()
    if intro:
        body.append(intro + "\n")
    after = (item.get("after") or "").strip()
    if after and after != intro:
        body.append(after + "\n")
    body.append("## Open it\n")
    body.append(f"- **tinyStudio (web)** — [open this project]({studio_url})")
    body.append(f"- **tinyStudio (desktop)** — Examples tab → *{title}*")
    body.append(f"- **Arduino IDE** — open `{name}/{name}.ino`\n")
    body.append("## Where this came from\n")
    body.append(f"From the tinyDocs page [{page_title(item)}]({docs_url(item['file'])}).")
    if crumbs:
        body.append(f"\nSection: *{crumbs}*")
    if item.get("aiGenerated", "").lower() in ("true", "yes"):
        model = item.get("aiModel") or "an AI model"
        body.append(f"\n> This sketch was one-shot by {model} and checked by hand.")
    body.append("\n## Files\n")
    body.append("```")
    body.append(f"{name}/")
    body.append(f"  {name}.ino   ← the sketch")
    body.append("  README.md")
    body.append("```\n")
    body.append("---\n")
    body.append("_Generated from tinyDocs by `tools/sync-examples.py`. "
                "Edit the docs page above, not this file — regenerating overwrites it._")
    return "\n".join(body) + "\n"

def header_comment(item, name, cat, studio_url):
    """A provenance banner prepended to each .ino."""
    return (
        "/*\n"
        f" * {human_title(item)}\n"
        " *\n"
        f" * Board:  tinyCore (ESP32-S3)\n"
        f" * Docs:   {docs_url(item['file'])}\n"
        f" * Studio: {studio_url}\n"
        " *\n"
        " * Part of the MR.INDUSTRIES tinyStudio examples collection.\n"
        " * Generated from tinyDocs — edit the docs page, not this file.\n"
        " */\n\n"
    )

# --------------------------------------------------------------------- main
def main():
    items = json.load(open(BLOCKS))

    # 1. stitch the two loop()-only flashers onto their base sketch
    by_file = collections.defaultdict(list)
    for i in items:
        by_file[i["file"]].append(i)
    for f, group in by_file.items():
        group.sort(key=lambda x: x["pos"])
        for idx, i in enumerate(group):
            if i["kind"] == "flasher" and not i["complete"]:
                base = None
                for j in reversed(group[:idx]):
                    if j["complete"] and j["kind"] == "flasher":
                        base = j; break
                if base:
                    i["code"] = stitch(i["code"], base["code"])
                    i["complete"] = True
                    i["stitched_from"] = base.get("title") or ""

    chosen = [i for i in items if i["complete"]]

    # 2. name everything, split HAT entries out
    named, hats = [], []
    used = collections.Counter()
    for i in chosen:
        cat = category(i["file"])
        if cat == "hat":
            hats.append(i); continue
        n = target_name(i)
        used[n] += 1
        if used[n] > 1:
            n = f"{n}-{used[n]}"
        named.append((cat, n, i))

    # 3. write the tree
    if os.path.isdir(STAGING):
        shutil.rmtree(STAGING)
    os.makedirs(STAGING, exist_ok=True)

    manifest = []
    for cat, name, i in named:
        rel  = f"{cat}/{name}"
        d    = os.path.join(STAGING, cat, name)
        os.makedirs(d, exist_ok=True)
        studio_url = f"{STUDIO_BASE}/{OWNER}/{EX_REPO}/{rel}"
        code = header_comment(i, name, cat, studio_url) + i["code"].strip() + "\n"
        open(os.path.join(d, f"{name}.ino"), "w", encoding="utf-8", newline="\n").write(code)
        open(os.path.join(d, "README.md"), "w", encoding="utf-8", newline="\n").write(
            readme(i, name, cat, studio_url))
        manifest.append({
            "title": human_title(i),
            "description": first_sentence(i),
            "owner": OWNER, "repo": EX_REPO, "path": rel,
            "board": "tinyCore (ESP32-S3)",
            "category": cat,
            "docsUrl": docs_url(i["file"]),
        })

    with open(os.path.join(STAGING, ".manifest-core.json"), "w", newline="\n") as f:
        json.dump(manifest, f, indent=2)

    json.dump({"named": [(c, n, i["file"], human_title(i)) for c, n, i in named],
               "hats": [(i["file"], i["title"], i["heading"]) for i in hats]},
              open(f"{HOME}/work/generated.json", "w"), indent=1)

    print(f"wrote {len(named)} example projects to {STAGING}")
    print(collections.Counter(c for c, _, _ in named))
    print(f"HAT blocks held back for linking: {len(hats)}")

LEADIN = re.compile(
    r"^(copy|paste|here'?s|here is|try|replace|add|open|upload|now|let'?s|"
    r"this is the code|the code|and here|type|enter|run)\b", re.I)

def sketch_description(code):
    """Pull the Description: paragraph out of a leading /* ... */ banner."""
    m = re.match(r"\s*/\*([\s\S]*?)\*/", code)
    if not m:
        return ""
    banner = "\n".join(re.sub(r"^\s*\*ic?", "", l).lstrip("* ").rstrip()
                        for l in m.group(1).split("\n"))
    d = re.search(r"Description:\s*\n([\s\S]*?)(\n\s*\n|\n[A-Z][a-z]+:)", banner)
    if not d:
        return ""
    txt = re.sub(r"\s+", " ", d.group(1)).strip()
    mm = re.search(r"^(.{20,190}?[.!?])(\s|$)", txt)
    return mm.group(1) if mm else txt[:170].rstrip() + "…"

def clean_prose(txt):
    txt = re.sub(r"(?m)^\s*(-{3,}|\*{3,}|_{3,})\s*$", " ", txt or "")
    txt = re.sub(r"\[\^?\d+\]", "", txt)
    txt = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", txt)
    txt = re.sub(r"[*_`#>]", "", txt)
    return re.sub(r"\s+", " ", txt).strip()

def first_sentence(i):
    d = sketch_description(i["code"])
    if d:
        return d
    def ok(sent):
        if len(sent) < 40 or len(sent.split()) < 7:
            return False
        if not sent[:1].isupper():
            return False
        if LEADIN.match(sent):
            return False
        if sent.rstrip().endswith((":", "→")) or " like this" in sent.lower():
            return False
        return True

    for source in (i.get("prose"), i.get("after")):
        txt = clean_prose(source)
        if not txt:
            continue
        for sent in re.findall(r"[^.!?]{15,220}[.!?]", txt):
            sent = sent.strip()
            if ok(sent):
                return sent
    return f"{human_title(i)} — from the tinyDocs \u201c{page_title(i)}\u201d guide."

if __name__ == "__main__":
    main()
