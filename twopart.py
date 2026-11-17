# Speaks one sentence in two parts, the second at its own pitch and speed.
#
# Why: the fa-IR voices never end a yes/no question high. Measured on every question clip of the
# app, the pitch always falls at the end; on a formal question like می‌شود تخفیف بدهید؟ it falls as
# steeply as in a statement. Research on Persian intonation (Sadat-Tehrani 2011, Sadeghi 2021)
# describes yes/no questions as ending on a high boundary tone after a low, with a higher last
# accent. Punctuation, آیا, a tag word or a cut clip do not get that from the voice. The service
# refuses a pitch curve, but it accepts two prosody elements side by side, so the end of the
# sentence can be raised: the whole last word, or only its last syllable (بِدَ|هید؟).
#
# The text carries a | where the raised part begins. A word split by the | is read as two tokens,
# so write the first half with its vowels (بِدَ) and let a native ear check the result.
#
# This leans on an internal of edge-tts (the module-level mkssml used by Communicate.stream),
# checked with edge-tts 7.3.1. If the library changes, save_two_part raises instead of quietly
# writing an ordinary clip.
import asyncio
from xml.sax.saxutils import escape

import edge_tts
from edge_tts import communicate as _c

_orig = _c.mkssml
_spec = {}   # escaped full text -> [escaped head, escaped tail, pitch, rate, used]
_lock = None

def _mkssml(tc, escaped_text):
    t = escaped_text.decode("utf-8") if isinstance(escaped_text, bytes) else escaped_text
    s = _spec.get(t)
    if not s:
        return _orig(tc, escaped_text)
    s[4] = True
    return ("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>"
            f"<voice name='{tc.voice}'>"
            f"<prosody pitch='{tc.pitch}' rate='{tc.rate}' volume='{tc.volume}'>{s[0]}</prosody>"
            f"<prosody pitch='{s[2]}' rate='{s[3]}' volume='{tc.volume}'>{s[1]}</prosody>"
            "</voice></speak>")

_c.mkssml = _mkssml

async def save_two_part(text, voice_name, path, pitch, rate="+0%"):
    """text holds one | ; what follows it is spoken at `pitch` (at most +50%) and `rate`."""
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    head, tail = text.split("|")
    key = escape(head + tail)
    async with _lock:  # one at a time: two variants of the same sentence share the key
        _spec[key] = [escape(head), escape(tail), pitch, rate, False]
        try:
            await edge_tts.Communicate(head + tail, voice_name).save(path)
            if not _spec[key][4]:
                raise RuntimeError("two-part request was not used: edge-tts internals changed")
        finally:
            _spec.pop(key, None)
