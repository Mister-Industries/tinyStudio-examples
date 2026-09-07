#!/usr/bin/env python3
"""
Compile every tinyStudio example and produce browser-flashable firmware.

For each sketch this writes

    firmware/<category>/<name>/firmware.bin    a single merged image, offset 0
    firmware/<category>/<name>/manifest.json   an ESP Web Tools manifest

which is exactly what the green "Flash tinyCore" button on tinyDocs consumes —
so a reader can flash any example from the browser with no IDE, no tinyStudio
and no tinyService.

Why not just use arduino-cli's own <sketch>.ino.merged.bin? Because the ESP32
core builds it with `--fill-flash-size`, which pads every image out to the full
8 MB of flash. The same firmware merged without that padding is ~360 KB. Over
~70 examples that is the difference between 550 MB and 40 MB, and between a
30-second download per flash and an instant one.

Usage
    python3 tools/build-firmware.py                 # everything
    python3 tools/build-firmware.py --only blink-basic wifi-mqtt-client
    python3 tools/build-firmware.py --skip-deps -j8 # deps already installed
    python3 tools/build-firmware.py --clean

Exit code is non-zero if any sketch fails, so this can gate CI.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, os, platform, re, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FQBN = "tinyCore:esp32:tiny_core_esp32s3_nopsram"
CHIP_FAMILY = "ESP32-S3"
CHIP = "esp32s3"
BOARD_INDEX = ("https://raw.githubusercontent.com/Mister-Industries/arduino-board-index/"
               "refs/heads/main/package_tiny_core_index.json")
ESP32_INDEX = ("https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/"
               "package_esp32_index.json")

# Flash layout for the ESP32-S3, mirroring the core's own upload recipe.
OFFSETS = {"bootloader": 0x0, "partitions": 0x8000, "boot_app0": 0xE000, "app": 0x10000}

# Third-party libraries, pinned. Installed straight from git so the build does
# not depend on the Arduino Library Manager index being reachable.
LIBRARIES = [
    ("Adafruit_SSD1306",        "https://github.com/adafruit/Adafruit_SSD1306.git",      "2.5.13"),
    ("Adafruit_GFX_Library",    "https://github.com/adafruit/Adafruit-GFX-Library.git",  "1.11.11"),
    ("Adafruit_BusIO",          "https://github.com/adafruit/Adafruit_BusIO.git",        "1.16.2"),
    ("Adafruit_Unified_Sensor", "https://github.com/adafruit/Adafruit_Sensor.git",       "1.1.14"),
    ("Adafruit_LSM6DS",         "https://github.com/adafruit/Adafruit_LSM6DS.git",       "4.7.4"),
    ("Adafruit_MCP4725",        "https://github.com/adafruit/Adafruit_MCP4725.git",      "2.0.2"),
    ("ArduinoJson",             "https://github.com/bblanchon/ArduinoJson.git",          "v7.2.1"),
    ("PubSubClient",            "https://github.com/knolleary/pubsubclient.git",         "v2.8"),
    ("WebSockets",              "https://github.com/Links2004/arduinoWebSockets.git",    "2.6.1"),
    ("AsyncTCP",                "https://github.com/ESP32Async/AsyncTCP.git",            None),
    ("ESPAsyncWebServer",       "https://github.com/ESP32Async/ESPAsyncWebServer.git",   None),
    ("ESP32_audioI2S",          "https://github.com/schreibfaul1/ESP32-audioI2S.git",    "3.2.1"),
    ("ESP_Mail_Client",         "https://github.com/mobizt/ESP-Mail-Client.git",         None),
    ("ElegantOTA",              "https://github.com/ayushsharma82/ElegantOTA.git",       None),
]


# A few sketches need a compile-time switch that can't live in the sketch or the
# library. Keyed by example name.
EXTRA_FLAGS = {
    # ElegantOTA defaults to the synchronous WebServer; this example pairs it
    # with ESPAsyncWebServer, which the library only supports when told to.
    "wifi-ota-updates": ["-DELEGANTOTA_USE_ASYNC_WEBSERVER=1"],
}


# ----------------------------------------------------------------- discovery
def find_cli(explicit: str | None) -> str:
    """arduino-cli: --cli, then $ARDUINO_CLI, then tinyStudio's vendored copy, then PATH."""
    if explicit:
        return explicit
    if os.environ.get("ARDUINO_CLI"):
        return os.environ["ARDUINO_CLI"]
    plat = {"Windows": "windows-x64", "Darwin": "macos", "Linux": "linux"}.get(platform.system(), "linux")
    if plat == "macos":
        plat = "macos-arm64" if platform.machine() in ("arm64", "aarch64") else "macos-x64"
    elif plat == "linux":
        plat = "linux-arm64" if platform.machine() in ("arm64", "aarch64") else "linux-x64"
    exe = "arduino-cli.exe" if platform.system() == "Windows" else "arduino-cli"
    for base in (os.path.join(ROOT, "..", "tinyStudio", "vendor", "arduino-cli"),
                 os.path.join(ROOT, "vendor", "arduino-cli")):
        cand = os.path.abspath(os.path.join(base, plat, exe))
        if os.path.isfile(cand):
            return cand
    found = shutil.which("arduino-cli")
    if found:
        return found
    sys.exit("arduino-cli not found. Pass --cli /path/to/arduino-cli, set $ARDUINO_CLI,\n"
             "or check out tinyStudio next to this repo (it vendors one).")


def discover(root: str) -> list[dict]:
    """Every sketch folder in the repo, as {category, name, dir}."""
    out = []
    for cat in ("basics", "advanced"):
        d = os.path.join(root, cat)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if os.path.isfile(os.path.join(p, name + ".ino")):
                out.append({"category": cat, "name": name, "dir": p})
    hat_root = os.path.join(root, "_hat-updates")
    if os.path.isdir(hat_root):
        for repo in sorted(os.listdir(hat_root)):
            d = os.path.join(hat_root, repo, "Software", "Arduino", "Examples")
            if not os.path.isdir(d):
                continue
            for name in sorted(os.listdir(d)):
                p = os.path.join(d, name)
                if os.path.isfile(os.path.join(p, name + ".ino")):
                    out.append({"category": "hats/" + repo, "name": name, "dir": p})
    return out


# ------------------------------------------------------------------- helpers
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ensure_deps(cli: str, cfg: str, sketchbook: str, quiet: bool) -> None:
    say = (lambda *a: None) if quiet else print
    say("Configuring arduino-cli…")
    run([cli, "config", "init", "--dest-file", cfg, "--overwrite"])
    run([cli, "config", "set", "board_manager.additional_urls", ESP32_INDEX, BOARD_INDEX,
         "--config-file", cfg])
    run([cli, "config", "set", "directories.user", sketchbook, "--config-file", cfg])
    say("Updating board index…")
    run([cli, "core", "update-index", "--config-file", cfg])
    say(f"Installing {FQBN.split(':')[0]} core (a few hundred MB the first time)…")
    r = run([cli, "core", "install", "tinyCore:esp32", "--config-file", cfg])
    if r.returncode != 0 and "already installed" not in (r.stdout + r.stderr):
        say(r.stdout[-2000:], r.stderr[-2000:])

    libdir = os.path.join(sketchbook, "libraries")
    os.makedirs(libdir, exist_ok=True)
    for name, url, tag in LIBRARIES:
        dest = os.path.join(libdir, name)
        if os.path.isdir(dest):
            continue
        say(f"  lib {name} {tag or '(default branch)'}")
        cmd = ["git", "clone", "-q", "--depth", "1"]
        if tag:
            cmd += ["--branch", tag]
        if run(cmd + [url, dest]).returncode != 0 and tag:
            run(["git", "clone", "-q", "--depth", "1", url, dest])
        if not os.path.isdir(dest):
            say(f"  !! could not fetch {name} — sketches needing it will fail")


def ctags_shim(cli: str, cfg: str) -> bool:
    """Returns True if we had to disable ctags (caller must generate prototypes)."""
    """
    arduino-cli generates .ino function prototypes with a ctags binary it
    normally downloads from downloads.arduino.cc. On a machine that can't reach
    it (locked-down network, offline build box) the compile dies with
    'fork/exec {runtime.tools.ctags.path}/ctags'. If a system ctags exists,
    drop it where the CLI looks. No-op when the real tool is already installed.
    """
    data = run([cli, "config", "get", "directories.data", "--config-file", cfg]).stdout.strip()
    if not data:
        return False
    for ver in ("5.8-arduino11", "5.8-arduino12"):
        dest = os.path.join(data, "packages", "builtin", "tools", "ctags", ver)
        real = os.path.join(dest, "ctags.exe" if platform.system() == "Windows" else "ctags")
        if os.path.isfile(real) and os.path.getsize(real) > 4096:
            return False
    dest = os.path.join(data, "packages", "builtin", "tools", "ctags", "5.8-arduino11")
    os.makedirs(dest, exist_ok=True)
    target = os.path.join(dest, "ctags.exe" if platform.system() == "Windows" else "ctags")
    try:
        if platform.system() == "Windows":
            with open(target[:-4] + ".bat", "w") as f:
                f.write("@echo off\r\nexit /b 0\r\n")
            shutil.copy2(target[:-4] + ".bat", target)
        else:
            with open(target, "w") as f:
                f.write("#!/bin/sh\nexit 0\n")
            os.chmod(target, 0o755)
    except OSError:
        return False
    print("  builtin ctags unavailable — disabling it and generating prototypes locally")
    return True


def esptool_cmd(cli: str, cfg: str) -> list[str]:
    data = run([cli, "config", "get", "directories.data", "--config-file", cfg]).stdout.strip()
    base = os.path.join(data, "packages", "esp32", "tools", "esptool_py")
    if os.path.isdir(base):
        for ver in sorted(os.listdir(base), reverse=True):
            for exe in ("esptool", "esptool.exe", "esptool.py"):
                p = os.path.join(base, ver, exe)
                if os.path.isfile(p):
                    return [sys.executable, p] if p.endswith(".py") else [p]
    found = shutil.which("esptool.py") or shutil.which("esptool")
    if found:
        return [found]
    sys.exit("esptool not found — install the tinyCore core first (drop --skip-deps).")


def platform_dir(cli: str, cfg: str) -> str:
    data = run([cli, "config", "get", "directories.data", "--config-file", cfg]).stdout.strip()
    base = os.path.join(data, "packages", "tinyCore", "hardware", "esp32")
    ver = sorted(os.listdir(base))[-1]
    return os.path.join(base, ver)


SIZE_RE = re.compile(r"Sketch uses (\d+) bytes.*?(\d+)%", re.S)

# ---------------------------------------------------------- prototype pre-pass
# Arduino lets a .ino call a function defined further down the file; the builder
# normally synthesises the missing C++ prototypes using a patched `ctags` it
# downloads from downloads.arduino.cc. Where that tool can't be fetched, a
# stand-in ctags is not good enough — a different ctags reports different line
# numbers and the builder splices prototypes into the middle of a statement,
# producing errors like "expected constructor before ';' token" in code that is
# perfectly valid. So when the real tool is missing we switch ctags off entirely
# and generate the prototypes here, inserting them immediately before the first
# function definition (after all globals, typedefs and structs) — a strictly
# safer insertion point than the builder's "right after the last #include".
FUNC_RE = re.compile(
    r"^(?P<ret>(?:[A-Za-z_][\w:]*\s*(?:<[^;{}]*?>)?[\s\*&]+)+)"
    r"(?P<name>[A-Za-z_]\w*)\s*\((?P<args>[^;{}()]*)\)\s*(?:const\s*)?\{",
    re.M)
NOT_A_TYPE = {"if", "for", "while", "switch", "return", "else", "do", "catch",
              "sizeof", "function", "case", "new", "delete", "typedef"}


def _mask(src: str) -> str:
    """Same-length copy with comments and string/char literals blanked out.

    Scanning the raw source would find `function togglePlay() {` inside a
    R"rawliteral( ... )rawliteral" block of page JavaScript and emit it as a C++
    prototype. Masking first means only real code is considered, and offsets
    still line up with the original.
    """
    out = list(src)
    i, n = 0, len(src)
    def blank(a, b):
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "
    while i < n:
        two = src[i:i + 2]
        if two == "/*":
            j = src.find("*/", i + 2); j = n if j < 0 else j + 2
            blank(i, j); i = j
        elif two == "//":
            j = src.find("\n", i); j = n if j < 0 else j
            blank(i, j); i = j
        elif src[i] == "R" and src[i + 1:i + 2] == '"':
            m = re.match(r'R"([^(]{0,16})\(', src[i:])
            if m:
                close = ")" + m.group(1) + '"'
                j = src.find(close, i + m.end()); j = n if j < 0 else j + len(close)
                blank(i, j); i = j
            else:
                i += 1
        elif src[i] in "\"'":
            q = src[i]; j = i + 1
            while j < n and src[j] != q:
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            blank(i, j); i = j
        else:
            i += 1
    return "".join(out)


def _split_args(args: str) -> str:
    """Drop default values — repeating them in a prototype is a hard error."""
    parts, depth, cur = [], 0, []
    for ch in args:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    out = []
    for p in parts:
        p = p.split("=")[0].strip()
        if p:
            out.append(" ".join(p.split()))
    return ", ".join(out)


def add_prototypes(src: str) -> str:
    masked = _mask(src)
    funcs, first = [], None
    for m in FUNC_RE.finditer(masked):
        ret = " ".join(m.group("ret").split())
        name = m.group("name")
        if ret.split()[0] in NOT_A_TYPE or name in NOT_A_TYPE:
            continue
        before = masked[:m.start()].rstrip()
        if before.endswith(("=", ",", "(")):      # initialiser / lambda, not a definition
            continue
        if first is None:
            first = m.start()
        if name in ("setup", "loop"):
            continue
        funcs.append(f"{ret} {name}({_split_args(m.group('args'))});")
    if not funcs or first is None:
        return src
    block = ("// --- prototypes generated by tools/build-firmware.py "
             "(the Arduino builder normally does this) ---\n"
             + "\n".join(funcs) + "\n\n")
    return src[:first] + block + src[first:]


def build_one(job, cli, cfg, esptool, boot_app0, outroot, builddir, prototypes=False) -> dict:
    name, cat, sdir = job["name"], job["category"], job["dir"]
    bpath = os.path.join(builddir, cat.replace("/", "_"), name)
    os.makedirs(bpath, exist_ok=True)
    t0 = time.time()

    if prototypes:
        # compile a preprocessed copy; the committed .ino is never touched
        sdir = os.path.join(builddir, "_src", cat.replace("/", "_"), name)
        shutil.rmtree(sdir, ignore_errors=True)
        shutil.copytree(job["dir"], sdir)
        ino = os.path.join(sdir, name + ".ino")
        with open(ino, encoding="utf-8") as f:
            src = f.read()
        with open(ino, "w", encoding="utf-8", newline="\n") as f:
            f.write(add_prototypes(src))

    cmd = [cli, "compile", "--fqbn", FQBN, "--config-file", cfg,
           "--output-dir", bpath, "--build-path", bpath + "_work"]
    for flag in EXTRA_FLAGS.get(name, []):
        cmd += ["--build-property", f"compiler.cpp.extra_flags={flag}"]
    cmd.append(sdir)
    r = run(cmd)
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip().splitlines()
        err = [l for l in err if "Error initializing instance" not in l and "library_index" not in l]
        return {**job, "ok": False, "seconds": round(time.time() - t0, 1),
                "error": "\n".join(err[-12:])[:1500]}

    parts = {"app": f"{name}.ino.bin", "bootloader": f"{name}.ino.bootloader.bin",
             "partitions": f"{name}.ino.partitions.bin"}
    missing = [k for k, v in parts.items() if not os.path.isfile(os.path.join(bpath, v))]
    if missing:
        return {**job, "ok": False, "seconds": round(time.time() - t0, 1),
                "error": f"compiled but missing artifacts: {missing}"}

    outdir = os.path.join(outroot, cat, name)
    os.makedirs(outdir, exist_ok=True)
    fw = os.path.join(outdir, "firmware.bin")
    merge = esptool + ["--chip", CHIP, "merge_bin", "-o", fw,
                       "--flash_mode", "keep", "--flash_freq", "keep", "--flash_size", "keep",
                       hex(OFFSETS["bootloader"]), os.path.join(bpath, parts["bootloader"]),
                       hex(OFFSETS["partitions"]), os.path.join(bpath, parts["partitions"]),
                       hex(OFFSETS["boot_app0"]), boot_app0,
                       hex(OFFSETS["app"]), os.path.join(bpath, parts["app"])]
    m = run(merge)
    if m.returncode != 0 or not os.path.isfile(fw):
        return {**job, "ok": False, "seconds": round(time.time() - t0, 1),
                "error": "merge_bin failed:\n" + (m.stderr or m.stdout)[-800:]}

    title = job.get("title") or name
    manifest = {
        "name": title,
        "version": "1.0.0",
        "new_install_prompt_erase": False,
        "builds": [{"chipFamily": CHIP_FAMILY, "improv": False,
                    "parts": [{"path": "firmware.bin", "offset": 0}]}],
    }
    with open(os.path.join(outdir, "manifest.json"), "w", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    sm = SIZE_RE.search(r.stdout or "")
    return {**job, "ok": True, "seconds": round(time.time() - t0, 1),
            "bytes": os.path.getsize(fw), "app_bytes": os.path.getsize(os.path.join(bpath, parts["app"])),
            "flash_pct": int(sm.group(2)) if sm else None,
            "firmware": os.path.relpath(fw, outroot).replace(os.sep, "/")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cli", help="path to arduino-cli")
    ap.add_argument("--only", nargs="*", help="build just these example names")
    ap.add_argument("--skip-deps", action="store_true", help="assume core + libraries are installed")
    ap.add_argument("-j", "--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    ap.add_argument("--clean", action="store_true", help="wipe firmware/ and the build cache first")
    ap.add_argument("--out", default=os.path.join(ROOT, "firmware"))
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    cli = find_cli(a.cli)
    cfg = os.path.join(ROOT, ".arduino-cli.yaml")
    sketchbook = os.path.join(ROOT, ".arduino")
    builddir = os.path.join(ROOT, ".build")
    if a.clean:
        for d in (a.out, builddir):
            shutil.rmtree(d, ignore_errors=True)

    print(f"arduino-cli : {cli}")
    print(f"board       : {FQBN}")
    if not a.skip_deps:
        ensure_deps(cli, cfg, sketchbook, a.quiet)
    need_prototypes = ctags_shim(cli, cfg)

    esptool = esptool_cmd(cli, cfg)
    boot_app0 = os.path.join(platform_dir(cli, cfg), "tools", "partitions", "boot_app0.bin")
    if not os.path.isfile(boot_app0):
        sys.exit(f"boot_app0.bin not found at {boot_app0}")

    jobs = discover(ROOT)
    if a.only:
        want = set(a.only)
        jobs = [j for j in jobs if j["name"] in want]
        missing = want - {j["name"] for j in jobs}
        if missing:
            print("no such example(s):", ", ".join(sorted(missing)))
    if not jobs:
        sys.exit("nothing to build")

    # titles come from the manifest so the flasher dialog says something human
    try:
        with open(os.path.join(ROOT, "examples.json")) as f:
            titles = {e["path"].split("/")[-1]: e["title"] for e in json.load(f)}
        for j in jobs:
            j["title"] = titles.get(j["name"], j["name"])
    except Exception:
        pass

    print(f"building    : {len(jobs)} sketches, {a.jobs} at a time\n")
    results, done = [], 0
    with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(build_one, j, cli, cfg, esptool, boot_app0, a.out, builddir,
                                  need_prototypes): j for j in jobs}
        for fut in cf.as_completed(futs):
            res = fut.result()
            results.append(res)
            done += 1
            if res["ok"]:
                print(f"[{done:>3}/{len(jobs)}] ok    {res['name']:<40} "
                      f"{res['bytes']/1024:7.0f} KB  {res['seconds']:>5.1f}s")
            else:
                print(f"[{done:>3}/{len(jobs)}] FAIL  {res['name']:<40} {res['seconds']:>5.1f}s")

    results.sort(key=lambda r: (r["category"], r["name"]))
    ok = [r for r in results if r["ok"]]
    bad = [r for r in results if not r["ok"]]
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "report.json"), "w", newline="\n") as f:
        json.dump({"board": FQBN,
                   "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "ok": len(ok), "failed": len(bad),
                   "total_bytes": sum(r["bytes"] for r in ok),
                   "libraries": [{"name": n, "url": u, "version": v} for n, u, v in LIBRARIES],
                   "results": results}, f, indent=2)
        f.write("\n")

    print(f"\n{len(ok)} built, {len(bad)} failed, "
          f"{sum(r['bytes'] for r in ok)/1048576:.1f} MB of firmware total")
    if bad:
        print("\nfailures:")
        for r in bad:
            first = (r["error"] or "").strip().splitlines()
            print(f"  {r['name']}\n      {first[0] if first else '?'}")
        print(f"\nfull errors in {os.path.join(a.out, 'report.json')}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
