#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
stamp_like_example.py (enhanced)
Infer a text placement region by comparing a BLANK image to an EXAMPLE-with-text,
then stamp any text in that same region. Adds precise controls for nudging and
constraining the fitted size.

New flags:
  --infer-pad N        : expand (>0) or shrink (<0) the inferred box
  --box-inset N        : inset the usable area inside the box before fitting
  --box-shift-x N      : shift the box horizontally (px)
  --box-shift-y N      : shift the box vertically (px)
  --fit-min N          : minimum font size when auto-fitting
  --fit-max N          : maximum font size when auto-fitting

Defaults tuned:
  v-align -> middle   (was bottom)
"""

import argparse
from pathlib import Path
from typing import Tuple, Optional, List

from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

# ----------------- helpers -----------------

def parse_color(s: Optional[str]):
    if not s:
        return None
    s = s.strip().lstrip("#")
    if len(s) in (3,6) and all(c in "0123456789abcdefABCDEF" for c in s):
        if len(s)==3:
            s = "".join(ch*2 for ch in s)
        return tuple(int(s[i:i+2],16) for i in (0,2,4))
    return s  # allow PIL color names

def load_font(font_path: Optional[str], size: int):
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def infer_box(blank_path: Path, example_path: Path, pad: int=0) -> Tuple[int,int,int,int]:
    with Image.open(blank_path) as b, Image.open(example_path) as e:
        if b.size != e.size:
            raise ValueError(f"Image sizes differ: {b.size} vs {e.size}")
        b_rgba = b.convert("RGBA")
        e_rgba = e.convert("RGBA")
        diff = ImageChops.difference(b_rgba, e_rgba)
        diffL = diff.convert("L")
        bbox = diffL.getbbox()
        if not bbox:
            raise ValueError("No visual difference found; cannot infer a region.")
        x0,y0,x1,y1 = bbox
        # apply pad (can be negative to shrink)
        x0 = clamp(x0 - pad, 0, b.width)
        y0 = clamp(y0 - pad, 0, b.height)
        x1 = clamp(x1 + pad, 0, b.width)
        y1 = clamp(y1 + pad, 0, b.height)
        return (x0,y0,x1,y1)

def save_box(box: Tuple[int,int,int,int], path: Path):
    x0,y0,x1,y1 = box
    path.write_text(f"{x0} {y0} {x1} {y1}", encoding="utf-8")

def load_box(path: Path) -> Tuple[int,int,int,int]:
    parts = path.read_text(encoding="utf-8").strip().replace(",", " ").split()
    if len(parts) != 4:
        raise ValueError("box file must contain exactly four integers: x0 y0 x1 y1")
    return tuple(int(v) for v in parts)  # type: ignore

def measure(draw: ImageDraw.ImageDraw, text: str, font, stroke_w: int, anchor: str):
    bbox = draw.textbbox((0,0), text, font=font, anchor=anchor, stroke_width=stroke_w)
    return bbox[2]-bbox[0], bbox[3]-bbox[1]

def find_max_font_size(
    text: str, font_path: Optional[str], box_w: int, box_h: int,
    start: int, stroke_w: int, anchor: str, fit_min: int, fit_max: int
) -> int:
    lo = max(1, fit_min)
    hi = max(lo, fit_max if fit_max > 0 else max(8, start*3))
    best = lo
    tmp = Image.new("RGBA", (max(1, box_w), max(1, box_h)), (0,0,0,0))
    draw = ImageDraw.Draw(tmp)
    while lo <= hi:
        mid = (lo+hi)//2
        font = load_font(font_path, mid)
        w, h = measure(draw, text, font, stroke_w, anchor)
        if w <= box_w and h <= box_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best

def place_point_in_box(box: Tuple[int,int,int,int], h_align: str, v_align: str, inset: int=0) -> Tuple[int,int]:
    x0,y0,x1,y1 = box
    # inset shrinks the box from each side before choosing anchor point
    x0i = x0 + inset; x1i = x1 - inset
    y0i = y0 + inset; y1i = y1 - inset
    if x0i > x1i: x0i, x1i = (x0+x1)//2, (x0+x1)//2
    if y0i > y1i: y0i, y1i = (y0+y1)//2, (y0+y1)//2

    if h_align == "left":   x = x0i
    elif h_align == "right":x = x1i
    else:                   x = (x0i + x1i)//2

    if v_align == "top":    y = y0i
    elif v_align == "bottom": y = y1i
    else:                   y = (y0i + y1i)//2
    return x,y

def anchor_from_align(h_align: str, v_align: str) -> str:
    return {"left":"l","center":"m","right":"r"}[h_align] + {"top":"t","middle":"m","bottom":"b"}[v_align]

def shift_box(box: Tuple[int,int,int,int], dx: int, dy: int, w: int, h: int) -> Tuple[int,int,int,int]:
    x0,y0,x1,y1 = box
    x0 = clamp(x0+dx, 0, w); x1 = clamp(x1+dx, 0, w)
    y0 = clamp(y0+dy, 0, h); y1 = clamp(y1+dy, 0, h)
    return (x0,y0,x1,y1)

def inset_box(box: Tuple[int,int,int,int], inset: int, w: int, h: int) -> Tuple[int,int,int,int]:
    x0,y0,x1,y1 = box
    x0 = clamp(x0+inset, 0, w); y0 = clamp(y0+inset, 0, h)
    x1 = clamp(x1-inset, 0, w); y1 = clamp(y1-inset, 0, h)
    if x1 < x0: x0, x1 = (x0+x1)//2, (x0+x1)//2
    if y1 < y0: y0, y1 = (y0+y1)//2, (y0+y1)//2
    return (x0,y0,x1,y1)

def unique_path(dst: Path) -> Path:
    if not dst.exists(): return dst
    stem, ext = dst.stem, dst.suffix
    i = 1
    while True:
        p = dst.with_name(f"{stem}_{i}{ext}")
        if not p.exists(): return p
        i += 1

# ----------------- main -----------------

def main():
    ap = argparse.ArgumentParser(description="Stamp text exactly where an example places it (auto-inferred box).")
    # inference / box selection
    ap.add_argument("--infer", nargs=2, metavar=("BLANK","EXAMPLE"),
                    help="Infer box from blank + example-with-text (same size).")
    ap.add_argument("--infer-pad", type=int, default=0,
                    help="Pad (px) to expand (>0) or shrink (<0) inferred box. Default 0.")
    ap.add_argument("--save-box", help="Save inferred box coords to this file.")
    ap.add_argument("--box-file", help="Use a previously saved box (x0 y0 x1 y1).")
    ap.add_argument("--box", nargs=4, type=int, metavar=("X0","Y0","X1","Y1"),
                    help="Manual box instead of inference.")
    ap.add_argument("--box-shift-x", type=int, default=0, help="Shift box horizontally (px).")
    ap.add_argument("--box-shift-y", type=int, default=0, help="Shift box vertically (px).")
    ap.add_argument("--box-inset", type=int, default=0, help="Shrink the usable area inside the box before fitting.")
    # stamping
    ap.add_argument("--text", required=False, default=None,
                    help="Text to stamp (e.g., XF+NN+MM+MX+DS).")
    ap.add_argument("--images", nargs="+",
                    help="Image(s) to stamp (e.g., list.bmp copy.bmp delete.bmp).")
    # style & placement inside the box:
    ap.add_argument("--font", help="Path to .ttf/.otf (optional).")
    ap.add_argument("--font-size", type=int, default=96,
                    help="Starting font size (also used with fit-on as seed).")
    ap.add_argument("--fit", choices=["on","off"], default="on",
                    help="Auto-size to fit the box (default on).")
    ap.add_argument("--fit-min", type=int, default=12,
                    help="Minimum font size when auto-fitting. Default 12.")
    ap.add_argument("--fit-max", type=int, default=0,
                    help="Maximum font size when auto-fitting; 0 = auto cap (~3x start).")
    ap.add_argument("--h-align", choices=["left","center","right"], default="center",
                    help="Horizontal alignment inside the box (default center).")
    ap.add_argument("--v-align", choices=["top","middle","bottom"], default="middle",
                    help="Vertical alignment inside the box (default middle).")
    ap.add_argument("--inset", type=int, default=0,
                    help="Extra padding (px) applied when choosing the anchor point.")
    ap.add_argument("--fill", default="FFFFFF",
                    help="Text color (hex or name). Default white.")
    ap.add_argument("--stroke", default="000000",
                    help="Outline color (hex or name). Default black.")
    ap.add_argument("--stroke-width", type=int, default=2,
                    help="Outline width px. Default 2.")
    # output
    ap.add_argument("--output-dir", default="out_stamped", help="Folder to write stamped images.")
    ap.add_argument("--suffix", default=None,
                    help="If set, append this before extension (e.g., _XF). Default: _<text> if single text used; otherwise none.")
    args = ap.parse_args()

    # 1) Resolve box
    box: Optional[Tuple[int,int,int,int]] = None
    base_w = base_h = None
    if args.infer:
        blank, example = map(Path, args.infer)
        box = infer_box(blank, example, pad=args.infer_pad)
        if args.save_box:
            save_box(box, Path(args.save_box))
        with Image.open(blank) as im0:
            base_w, base_h = im0.width, im0.height
    if args.box_file:
        box = load_box(Path(args.box_file))
    if args.box:
        box = tuple(args.box)  # type: ignore
    if not box:
        raise SystemExit("No box region. Provide --infer BLANK EXAMPLE, or --box-file, or --box x0 y0 x1 y1.")

    # 2) What to stamp & on which images
    if not args.text or not args.images:
        # Allow inference-only runs
        if args.infer and args.save_box:
            print(f"[INFO] Inferred box saved. ({box})")
            return
        raise SystemExit("You must provide --text and --images for stamping.")

    img_paths = [Path(p) for p in args.images]
    out_root = Path(args.output_dir); out_root.mkdir(parents=True, exist_ok=True)
    fill = parse_color(args.fill); stroke = parse_color(args.stroke)

    for img_path in img_paths:
        if not img_path.exists():
            print(f"[WARN] missing image: {img_path}")
            continue
        with Image.open(img_path) as im:
            work = im.convert("RGBA")
            W,H = work.width, work.height
            # If we inferred sizes from a different image, still apply shifts/limits relative to current W,H
            x0,y0,x1,y1 = box
            # Apply box shift
            x0,y0,x1,y1 = shift_box((x0,y0,x1,y1), args.box_shift_x, args.box_shift_y, W, H)
            # Apply box inset (shrink usable area before fitting)
            if args.box_inset:
                x0,y0,x1,y1 = inset_box((x0,y0,x1,y1), args.box_inset, W, H)

            box_w, box_h = max(1, x1-x0), max(1, y1-y0)
            draw = ImageDraw.Draw(work)

            # anchor point inside (possibly inset) box
            anchor = anchor_from_align(args.h_align, args.v_align)
            cx, cy = place_point_in_box((x0,y0,x1,y1), args.h_align, args.v_align, inset=args.inset)

            # choose font size
            if args.fit == "on":
                size = find_max_font_size(args.text, args.font, box_w, box_h,
                                          args.font_size, args.stroke_width, anchor,
                                          fit_min=args.fit_min, fit_max=args.fit_max)
            else:
                size = args.font_size
            font = load_font(args.font, size)

            # draw
            draw.text((cx, cy), args.text, font=font, fill=fill, anchor=anchor,
                      stroke_width=args.stroke_width, stroke_fill=stroke)

            # save
            dst = out_root / f"{img_path.stem}{f'_{args.text}' if not args.suffix else args.suffix}{img_path.suffix}"
            dst = unique_path(dst)
            out_img = work.convert(im.mode) if im.mode in ("RGB","P","L") else work
            out_img.save(dst)
            print(f"[WRITE] {img_path} -> {dst}  (box=({x0},{y0},{x1},{y1}), anchor={anchor}, size={size})")

if __name__ == "__main__":
    main()
