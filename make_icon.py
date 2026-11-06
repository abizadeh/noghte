# Draws the app icon: a cobalt tile, a white tooth stroke (the skeleton of ب) and a saffron dot.
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

def make(size, name):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=(36, 87, 197, 255))
    # tooth stroke: a wide bowl, like the body of ب
    w = int(s * 0.11)
    box = [int(s * 0.16), int(s * 0.10), int(s * 0.84), int(s * 0.66)]
    d.arc(box, start=20, end=160, fill=(255, 255, 255, 255), width=w)
    # saffron dot below the bowl
    r = int(s * 0.085)
    cx, cy = s // 2, int(s * 0.80)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(242, 164, 28, 255))
    img.save(os.path.join(HERE, name))

make(180, "icon-180.png")
make(512, "icon-512.png")
print("icons written")
