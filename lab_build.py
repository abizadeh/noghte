# Pronunciation lab: generates several candidate readings of each problem word so a
# native ear can pick the right one. Output: audio/lab/*.mp3 and lab.js, used by lab.html.
# Usage: python lab_build.py
import asyncio, datetime, hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "audio", "lab")
os.makedirs(OUT, exist_ok=True)
VOICES = {"dilara": "fa-IR-DilaraNeural", "farid": "fa-IR-FaridNeural"}

# word shown to the learner -> candidates. A candidate is (text the voice reads, voice), or
# (parts, voice, note) where parts is a sentence with raised stretches (see raised.py) and note
# says in French what was raised.
ROUND = 10  # bump when the candidates change; shown at the top of lab.html
OPEN = ('آیا می‌شود', '+35%')   # round 9 B: the opening clearly higher
GROUPS = [
    # round 10: round 9 B was the best, but every round 9 reading said "bedhid" for بدهید.
    # Measured: splitting the word as بِدَ + هید drops the middle vowel (two vowel peaks instead
    # of three). Splitting after بِ, or not splitting, keeps be-da-hid.
    ('آیا می‌شود تخفیف بدهید؟',
     "le début de la série 9 B (Farid, début nettement plus haut), avec بدهید dit en entier. Tu avais raison : mes mesures montrent que la série 9 "
     "avalait une syllabe (« bedhid »). Ces quatre-ci gardent les trois syllabes be-da-hid. A et B : le mot est coupé après بِ pour la voix et « dahid » est dit plus haut. "
     "C et D : le mot n'est pas coupé, il est dit plus haut en entier. La fin monte moins que dans la série 9 : c'est le prix pour garder le mot intact",
     [([OPEN, ' تخفیف بِ', ('دَهید؟', '+50%')], 'farid', '« dahid » plus haut'),
      ([OPEN, ' تخفیف بِ', ('دَهید؟', '+50%', '-15%')], 'farid', '« dahid » plus haut et plus lent'),
      ([OPEN, ' تخفیف ', ('بدهید؟', '+50%')], 'farid', 'tout le dernier mot nettement plus haut'),
      ([OPEN, ' تخفیف ', ('بدهید؟', '+35%')], 'farid', 'tout le dernier mot un peu plus haut')]),
]

def h(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]

def raised(v):
    return not isinstance(v[0], str)

def spoken(v):
    return "".join(p if isinstance(p, str) else p[0] for p in v[0]) if raised(v) else v[0]

def clip(v):
    return h(v[1] + "|" + (json.dumps(v[0], ensure_ascii=False) if raised(v) else v[0])) + ".mp3"

async def gen(sem, v):
    import edge_tts
    path = os.path.join(OUT, clip(v))
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return
    async with sem:
        for attempt in range(4):
            try:
                if raised(v):
                    from raised import save_raised
                    await save_raised(v[0], VOICES[v[1]], path)
                else:
                    await edge_tts.Communicate(v[0], VOICES[v[1]]).save(path)
                if os.path.getsize(path) > 1000:
                    return
            except (RuntimeError, ValueError):
                raise
            except Exception:
                await asyncio.sleep(1.5 * (attempt + 1))
        print("FAILED", spoken(v), v[1])

async def main():
    sem = asyncio.Semaphore(4)
    await asyncio.gather(*[gen(sem, v) for _, _, vs in GROUPS for v in vs])

asyncio.run(main())
lab = []
for word, latin, vs in GROUPS:
    lab.append({"word": word, "latin": latin, "variants": [
        {"label": chr(65 + i), "text": spoken(v), "voice": v[1] + (" · " + v[2] if raised(v) else ""), "src": "audio/lab/" + clip(v)} for i, v in enumerate(vs)]})
with open(os.path.join(HERE, "lab.js"), "w", encoding="utf-8") as f:
    f.write("window.LAB = " + json.dumps(lab, ensure_ascii=False) + ";\n")
    f.write("window.LAB_ROUND = " + json.dumps(ROUND) + ";\n")
    f.write("window.LAB_BUILT = " + json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + ";\n")
print("lab.js written,", sum(len(g[2]) for g in GROUPS), "clips")
