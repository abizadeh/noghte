# Builds content.js (data + audio map + karaoke timings) and generates the Persian audio clips.
# Usage: python build.py            -> generates missing audio, writes content.js
#        python build.py --no-audio -> only writes content.js from what exists
import asyncio, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(HERE, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

with open(os.path.join(HERE, "content.json"), encoding="utf-8") as f:
    C = json.load(f)

VOICES = C["voices"]

def h(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]

items = {}  # text -> voice

def add(text, voice="default"):
    if not text or not isinstance(text, str):
        return
    if not re.search(r"[؀-ۿ]", text):
        return
    items.setdefault(text, voice)

for w in C["words"].values():
    add(w["fa"]); add(w.get("para")); add(w.get("colloq"))
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
        else:
            add(m["text"], parts[m["from"]].get("voice", "default"))
for k in C["feedback"]["good"] + C["feedback"]["bad"]:
    add(k)

print(f"{len(items)} audio strings")

def clean_for_tts(text):
    # Remove emoji; keep Persian punctuation.
    return re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", text).strip()

async def gen_one(sem, text, voice):
    import edge_tts
    path = os.path.join(AUDIO_DIR, h(text) + ".mp3")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return
    async with sem:
        for attempt in range(4):
            try:
                comm = edge_tts.Communicate(clean_for_tts(text), VOICES[voice])
                await comm.save(path)
                if os.path.getsize(path) > 1000:
                    return
            except Exception as e:  # noqa
                await asyncio.sleep(1.5 * (attempt + 1))
        print("FAILED:", text)

async def gen_karaoke(kid, k):
    import edge_tts
    text = "\n".join(k["lines"])
    path = os.path.join(AUDIO_DIR, "karaoke_" + kid + ".mp3")
    tpath = os.path.join(AUDIO_DIR, "karaoke_" + kid + ".json")
    if os.path.exists(path) and os.path.exists(tpath):
        return
    comm = edge_tts.Communicate(text, VOICES["default"], rate="-12%", boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"t": chunk["offset"] / 1e7, "d": chunk["duration"] / 1e7, "w": chunk["text"]})
    with open(tpath, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)

async def main():
    sem = asyncio.Semaphore(4)
    tasks = [gen_one(sem, t, v) for t, v in items.items()]
    tasks += [gen_karaoke(kid, k) for kid, k in C["karaoke"].items()]
    await asyncio.gather(*tasks)

if "--no-audio" not in sys.argv:
    asyncio.run(main())

audio_map = {}
for t in items:
    p = os.path.join(AUDIO_DIR, h(t) + ".mp3")
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        audio_map[t] = "audio/" + h(t) + ".mp3"
print(f"{len(audio_map)} clips available")

kt = {}
for kid in C["karaoke"]:
    tpath = os.path.join(AUDIO_DIR, "karaoke_" + kid + ".json")
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as f:
            kt[kid] = {"src": "audio/karaoke_" + kid + ".mp3", "words": json.load(f)}

with open(os.path.join(HERE, "content.js"), "w", encoding="utf-8") as f:
    f.write("window.CONTENT = " + json.dumps(C, ensure_ascii=False) + ";\n")
    f.write("window.AUDIO = " + json.dumps(audio_map, ensure_ascii=False) + ";\n")
    f.write("window.KARAOKE_TIMING = " + json.dumps(kt, ensure_ascii=False) + ";\n")
print("content.js written")

# artifact.html: the page body only, for publishing as a claude.ai artifact (which adds its own document skeleton)
with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
    page = f.read()
start = page.index("<!-- artifact-start -->") + len("<!-- artifact-start -->")
end = page.index("<!-- artifact-end -->")
with open(os.path.join(HERE, "artifact.html"), "w", encoding="utf-8") as f:
    f.write(page[start:end].strip() + "\n")
print("artifact.html written")
