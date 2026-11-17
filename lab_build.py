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
ROUND = 9  # bump when the candidates change; shown at the top of lab.html
AYA, MI, MID = 'آیا', 'می‌شود', ' تخفیف بِدَ'
END50, END30 = ('هید؟', '+50%'), ('هید؟', '+30%')
GROUPS = [
    # round 9: after round 8 (D best, none great). The opening word sounded like an assertion,
    # and the sentence should start with آیا. Farid, last syllable raised as in round 8 D.
    ('آیا می‌شود تخفیف بدهید؟',
     "le ton d'une question, avec آیا en tête et la voix de Farid (ton choix D). Cette fois le début de la phrase est touché aussi : "
     "dit plus haut (A, B, C, E) ou avec la fin de می‌شود qui monte (D). F sert de repère : la fin de la série 8, sans toucher au début. "
     "Si aucune n'est vraiment bonne, la phrase reste sans son",
     [([(AYA + ' ' + MI, '+20%'), MID, END50], 'farid', 'début un peu plus haut, dernière syllabe haute'),
      ([(AYA + ' ' + MI, '+35%'), MID, END50], 'farid', 'début nettement plus haut, dernière syllabe haute'),
      ([AYA + ' ', (MI, '+35%'), MID, END50], 'farid', 'seul می‌شود plus haut, dernière syllabe haute'),
      ([AYA + ' می‌شَ', ('وَد', '+35%'), MID, END50], 'farid', 'la fin de می‌شود monte, dernière syllabe haute'),
      ([(AYA + ' ' + MI, '+25%'), MID, END30], 'farid', 'début plus haut, dernière syllabe un peu haute'),
      ([AYA + ' ' + MI + MID, END50], 'farid', 'repère : début non touché, dernière syllabe haute')]),
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
