# Speaks one sentence with up to two stretches at their own pitch (and speed).
#
# Why: the fa-IR voices never end a yes/no question high. Measured on every question clip of the
# app, the pitch always falls at the end; on a formal question like می‌شود تخفیف بدهید؟ it falls as
# steeply as in a statement, and the opening word sounds like an assertion. Research on Persian
# intonation (Sadat-Tehrani 2011, Sadeghi 2021) describes yes/no questions as ending on a high
# boundary tone after a low, with higher accents overall. Punctuation, آیا, a tag word or a cut
# clip do not get that from the voice. The service refuses a pitch curve and refuses three
# prosody elements, but it accepts two of them with plain text around, so two stretches can be
# raised: the opening, and the last word or only its last syllable.
#
# A sentence is a list of parts: plain text, or (text, pitch[, rate]) for a raised stretch, e.g.
#   [("آیا می‌شود", "+25%"), " تخفیف بِدَ", ("هید؟", "+50%")]
# Pitch above +50% changes nothing. A word split between two parts is read as two tokens, so
# write the first half with its vowels (بِدَ + هید) and let a native ear check the result.
#
# This leans on an internal of edge-tts (the module-level mkssml used by Communicate.stream),
# checked with edge-tts 7.3.1. If the library changes, save_raised raises instead of quietly
# writing an ordinary clip.
import asyncio
from xml.sax.saxutils import escape

import edge_tts
from edge_tts import communicate as _c

_orig = _c.mkssml
_spec = {}   # escaped full text -> [parts, used]
_lock = None

def plain(parts):
    return "".join(p if isinstance(p, str) else p[0] for p in parts)

def _mkssml(tc, escaped_text):
    t = escaped_text.decode("utf-8") if isinstance(escaped_text, bytes) else escaped_text
    s = _spec.get(t)
    if not s:
        return _orig(tc, escaped_text)
    s[1] = True
    inner = "".join(escape(p) if isinstance(p, str) else
                    "<prosody pitch='%s' rate='%s' volume='%s'>%s</prosody>" % (p[1], p[2] if len(p) > 2 else "+0%", tc.volume, escape(p[0]))
                    for p in s[0])
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>"
            f"<voice name='{tc.voice}'>" + inner + "</voice></speak>")

_c.mkssml = _mkssml

async def save_raised(parts, voice_name, path):
    global _lock
    if sum(1 for p in parts if not isinstance(p, str)) > 2:
        raise ValueError("the service accepts at most two raised stretches")
    if _lock is None:
        _lock = asyncio.Lock()
    key = escape(plain(parts))
    async with _lock:  # one at a time: two readings of the same sentence share the key
        _spec[key] = [parts, False]
        try:
            await edge_tts.Communicate(plain(parts), voice_name).save(path)
            if not _spec[key][1]:
                raise RuntimeError("raised request was not used: edge-tts internals changed")
        finally:
            _spec.pop(key, None)
