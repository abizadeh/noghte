# Pronunciation lab: generates several candidate readings of each problem word so a
# native ear can pick the right one. Output: audio/lab/*.mp3 and lab.js, used by lab.html.
# Usage: python lab_build.py
import asyncio, datetime, hashlib, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "audio", "lab")
os.makedirs(OUT, exist_ok=True)
VOICES = {"dilara": "fa-IR-DilaraNeural", "farid": "fa-IR-FaridNeural"}

# word shown to the learner -> candidate (text the voice reads, voice)
ROUND = 6  # bump when the candidates change; shown at the top of lab.html
GROUPS = [
    # round 6: clips flagged in the first listening pass on Days 3 and 4
    ('توت\u200cفرنگی', 'tut-farangi (pas « tute frangi »). A = version actuelle', [('توت\u200cفرنگی', 'dilara'), ('توت فَرَنگی', 'dilara'), ('توتفَرَنگی', 'dilara'), ('توت\u200cفَرَنگی', 'dilara'), ('توت\u200cفرنگی', 'farid'), ('توت فَرَنگی', 'farid')]),
    ('هفده', 'hefdah (pas « hefde »). A = version actuelle', [('هفده', 'dilara'), ('هِفدَه', 'dilara'), ('هفدَه', 'dilara'), ('هیفدَه', 'dilara'), ('هفده', 'farid'), ('هِفدَه', 'farid')]),
    ('میوه\u200cفروشی', 'mive-forushi (pas « mivah frushi »). A = version actuelle', [('میوه\u200cفروشی', 'dilara'), ('میوه فُروشی', 'dilara'), ('میوِه\u200cفُروشی', 'dilara'), ('میوِ فُروشی', 'dilara'), ('میوه\u200cفروشی', 'farid'), ('میوه فُروشی', 'farid')]),
    ('سارا از میوه\u200cفروش پرسید: «انار کیلویی چند است؟»', 'mive-forush sans « h », et anâr kiluyi sans « e » entre les deux. A = version actuelle', [('سارا از میوه\u200cفروش پرسید: «انار کیلویی چند است؟»', 'dilara'), ('سارا از میوه فُروش پرسید: «انار، کیلویی چند است؟»', 'dilara'), ('سارا از میوِ فُروش پرسید: «انار، کیلویی چند است؟»', 'dilara'), ('سارا از میوِه\u200cفُروش پرسید: «انار کیلویی، چند است؟»', 'dilara')]),
    ('ریحان', 'reyhân (pas « rihan »). A = version actuelle', [('ریحان', 'dilara'), ('رِیحان', 'dilara'), ('رَیحان', 'dilara'), ('ریحان', 'farid'), ('رِیحان', 'farid')]),
    ('مشتری', 'moshtari, accent sur la fin. A = version actuelle', [('مشتری', 'dilara'), ('مُشتَری', 'dilara'), ('مشتری', 'farid'), ('مُشتَری', 'farid')]),
    ('می\u200cشود تخفیف بدهید؟', "avec le ton d'une question. A = version actuelle", [('می\u200cشود تخفیف بدهید؟', 'dilara'), ('می\u200cشود تخفیف بدهید?', 'dilara'), ('می\u200cشود تخفیف بدهید؟', 'farid'), ('می\u200cشود تخفیف بدهید?', 'farid')]),
    ('ترکیبات: آرد، شکر، روغن گیاهی', 'ârd (pas « ârad »). A = version actuelle', [('ترکیبات: آرد، شکر، روغن گیاهی', 'dilara'), ('ترکیبات: آرْد، شکر، روغن گیاهی', 'dilara'), ('ترکیبات: آرْدْ، شکر، روغن گیاهی', 'dilara')]),
    ('بازیکن', 'bâzikon, accent sur la fin. A = version actuelle', [('بازیکن', 'dilara'), ('بازی\u200cکن', 'dilara'), ('بازیکُن', 'dilara'), ('بازیکن', 'farid'), ('بازیکُن', 'farid')]),
    ('ترانه', 'tarâne, accent sur la fin. A = version actuelle', [('ترانه', 'dilara'), ('تَرانه', 'dilara'), ('ترانه', 'farid'), ('تَرانه', 'farid')]),
    ('افتخار', 'eftekhâr (pas « eftkhâr »). A = version actuelle', [('افتخار', 'dilara'), ('اِفتِخار', 'dilara'), ('افتِخار', 'dilara'), ('افتخار', 'farid'), ('اِفتِخار', 'farid')]),
    ('بالاخره', 'belakhare (pas « bâlâkhare »). A = version actuelle', [('بالاخره', 'dilara'), ('بلاخره', 'dilara'), ('بِلَخَره', 'dilara'), ('بِلاخَره', 'dilara'), ('بالاخره', 'farid'), ('بلاخره', 'farid')]),
    ('بالاخره برق آمد و پایان فیلم را دیدیم.', 'le même mot dans une phrase. A = version actuelle', [('بالاخره برق آمد و پایان فیلم را دیدیم.', 'dilara'), ('بلاخره برق آمد و پایان فیلم را دیدیم.', 'dilara'), ('بِلَخَره برق آمد و پایان فیلم را دیدیم.', 'dilara'), ('بِلاخَره برق آمد و پایان فیلم را دیدیم.', 'dilara')]),
    ('تو خونه دیدمش.', 'didamesh (pas « didemesh »). A = version actuelle', [('تو خونِه دیدمش.', 'dilara'), ('تو خونِه دیدَمِش.', 'dilara'), ('تو خونِه دیدَمش.', 'dilara'), ('تو خونه دیدَمِش.', 'farid')]),
    ('سبزیِ خوش\u200cبو که با غذا می\u200cخورند.', 'définition de ریحان : sabzi-ye khoshbu. C change la formulation. A = version actuelle', [('سبزیِ خوش\u200cبو که با غذا می\u200cخورند.', 'dilara'), ('سبزی\u200cیه خوش\u200cبو که با غذا می\u200cخورند.', 'dilara'), ('یک سبزی که بوی خوبی دارد و با غذا می\u200cخورند.', 'dilara')]),
    ('یعنی «مرسی»، با ادبِ بیشتر.', 'définition de متشکرم : mersi, et adab-e bishtar. C change la formulation. A = version actuelle', [('یعنی «مرسی»، با ادبِ بیشتر.', 'dilara'), ('یعنی «مِرسی»، با اَدَبه بیشتر.', 'dilara'), ('یعنی «مِرسی»، ولی مؤدبانه\u200cتر.', 'dilara')]),
    ('حسی که قبل از یک اتفاقِ مهم داری. قلبت تند می\u200cزند.', 'définition de هیجان : une pause après داری, et tond (pas « tand »)', [('حسی که قبل از یک اتفاقِ مهم داری. قلبت تُند می\u200cزند.', 'dilara'), ('حسی که قبل از یک اتفاقه مهم داری. قلبت تُند می\u200cزند.', 'dilara'), ('حسی که قبل از یک اتفاقِ مهم داری. قلبت توند می\u200cزند.', 'dilara')]),
    ('عالیه! من عاشق فلافلم', 'âsheq-e falâfelam, avec le « e ». A = version actuelle', [('عالیه! من عاشِق فلافلم', 'farid'), ('عالیه! من عاشقه فلافلم', 'farid'), ('عالیه! من عاشِقِ فلافلم', 'farid')]),
    ('شیرینیش گیاهی باشه ها!', 'shirinish giyâhi, sans « e » entre les deux. A = version actuelle', [('شیرینیش گیاهی باشه ها!', 'dilara'), ('شیرینیش، گیاهی باشه ها!', 'dilara'), ('شیرینی\u200cش گیاهی باشه ها!', 'dilara')]),
    ('ساعت ده خوبه؟', "sâ'at-e dah, avec le « e ». A = version actuelle", [('ساعَت ده خوبه؟', 'dilara'), ('ساعته ده خوبه؟', 'dilara'), ('ساعَتِ ده خوبه؟', 'dilara'), ('ساعته ده خوبه?', 'dilara')]),
    ('پس، فردا ساعت ده، دم در خونه\u200cی ما.', "sâ'at-e dah, dam-e dar-e khune-ye mâ. A = version actuelle", [('پس، فردا ساعَت ده، دم در خونِه\u200cی ما.', 'dilara'), ('پس، فردا ساعته ده، دمه دره خونه\u200cی ما.', 'dilara'), ('پس، فردا ساعَتِ ده، دَمِ دَرِ خونه\u200cی ما.', 'dilara')]),
    ('فیلم زیرنویس نداشت، اما من بیشتر حرف\u200cها را فهمیدم.', 'bishtar-e harfhâ, avec le « e ». A = version actuelle', [('فیلم زیرنویس نداشت، اَمّا من بیشتر حرف\u200cها را فهمیدم.', 'dilara'), ('فیلم زیرنویس نداشت، اَمّا من بیشتره حرف\u200cها را فهمیدم.', 'dilara'), ('فیلم زیرنویس نداشت، اَمّا من بیشترِ حرف\u200cها را فهمیدم.', 'dilara')]),
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
    f.write("window.LAB_ROUND = " + json.dumps(ROUND) + ";\n")
    f.write("window.LAB_BUILT = " + json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + ";\n")
print("lab.js written,", sum(len(g[2]) for g in GROUPS), "clips")
