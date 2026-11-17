# Reads and writes content.json in the project's layout: compact, one entry per line where it fits.
# Use it from any script that changes the content:
#     from contentfmt import load, dump
#     C = load(); ...; dump(C)
# Run directly to reformat the file in place:  python contentfmt.py
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "content.json")

def fmt(o, ind=0, width=190):
    s = json.dumps(o, ensure_ascii=False)
    pad = "  " * ind
    if not isinstance(o, (dict, list)) or not o or len(s) + len(pad) <= width:
        return s
    if isinstance(o, dict):
        parts = [pad + "  " + json.dumps(k, ensure_ascii=False) + ": " + fmt(v, ind + 1, width) for k, v in o.items()]
        return "{\n" + ",\n".join(parts) + "\n" + pad + "}"
    parts = [pad + "  " + fmt(v, ind + 1, width) for v in o]
    return "[\n" + ",\n".join(parts) + "\n" + pad + "]"

def load():
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)

def dump(C):
    out = fmt(C) + "\n"
    assert json.loads(out) == C
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(out)

if __name__ == "__main__":
    dump(load())
    print("content.json reformatted")
