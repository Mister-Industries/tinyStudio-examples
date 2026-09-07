#!/usr/bin/env python3
"""Second half of the build: HAT linking, manifest, repo scaffolding."""
import json, os, re, sys, collections
HOME = os.path.expanduser("~")
sys.path.insert(0, f"{HOME}/work")
import generate as G

STAGING = G.STAGING
OWNER   = G.OWNER

# ---- tinyHAT wiring -------------------------------------------------------
# Each HAT keeps its own repo. tinyStudio loads <owner>/<repo>/<path> directly,
# and these repos already use the Arduino sketch-folder layout it expects:
#   Software/Arduino/Examples/<Name>/<Name>.ino
# So the manifest LINKS to them — no copies, no drift.
HAT_ROOT = "Software/Arduino/Examples"

# docs block title  ->  (repo, sketch folder in that repo)
# Verified against the live repo trees on 2026-09-06.
HAT_MAP = {
    # tinySniff — the docs and the repo disagree on names; mapped by content.
    "Basic_Demo.ino":         ("tinySniff", "tinySniff_Monitor"),
    "SD_Card_Logger.ino":     ("tinySniff", "tinySniff_SDLogger"),
    "Google_Sheets.ino":      ("tinySniff", "tinySniff_Sheets"),
    "Text_Notifications.ino": ("tinySniff", "tinySniff_Alarm"),
    # No counterpart in the repo yet — staged in _hat-updates/ for you to push.
    "Button_and_Buzzer.ino":  ("tinySniff", "tinySniff_ButtonBuzzer"),
    # tinySpeak — docs titles already match the repo folder names exactly.
    "tinyMP3Player.ino":      ("tinySpeak", "tinyMP3Player"),
    "tinyRecorder.ino":       ("tinySpeak", "tinyRecorder"),
    "tinySoundboard.ino":     ("tinySpeak", "tinySoundboard"),
    "tinyTheremin.ino":       ("tinySpeak", "tinyTheremin"),
    "tinyWalkieTalkie.ino":   ("tinySpeak", "tinyWalkieTalkie"),
    "tinyWebSynth":           ("tinySpeak", "tinyWebSynth"),
    "tinyAIText.ino":         ("tinySpeak", "tinyAIText"),
    "tinyAIVoice.ino":        ("tinySpeak", "tinyAIVoice"),
    "tinyAIVoice_EL.ino":     ("tinySpeak", "tinyAIVoice_EL"),
}
# Folders confirmed to exist on the HAT repos' default branch today. Anything
# not in here is staged in _hat-updates/ and its manifest entry is held back.
HAT_LIVE = {
    ("tinySniff", "tinySniff_Monitor"), ("tinySniff", "tinySniff_Alarm"),
    ("tinySniff", "tinySniff_SDLogger"), ("tinySniff", "tinySniff_Sheets"),
    ("tinySpeak", "tinyMP3Player"), ("tinySpeak", "tinyRecorder"),
    ("tinySpeak", "tinySoundboard"), ("tinySpeak", "tinyTheremin"),
    ("tinySpeak", "tinyWalkieTalkie"), ("tinySpeak", "tinyWebSynth"),
    ("tinySpeak", "tinyAIText"), ("tinySpeak", "tinyAIVoice"),
    ("tinySpeak", "tinyAIVoice_EL"),
}
HAT_BOARD = {"tinySniff": "tinyCore + tinySniff HAT",
             "tinySpeak": "tinyCore + tinySpeak HAT"}

def load_blocks():
    items = json.load(open(f"{HOME}/work/blocks.json"))
    by_file = collections.defaultdict(list)
    for i in items:
        by_file[i["file"]].append(i)
    for f, g in by_file.items():
        g.sort(key=lambda x: x["pos"])
        for idx, i in enumerate(g):
            if i["kind"] == "flasher" and not i["complete"]:
                for j in reversed(g[:idx]):
                    if j["complete"] and j["kind"] == "flasher":
                        i["code"] = G.stitch(i["code"], j["code"])
                        i["complete"] = True
                        break
    return items

def main():
    items   = load_blocks()
    entries = json.load(open(f"{STAGING}/.manifest-core.json"))
    pending = []

    hats = [i for i in items if i["complete"] and G.category(i["file"]) == "hat"]
    for i in hats:
        key = (i.get("title") or "").strip()
        if key not in HAT_MAP:
            continue
        repo, folder = HAT_MAP[key]
        path = f"{HAT_ROOT}/{folder}"
        studio = f"{G.STUDIO_BASE}/{OWNER}/{repo}/{path}"
        entry = {
            "title": f"{repo}: {G.human_title(i)}",
            "description": G.first_sentence(i),
            "owner": OWNER, "repo": repo, "path": path,
            "board": HAT_BOARD.get(repo, "tinyCore + HAT"),
            "category": "hats",
            "docsUrl": G.docs_url(i["file"]),
        }
        if (repo, folder) in HAT_LIVE:
            entries.append(entry)
        else:
            pending.append(entry)

        # Mirror the docs version of every HAT sketch into _hat-updates/ so the
        # HAT repos can be diffed against what the docs currently publish.
        d = os.path.join(STAGING, "_hat-updates", repo, HAT_ROOT, folder)
        os.makedirs(d, exist_ok=True)
        code = G.header_comment(i, folder, "hats", studio) + i["code"].strip() + "\n"
        open(os.path.join(d, f"{folder}.ino"), "w", encoding="utf-8", newline="\n").write(code)
        open(os.path.join(d, "README.md"), "w", encoding="utf-8", newline="\n").write(
            G.readme(i, folder, "hats", studio))

    # The three original tinyStudio demo projects keep their circuit + p5 views.
    demos = [
        {"title": "Blink LED (Circuit + Visual)",
         "description": "Blink the onboard LED and mirror its state in the Visual view.",
         "owner": OWNER, "repo": "tinyStudio", "path": "demo/Blink Example",
         "board": "tinyCore / Arduino", "category": "demos",
         "docsUrl": f"{G.DOCS_BASE}/2_tiny-core/basics/blink-led/"},
        {"title": "Fade LED (Circuit + Visual)",
         "description": "PWM-fade an LED and chart the brightness curve live.",
         "owner": OWNER, "repo": "tinyStudio", "path": "demo/Fade Example",
         "board": "tinyCore / Arduino", "category": "demos",
         "docsUrl": f"{G.DOCS_BASE}/5_reference/advanced/pwm/"},
        {"title": "Joystick (Circuit + Visual)",
         "description": "Read a Qwiic joystick and visualize the stick position.",
         "owner": OWNER, "repo": "tinyStudio", "path": "demo/Joystick Example",
         "board": "tinyCore + Qwiic Joystick", "category": "demos",
         "docsUrl": f"{G.DOCS_BASE}/2_tiny-core/basics/read-sensor-value/"},
    ]

    order = {"demos": 0, "basics": 1, "advanced": 2, "hats": 3}
    manifest = demos + entries
    manifest.sort(key=lambda e: (order.get(e["category"], 9), e["title"].lower()))

    with open(f"{STAGING}/examples.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    if pending:
        with open(f"{STAGING}/examples.pending.json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(pending, f, indent=2)
            f.write("\n")

    os.remove(f"{STAGING}/.manifest-core.json")
    print(f"manifest: {len(manifest)} entries "
          f"({collections.Counter(e['category'] for e in manifest)})")
    print(f"pending (path not on the HAT repo yet): {len(pending)}")
    return manifest, pending

if __name__ == "__main__":
    main()
