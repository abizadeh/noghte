# Pronunciation lab: generates several candidate readings of each problem word so a
# native ear can pick the right one. Output: audio/lab/*.mp3 and lab.js, used by lab.html.
# Usage: python lab_build.py
import asyncio, hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "audio", "lab")
os.makedirs(OUT, exist_ok=True)
VOICES = {"dilara": "fa-IR-DilaraNeural", "farid": "fa-IR-FaridNeural"}

# word shown to the learner -> candidate (text the voice reads, voice)
GROUPS = [
    # round 2: the h of گیاه must be heard before خوار
    ("گیاه‌خوار", "giyāh-khār", [("گیاهْ‌خوار", "dilara"), ("گیاهْ خوار", "dilara"), ("گیاح‌خوار", "dilara"), ("گیاح خوار", "dilara"), ("گیاهْ‌خوار", "farid"), ("گیاح‌خوار", "farid"), ("گیاهه خوار", "dilara")]),
    ("من گیاه‌خوارم.", "man giyāh-khāram", [("من گیاهْ‌خوارَم.", "dilara"), ("من گیاح‌خوارَم.", "dilara"), ("من گیاهْ‌خوارَم.", "farid"), ("من گیاح‌خوارَم.", "farid")]),
]

def h(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]

async def gen(sem, text, voice):
    import edge_tts
    path = os.path.join(OUT, h(voice + "|" + text) + ".mp3")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return
    async with sem:
        for attempt in range(4):
            try:
                await edge_tts.Communicate(text, VOICES[voice]).save(path)
                if os.path.getsize(path) > 1000:
                    return
            except Exception:
                await asyncio.sleep(1.5 * (attempt + 1))
        print("FAILED", text, voice)

async def main():
    sem = asyncio.Semaphore(4)
    await asyncio.gather(*[gen(sem, t, v) for _, _, vs in GROUPS for t, v in vs])

asyncio.run(main())
lab = []
for word, latin, vs in GROUPS:
    lab.append({"word": word, "latin": latin, "variants": [
        {"label": chr(65 + i), "text": t, "voice": v, "src": "audio/lab/" + h(v + "|" + t) + ".mp3"} for i, (t, v) in enumerate(vs)]})
with open(os.path.join(HERE, "lab.js"), "w", encoding="utf-8") as f:
    f.write("window.LAB = " + json.dumps(lab, ensure_ascii=False) + ";\n")
print("lab.js written,", sum(len(g[2]) for g in GROUPS), "clips")
