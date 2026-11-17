# Builds content.js (data + audio map + karaoke timings) and generates the Persian audio clips.
# Usage: python build.py            -> generates missing or changed audio, writes content.js and artifact.html
#        python build.py --no-audio -> only writes content.js and artifact.html from what exists
import asyncio, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(HERE, "audio")
MANIFEST = os.path.join(AUDIO_DIR, "manifest.json")
os.makedirs(AUDIO_DIR, exist_ok=True)

with open(os.path.join(HERE, "content.json"), encoding="utf-8") as f:
    C = json.load(f)

VOICES = C["voices"]
TTS = C.get("tts", {})
ZWNJ = "‌"

def h(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]

# ---- what the voice actually reads -------------------------------------------------------
# The display text stays unvowelled (that is what the learner must read). The voice gets a
# vowelled version where the plain spelling is ambiguous, plus a space before a suffix alef
# after a half-space (جعبه‌ای), which the voice otherwise runs together.
# A map value is either the vowelled text, or {"text": ..., "voice": "male"|"default"} when the
# isolated word clip should use a particular voice (sentences keep their own voice).
def tts_spelling(key):
    v = TTS[key]
    return v["text"] if isinstance(v, dict) else v

def tts_voice(text):
    v = TTS.get(text)
    return v.get("voice") if isinstance(v, dict) else None

# An entry with "solo": true is used only when the clip is exactly that word. Sentences that
# contain the word are left alone, since context already tells the voice how to read it.
_keys = sorted((k for k in TTS if not (isinstance(TTS[k], dict) and TTS[k].get("solo"))), key=len, reverse=True)
_pat = re.compile("(?<![؀-ۿ])(" + "|".join(re.escape(k) for k in _keys) + ")(?![؀-ۿ])") if _keys else None

def tts_text(text):
    t = text
    if text in TTS:
        t = tts_spelling(text)
    elif _pat:
        t = _pat.sub(lambda m: tts_spelling(m.group(1)), t)
    t = re.sub(ZWNJ + "(?=ا)", " ", t)
    t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", t)  # emoji
    return t.strip()

# ---- collect every string that needs a clip ----------------------------------------------
items = {}  # display text -> voice

def add(text, voice="default"):
    if not text or not isinstance(text, str):
        return
    if not re.search(r"[؀-ۿ]", text):
        return
    items.setdefault(text, voice)

for w in C["words"].values():
    add(w["fa"]); add(w.get("para"), w.get("para_voice", "default")); add(w.get("colloq"))
for p in C["pairs"]:
    add(p["words"][0]); add(p["words"][1])
for s in C["spell"]:
    add(s["word"])
for s in C["fixdots"]:
    add(s["correct"])
for s in C["dots"]:
    add(s["word"])
for s in C["register_mc"]:
    add(s["familier"]); add(s["correct"])
for s in C["register_build"]:
    add(s["familier"]); add(s["answer"])
for e in C["explain"].values():
    for a, b in e["examples"]:
        add(a); add(b)
for r in C["readings"].values():
    for para in r["paragraphs"]:
        for s in para:
            add(s)
    for q in r["questions"]:
        add(q["q"])
for ch in C["chats"].values():
    parts = ch["participants"]
    for m in ch["script"]:
        if "choice" in m:
            for c in m["choice"]:
                add(c["text"])
                for r in c.get("reply", []):  # the cousins' answer to that particular choice
                    add(r["text"], parts[r["from"]].get("voice", "default"))
        else:
            add(m["text"], parts[m["from"]].get("voice", "default"))
for m in C.get("mc", []):  # questions whose prompt is something heard
    add(m.get("audio"))
for k in C["feedback"]["good"] + C["feedback"]["bad"]:
    add(k)

for t in list(items):
    if tts_voice(t):
        items[t] = tts_voice(t)
print(f"{len(items)} audio strings")

manifest = {}
if os.path.exists(MANIFEST):
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

def needs(hash_, spoken, voice):
    path = os.path.join(AUDIO_DIR, hash_ + ".mp3")
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        return True
    return manifest.get(hash_) != voice + "|" + spoken

async def gen_one(sem, text, voice):
    import edge_tts
    hash_ = h(text); spoken = tts_text(text)
    if not needs(hash_, spoken, voice):
        return
    path = os.path.join(AUDIO_DIR, hash_ + ".mp3")
    async with sem:
        for attempt in range(4):
            try:
                comm = edge_tts.Communicate(spoken, VOICES[voice])
                await comm.save(path)
                if os.path.getsize(path) > 1000:
                    manifest[hash_] = voice + "|" + spoken
                    return
            except Exception:  # noqa
                await asyncio.sleep(1.5 * (attempt + 1))
        print("FAILED:", text)

async def tts_with_words(spoken, voice, path):
    """Write one slow clip and return the time of each word in it."""
    import edge_tts
    for attempt in range(4):
        try:
            comm = edge_tts.Communicate(spoken, VOICES[voice], rate="-12%", boundary="WordBoundary")
            words = []
            with open(path, "wb") as f:
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        words.append({"t": chunk["offset"] / 1e7, "d": chunk["duration"] / 1e7, "w": chunk["text"]})
            if os.path.getsize(path) > 1000 and words:
                return words
        except Exception:  # noqa
            pass
        await asyncio.sleep(1.5 * (attempt + 1))
    print("FAILED karaoke clip:", spoken)
    return []

async def gen_karaoke(kid, k):
    # One clip for the whole song, plus one clip per line: the learner reads a line, then hears it.
    spoken = tts_text("\n".join(k["lines"]))
    path = os.path.join(AUDIO_DIR, "karaoke_" + kid + ".mp3")
    tpath = os.path.join(AUDIO_DIR, "karaoke_" + kid + ".json")
    old = {}
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as f:
            old = json.load(f)
        if not isinstance(old, dict):
            old = {}
    data = {"tts": spoken, "words": old.get("words") or [], "lines": []}
    if not (os.path.exists(path) and old.get("tts") == spoken and data["words"]):
        data["words"] = await tts_with_words(spoken, "default", path)
    old_lines = old.get("lines") or []
    for i, line in enumerate(k["lines"]):
        sp = tts_text(line)
        lpath = os.path.join(AUDIO_DIR, "karaoke_%s_%d.mp3" % (kid, i))
        prev = old_lines[i] if i < len(old_lines) else None
        if prev and prev.get("tts") == sp and prev.get("words") and os.path.exists(lpath) and os.path.getsize(lpath) > 1000:
            data["lines"].append(prev)
        else:
            data["lines"].append({"tts": sp, "words": await tts_with_words(sp, "default", lpath)})
    with open(tpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

async def main():
    sem = asyncio.Semaphore(4)
    tasks = [gen_one(sem, t, v) for t, v in items.items()]
    tasks += [gen_karaoke(kid, k) for kid, k in C["karaoke"].items()]
    await asyncio.gather(*tasks)

if "--no-audio" not in sys.argv:
    todo = sum(1 for t, v in items.items() if needs(h(t), tts_text(t), v))
    print(f"{todo} clips to generate")
    asyncio.run(main())
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=0)

audio_map = {}
for t in items:
    p = os.path.join(AUDIO_DIR, h(t) + ".mp3")
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        # version tag from the spoken text, so a regenerated clip bypasses any cached copy
        audio_map[t] = "audio/" + h(t) + ".mp3?v=" + h(items[t] + "|" + tts_text(t))[:6]
print(f"{len(audio_map)} clips available")

kt = {}
for kid in C["karaoke"]:
    tpath = os.path.join(AUDIO_DIR, "karaoke_" + kid + ".json")
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {"tts": "", "words": data, "lines": []}
        kt[kid] = {"src": "audio/karaoke_" + kid + ".mp3?v=" + h(data.get("tts", ""))[:6], "words": data["words"],
                   "lines": [{"src": "audio/karaoke_%s_%d.mp3?v=%s" % (kid, i, h(ln.get("tts", ""))[:6]), "words": ln["words"]}
                             for i, ln in enumerate(data.get("lines", []))]}

with open(os.path.join(HERE, "content.js"), "w", encoding="utf-8") as f:
    f.write("window.CONTENT = " + json.dumps(C, ensure_ascii=False) + ";\n")
    f.write("window.AUDIO = " + json.dumps(audio_map, ensure_ascii=False) + ";\n")
    f.write("window.KARAOKE_TIMING = " + json.dumps(kt, ensure_ascii=False) + ";\n")
print("content.js written")

# check.js: every clip of the units listed in "check_units", grouped by lesson, so that a
# speaker can listen to a whole new day once (check.html) and tick what the voice gets wrong.
def lesson_clips(lesson):
    out = []
    def put(t):
        if t and isinstance(t, str) and t in audio_map and all(t != o["t"] for o in out):
            sp = tts_text(t)
            out.append({"t": t, "s": sp if sp != t else "", "v": "Farid" if items.get(t) == "male" else "Dilara", "src": audio_map[t]})
    def put_word(wid):
        w = C["words"][wid]; put(w["fa"]); put(w.get("colloq")); put(w.get("para"))
    for wid in lesson.get("words", []):
        put_word(wid)
    for e in lesson.get("exercises", []):
        t = e["type"]
        if t == "pair":
            for w in C["pairs"][e["pair"]]["words"]: put(w)
        elif t == "dots": put(C["dots"][e["item"]]["word"])
        elif t == "fixdots": put(C["fixdots"][e["item"]]["correct"])
        elif t == "spell": put(C["spell"][e["item"]]["word"])
        elif t == "register_mc": put(C["register_mc"][e["item"]]["familier"]); put(C["register_mc"][e["item"]]["correct"])
        elif t == "register_build": put(C["register_build"][e["item"]]["familier"]); put(C["register_build"][e["item"]]["answer"])
        elif t == "explain":
            for a, b in C["explain"][e["item"]]["examples"]: put(a); put(b)
        elif t == "mc": put(C["mc"][e["item"]].get("audio"))
        elif t == "build": put(C["words"][C["build"][e["item"]]["word"]]["fa"])
        elif t in ("vocab", "vocab_check", "vocab_check_rev"): put_word(e["word"])
    for rid in ([lesson["reading"]] if lesson.get("reading") else [v["reading"] for v in lesson.get("variants", [])]):
        r = C["readings"][rid]
        for para in r["paragraphs"]:
            for s in para: put(s)
        for q in r["questions"]: put(q["q"])
    if lesson.get("chat"):
        for m in C["chats"][lesson["chat"]]["script"]:
            if "choice" in m:
                for c in m["choice"]:
                    put(c["text"])
                    for r in c.get("reply", []): put(r["text"])
            else:
                put(m["text"])
    if lesson.get("karaoke") and lesson["karaoke"] in kt:
        for i, line in enumerate(C["karaoke"][lesson["karaoke"]]["lines"]):
            if i < len(kt[lesson["karaoke"]]["lines"]):
                sp = tts_text(line)
                out.append({"t": line, "s": sp if sp != line else "", "v": "Dilara", "src": kt[lesson["karaoke"]]["lines"][i]["src"]})
    return out

check, seen = [], set()
for unit in C["units"]:
    if unit["id"] not in C.get("check_units", []):
        continue
    for lesson in unit["lessons"]:
        clips = [c for c in lesson_clips(lesson) if c["t"] not in seen]
        seen.update(c["t"] for c in clips)
        if clips:
            check.append({"unit": unit["title"] + " · " + unit["subtitle"], "lesson": lesson["title"], "clips": clips})
import datetime
with open(os.path.join(HERE, "check.js"), "w", encoding="utf-8") as f:
    f.write("window.CHECK = " + json.dumps(check, ensure_ascii=False) + ";\n")
    f.write("window.CHECK_BUILT = " + json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + ";\n")
print("check.js written:", sum(len(g["clips"]) for g in check), "clips to listen to")

# artifact.html: the page body only, for publishing as a claude.ai artifact (which adds its own document skeleton)
with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
    page = f.read()
start = page.index("<!-- artifact-start -->") + len("<!-- artifact-start -->")
end = page.index("<!-- artifact-end -->")
with open(os.path.join(HERE, "artifact.html"), "w", encoding="utf-8") as f:
    f.write(page[start:end].strip() + "\n")
print("artifact.html written")
