#!/usr/bin/env python3
"""
CSIFY a GIF: pixelate + scanlines + subtle noise.
Usage:
  python tools/csify_gif.py input.gif output.gif
"""

import random
import sys
from typing import List
from PIL import Image, ImageDraw, ImageFilter, ImageSequence

CS_BG = (0x2B, 0x32, 0x28)  # #2b3228


def clamp(channel: int) -> int:
    return max(0, min(255, channel))


def csify_frame(im: Image.Image) -> Image.Image:
    frame = im.convert("RGBA")

    bg = Image.new("RGBA", frame.size, CS_BG + (255,))
    frame = Image.alpha_composite(bg, frame)

    w, h = frame.size

    small = frame.resize((max(1, w // 2), max(1, h // 2)), Image.BILINEAR)
    frame = small.resize((w, h), Image.NEAREST)

    scan = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(scan)
    for y in range(0, h, 3):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 22))
    frame = Image.alpha_composite(frame, scan)

    px = frame.load()
    for _ in range(int(w * h * 0.01)):
        x = random.randrange(w)
        y = random.randrange(h)
        r, g, b, a = px[x, y]
        delta = random.randint(-10, 10)
        px[x, y] = (
            clamp(r + delta),
            clamp(g + delta),
            clamp(b + delta),
            a,
        )

    return frame.filter(ImageFilter.UnsharpMask(radius=1.1, percent=120, threshold=3))


def main(argv: List[str]) -> int:
    if len(argv) != 3:
        print("Usage: python tools/csify_gif.py input.gif output.gif")
        return 2

    in_path, out_path = argv[1], argv[2]
    im = Image.open(in_path)

    frames = []
    durations = []
    loop = im.info.get("loop", 0)

    for fr in ImageSequence.Iterator(im):
        durations.append(fr.info.get("duration", 80))
        cs_frame = csify_frame(fr)
        frames.append(cs_frame.convert("P", palette=Image.ADAPTIVE, colors=256))

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop,
        optimize=True,
        disposal=2,
    )

    print(f"CSified GIF written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
