# Pronunciation lab: generates several candidate readings of each problem word so a
# native ear can pick the right one. Output: audio/lab/*.mp3 and lab.js, used by lab.html.
# Usage: python lab_build.py
import asyncio, datetime, hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "audio", "lab")
os.makedirs(OUT, exist_ok=True)
VOICES = {"dilara": "fa-IR-DilaraNeural", "farid": "fa-IR-FaridNeural"}

# word shown to the learner -> candidates. A candidate is (text the voice reads, voice), or
# (text with a | before the part to raise, voice, pitch of that part[, its speed]): see twopart.py.
ROUND = 8  # bump when the candidates change; shown at the top of lab.html
Q = 'می‌شود تخفیف '
GROUPS = [
    # round 8: the question that still sounded like a statement. The voice never ends a question
    # high by itself (measured), so the end is raised by hand.
    ('می‌شود تخفیف بدهید؟',
     "le ton d'une question. Cette voix ne monte jamais d'elle-même à la fin d'une question : ici je la force. "
     "De A à D, seule la dernière syllabe (-hid) est dite plus haut, après un creux : c'est la forme que décrivent les études sur l'intonation du persan. "
     "Pour E et F, tout le dernier mot est dit plus haut. Vérifie aussi que بدهید reste bien prononcé, car il est coupé en deux pour la voix",
     [(Q + 'بِدَ|هید؟', 'dilara', '+30%'), (Q + 'بِدَ|هید؟', 'dilara', '+50%'), (Q + 'بِدَ|هید؟', 'dilara', '+50%', '-20%'),
      (Q + 'بِدَ|هید؟', 'farid', '+50%'), (Q + '|بدهید؟', 'dilara', '+35%'), (Q + '|بدهید؟', 'dilara', '+50%')]),
]

def h(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]

def parts(v):
    return v[0], v[1], (v[2] if len(v) > 2 else None), (v[3] if len(v) > 3 else "+0%")

def clip(v):
    text, voice, pitch, rate = parts(v)
    return h(voice + "|" + text + ("|" + pitch + "|" + rate if pitch else "")) + ".mp3"

def voice_label(v):
    text, voice, pitch, rate = parts(v)
    if not pitch:
        return voice
    what = "dernier mot plus haut" if text[text.index("|") - 1] == " " else "dernière syllabe plus haute"
    return voice + " · " + what + " (" + pitch + ")" + (", plus lente" if rate != "+0%" else "")

async def gen(sem, v):
    import edge_tts
    text, voice, pitch, rate = parts(v)
    path = os.path.join(OUT, clip(v))
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return
    async with sem:
        for attempt in range(4):
            try:
                if pitch:
                    from twopart import save_two_part
                    await save_two_part(text, VOICES[voice], path, pitch, rate)
                else:
                    await edge_tts.Communicate(text, VOICES[voice]).save(path)
                if os.path.getsize(path) > 1000:
                    return
            except RuntimeError:
                raise
            except Exception:
                await asyncio.sleep(1.5 * (attempt + 1))
        print("FAILED", text, voice)

async def main():
    sem = asyncio.Semaphore(4)
    await asyncio.gather(*[gen(sem, v) for _, _, vs in GROUPS for v in vs])

asyncio.run(main())
lab = []
for word, latin, vs in GROUPS:
    lab.append({"word": word, "latin": latin, "variants": [
        {"label": chr(65 + i), "text": v[0].replace("|", ""), "voice": voice_label(v), "src": "audio/lab/" + clip(v)} for i, v in enumerate(vs)]})
with open(os.path.join(HERE, "lab.js"), "w", encoding="utf-8") as f:
    f.write("window.LAB = " + json.dumps(lab, ensure_ascii=False) + ";\n")
    f.write("window.LAB_ROUND = " + json.dumps(ROUND) + ";\n")
    f.write("window.LAB_BUILT = " + json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + ";\n")
print("lab.js written,", sum(len(g[2]) for g in GROUPS), "clips")
