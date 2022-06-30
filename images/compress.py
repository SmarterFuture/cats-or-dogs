import os

from PIL import Image


def compress(name, path, source):
    q = 85

    img = Image.open(source)
    if os.path.getsize(source) > 500000:
        q = 70

    h, w = img.size
    if (h + w) >= 5000:
        h, w = (2000, w * 2000 // h) if h >= w else (h * 2000 // w, 2000)
        img = img.resize((h, w), Image.ANTIALIAS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(f"{path}{name}.jpg", quality=q, optimize=True)
    img.close()

    if os.path.getsize(f"{path}{name}.jpg") > os.path.getsize(source):
        os.replace(source, f"{path}{name}.jpg")


for i in range(100):
    compress(i, "cats\\",  f"cats\\{i}r.jpg")
