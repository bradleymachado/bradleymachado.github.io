#!/usr/bin/env python3
"""One-off pass: resize + convert img/*.{jpg,png} to WebP alongside the originals.

Long edge capped at 1800px (skipped if already smaller). Quality 82 for photos/
renders, 88 for images classified as line art, diagrams, or text-bearing (see
HIGH_QUALITY below) since softness shows there. method=6 (slowest, best
compression). EXIF is stripped by never forwarding source image.info to save().
"""

from pathlib import Path
from PIL import Image

IMG_DIR = Path(__file__).parent / "img"
MAX_EDGE = 1800
Q_DEFAULT = 82
Q_HIGH = 88

# Line art / diagrams / text-bearing images -- classified by inspection.
HIGH_QUALITY = {
    "r01-hvac-rightsizing-01.png",       # infographic, heavy text
    "r02-aem-surveying-01.jpg",          # topo map, heavy text
    "r03-contextual-water-security-01.png",  # icon/logo mark with wordmark
    "w02-artificial-context-03.jpg",     # Grasshopper canvas screenshot, tiny text
    "w02-artificial-context-04.png",     # thin wireframe line art
    "w03-hub-boriken-02.png",            # hand sketch, annotated
    "w03-hub-boriken-03.png",            # hand sketch, annotated
    "w03-hub-boriken-04.jpg",            # hand sketch, annotated
    "w03-hub-boriken-05.jpg",            # hand sketch, annotated
    "w03-hub-boriken-11.jpg",            # labeled axon diagram
    "w03-hub-boriken-12.jpg",            # labeled site diagram
    "w04-cyprus-cove-02.png",            # fine wireframe model linework
    "w04-cyprus-cove-03.png",            # floor plan, room labels
    "w04-cyprus-cove-04.png",            # line-drawn section
}


def process(path):
    img = Image.open(path)

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    w, h = img.size
    long_edge = max(w, h)
    if long_edge > MAX_EDGE:
        scale = MAX_EDGE / long_edge
        img = img.resize((round(w * scale), round(h * scale)), Image.Resampling.LANCZOS)

    quality = Q_HIGH if path.name in HIGH_QUALITY else Q_DEFAULT
    out_path = path.with_suffix(".webp")
    img.save(out_path, "WEBP", quality=quality, method=6)
    return out_path, quality


def main():
    rows = []
    total_before = total_after = 0

    for path in sorted(IMG_DIR.iterdir()):
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        before = path.stat().st_size
        out_path, quality = process(path)
        after = out_path.stat().st_size
        total_before += before
        total_after += after
        rows.append((path.name, before, out_path.name, after, quality))

    name_w = max(len(r[0]) for r in rows)
    header = f"{'file':<{name_w}} {'before':>9} {'after':>9} {'q':>3} {'saved':>7}   {'webp'}"
    print(header)
    print("-" * len(header))
    for name, before, outname, after, q in rows:
        saved = 100 * (1 - after / before) if before else 0
        print(f"{name:<{name_w}} {before/1024:>8.0f}K {after/1024:>8.0f}K {q:>3} {saved:>6.1f}%   {outname}")

    print("-" * len(header))
    saved_total = 100 * (1 - total_after / total_before) if total_before else 0
    print(
        f"{'TOTAL (' + str(len(rows)) + ' files)':<{name_w}} "
        f"{total_before/1024/1024:>7.1f}M {total_after/1024/1024:>8.1f}M {'':>3} {saved_total:>6.1f}%"
    )


if __name__ == "__main__":
    main()
