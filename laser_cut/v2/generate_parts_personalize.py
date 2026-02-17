#!/usr/bin/env python3
import numpy as np
import os
import base64

# ===================== PARAMETERS =====================

W = 100.0
D = 80.0
H = 100.0
TEXT_TOP = "LORENZO\nDIANE"
TEXT_FRONT = "SPRING\n2026"
CU_LOGO = True
DIVIDER = 0.4


HOLE_D = 2.2
HOLE_R = HOLE_D / 2
HOLE_OFFSET = 1.5
MIN_SPACING = 20.0
TOP_OFFSET = 4.7
MATERIAL_THICKNESS = 3

STROKE = "rgb(255,0,0)"
STROKE_W = "0.2"
OUT_DIR = "parts"

STOCK_W = 600
STOCK_H = 300
STOCK_SPACING = 10

# ===================== SVG =====================

class SVG:
    def __init__(self, name, w, h):
        os.makedirs(OUT_DIR, exist_ok=True)
        self.f = open(f"{OUT_DIR}/{name}", "w")

        self.mode = "CUT"  # default

        self.f.write(
            f"""<?xml version="1.0" encoding="UTF-8"?>
        <svg width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"
        xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink">
        """
        )


        self._open_group()

    def _open_group(self):
        if self.mode == "CUT":
            self.f.write(
                f'<g id="CUT" stroke="{STROKE}" stroke-width="{STROKE_W}" fill="none">\n'
            )
        else:
            self.f.write(
                f'<g id="ENGRAVE" stroke="none" fill="rgb(0,0,255)">\n'
            )

    def _close_group(self):
        self.f.write("</g>\n")

    def switch_to_engrave(self):
        if self.mode != "ENGRAVE":
            self._close_group()
            self.mode = "ENGRAVE"
            self._open_group()

    def switch_to_cut(self):
        if self.mode != "CUT":
            self._close_group()
            self.mode = "CUT"
            self._open_group()


    def line(self, x1, y1, x2, y2):
        self.f.write(
            f'<line x1="{x1:.3f}" y1="{y1:.3f}" '
            f'x2="{x2:.3f}" y2="{y2:.3f}" />\n'
        )

    def rect(self, x, y, w, h):
        self.line(x, y, x+w, y)
        self.line(x+w, y, x+w, y+h)
        self.line(x+w, y+h, x, y+h)
        self.line(x, y+h, x, y)

    def circle(self, x, y, r):
        self.f.write(
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r:.3f}" />\n'
        )

    def text_multiline(self, cx, cy, text, font_size):
        lines = text.split("\n")
        dy = font_size * 1.2
        start_y = cy - dy * (len(lines)-1) / 2

        self.f.write(
            f'<text x="{cx:.3f}" y="{start_y:.3f}" '
            f'font-family="sans-serif" font-size="{font_size:.3f}" '
            f'text-anchor="middle">\n'
        )
        for i, line in enumerate(lines):
            self.f.write(
                f'<tspan x="{cx:.3f}" y="{start_y + i*dy:.3f}">{line}</tspan>\n'
            )
        self.f.write('</text>\n')

    def cross(self, x, y, rotate=None):
        pts = np.array([
            (0, 0), (-3, 0), (-3, -1.25), (-4.7, -1.25), (-4.7, 0), (-10, 0),
            (-10, 2.2), (-4.7, 2.2), (-4.7, 3.45), (-3, 3.45), (-3, 2.2), (0, 2.2)
        ], dtype=float)

        # Rotation
        if rotate is not None:
            theta = np.deg2rad(rotate)
            R = np.array([
                [np.cos(theta), -np.sin(theta)],
                [np.sin(theta),  np.cos(theta)]
            ])
            pts = pts @ R.T

        # Translation
        pts[:, 0] += x
        pts[:, 1] += y

        # Draw
        for i in range(1, len(pts)):
            self.line(
                pts[i-1, 0], pts[i-1, 1],
                pts[i, 0],   pts[i, 1]
            )

    def close(self):
        self.f.write("</g></svg>")
        self.f.close()

# ===================== UTILS =====================

def validate_inputs():
    # ---- Dimension checks ----
    if W <= 0 or D <= 0 or H <= 0:
        raise ValueError("W, D, H must be positive numbers.")

    if MATERIAL_THICKNESS <= 0:
        raise ValueError("MATERIAL_THICKNESS must be positive.")

    if MATERIAL_THICKNESS >= min(W, D):
        raise ValueError("MATERIAL_THICKNESS too large compared to panel dimensions.")

    # ---- Hole checks ----
    if HOLE_D <= 0:
        raise ValueError("HOLE_D must be positive.")

    if HOLE_OFFSET < 0:
        raise ValueError("HOLE_OFFSET cannot be negative.")

    if HOLE_OFFSET + HOLE_R > MATERIAL_THICKNESS * 2:
        raise ValueError("Hole offset too large relative to material thickness.")

    # ---- Divider checks ----
    if DIVIDER is not None:
        if not (0.0 <= DIVIDER <= 1.0):
            raise ValueError("DIVIDER must be between 0 and 1.")

    # ---- Text checks ----
    for txt in [TEXT_TOP, TEXT_FRONT]:
        if txt is not None and not isinstance(txt, str):
            raise ValueError("Text parameters must be strings or None.")

    # ---- Spacing sanity ----
    if MIN_SPACING <= 0:
        raise ValueError("MIN_SPACING must be positive.")


def equispaced_positions(length):
    n = int(np.floor(length / MIN_SPACING)) - 1
    if n <= 0:
        return []
    step = length / (n + 1)
    return [(i + 1) * step for i in range(n)]

def engrave_text(svg, x, y, w, h, text):
    lines = text.split("\n")
    n = len(lines)

    max_w = 0.8 * w
    max_h = 0.8 * h

    font_size = min(
        max_h / n,
        max_w / max(len(line) for line in lines) * 1.2
    )

    total_h = n * font_size * 1.2
    y0 = y + h/2 - total_h/2 + font_size

    svg.switch_to_engrave()

    for i, line in enumerate(lines):
        svg.f.write(
            f'<text x="{x + w/2:.3f}" '
            f'y="{y0 + i*font_size*1.2:.3f}" '
            f'font-family="sans-serif" '
            f'font-size="{font_size:.3f}" '
            f'text-anchor="middle" '
            f'dominant-baseline="middle">'
            f'{line}</text>\n'
        )

    svg.switch_to_cut()


def sierpinski(cx, cy, size, depth=4):
    tris = []
    h = size * np.sqrt(3) / 2
    p1 = (cx, cy - 2*h/3)
    p2 = (cx - size/2, cy + h/3)
    p3 = (cx + size/2, cy + h/3)

    def rec(a, b, c, d):
        if d == 0:
            tris.append([a, b, c, a])
        else:
            ab = ((a[0]+b[0])/2, (a[1]+b[1])/2)
            bc = ((b[0]+c[0])/2, (b[1]+c[1])/2)
            ca = ((c[0]+a[0])/2, (c[1]+a[1])/2)
            rec(a, ab, ca, d-1)
            rec(ab, b, bc, d-1)
            rec(ca, bc, c, d-1)

    rec(p1, p2, p3, depth)
    return tris

def engrave_sierpinski(svg, cx, cy, size, depth=4):
    tris = sierpinski(cx, cy, size, depth)

    svg.switch_to_engrave()
    for tri in tris:
        pts = " ".join(f"{x:.3f},{y+3:.3f}" for x, y in tri)
        svg.f.write(
            f'<polyline points="{pts}" fill="none" stroke="blue" />\n'
        )
    svg.switch_to_cut()

def png_to_base64(path):
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

def combine_svgs_on_stock(
    stock_w=600,
    stock_h=300,
    spacing=15,
    output_name="all_parts.svg"
):
    import re

    files = sorted([
        f for f in os.listdir(OUT_DIR)
        if f.endswith(".svg") and f != output_name
    ])

    if not files:
        raise RuntimeError("No SVG files found.")

    parts = []

    for fname in files:
        path = os.path.join(OUT_DIR, fname)

        with open(path, "r") as f:
            data = f.read()

        w = float(re.search(r'width="([\d\.]+)', data).group(1))
        h = float(re.search(r'height="([\d\.]+)', data).group(1))

        start = data.find("<g")
        end = data.rfind("</svg>")
        inner = data[start:end]

        parts.append((fname, w, h, inner))

    # ---- simple row packing ----
    x = spacing
    y = spacing
    row_height = 0

    placements = []

    for name, w, h, inner in parts:

        if x + w > stock_w - spacing:
            # new row
            x = spacing
            y += row_height + spacing
            row_height = 0

        if y + h > stock_h - spacing:
            raise RuntimeError(
                f"Part {name} does not fit in stock {stock_w}x{stock_h}."
            )

        placements.append((x, y, inner))
        row_height = max(row_height, h)
        x += w + spacing

    # ---- write output ----
    out_path = os.path.join(OUT_DIR, output_name)

    with open(out_path, "w") as f:
        f.write(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{stock_w}mm" height="{stock_h}mm"
viewBox="0 0 {stock_w} {stock_h}"
xmlns="http://www.w3.org/2000/svg"
xmlns:xlink="http://www.w3.org/1999/xlink">
"""
        )

        # stock boundary (optional)
        f.write(
            f'<rect x="0" y="0" width="{stock_w}" height="{stock_h}" '
            f'stroke="black" fill="none" stroke-dasharray="5,5"/>\n'
        )

        for x, y, inner in placements:
            f.write(f'<g transform="translate({x},{y})">\n')
            f.write(inner)
            f.write("</g>\n")

        f.write("</svg>")

# ===================== PARTS =====================

def write_side(l, name, fractal=None, text=None, divider=None, logo=False, flip=False):

    hs = equispaced_positions(H)

    w1 = l - MATERIAL_THICKNESS

    svg = SVG("side_" + name + ".svg", w1, H + MATERIAL_THICKNESS)
    if divider is None:
        svg.line(0, 0, l, 0)
    else:
        # divider is a percentage along x
        p = divider

        if flip is True:
            p = 1.0 - p

        # usable length excludes material thickness on both sides
        usable = l - 2 * MATERIAL_THICKNESS
        x = MATERIAL_THICKNESS + p * usable

        # top edge with vertical slot
        svg.line(0, 0, x - MATERIAL_THICKNESS / 2, 0)
        svg.line(x - MATERIAL_THICKNESS / 2, 0,
                 x - MATERIAL_THICKNESS / 2, 10)
        svg.line(x - MATERIAL_THICKNESS / 2, 10,
                 x + MATERIAL_THICKNESS / 2, 10)
        svg.line(x + MATERIAL_THICKNESS / 2, 10,
                 x + MATERIAL_THICKNESS / 2, 0)
        svg.line(x + MATERIAL_THICKNESS / 2, 0, w1, 0)

    if logo is True:
        img_path = "columbia.png"

        # nominal layout
        img_w = 60.0
        img_h = 60.0
        text_h = 30.0
        gap = 6.0

        block_w = img_w
        block_h = img_h + gap + text_h

        # 80% rule
        max_dim = 0.8 * min(w1, H)
        scale = 1.0
        if max(block_w, block_h) > max_dim:
            scale = max_dim / max(block_w, block_h)

        img_w *= scale
        img_h *= scale
        text_h *= scale
        gap *= scale
        block_h = img_h + gap + text_h

        # centered placement
        x0 = (w1 - img_w) / 2
        y0 = (H - block_h) / 2

        # embed image
        img_data = png_to_base64(img_path)

        svg.switch_to_engrave()

        svg.f.write(
            f'<image x="{x0:.3f}" y="{y0:.3f}" '
            f'width="{img_w:.3f}" height="{img_h:.3f}" '
            f'xlink:href="{img_data}" />\n'
        )

        engrave_text(
            svg,
            x=x0,
            y=y0 + img_h + gap,
            w=img_w,
            h=text_h,
            text="DIGITAL\nMANUFACTURING"
        )

    if fractal or text:
        # layout
        frac_size = 80.0
        text_h = 25.0 if text else 0.0
        gap = 6.0 if text else 0.0

        block_h = frac_size + gap + text_h
        block_w = frac_size

        # 80% rule
        max_dim = 0.8 * min(w1, H)
        scale = 1.0
        if max(block_w, block_h) > max_dim:
            scale = max_dim / max(block_w, block_h)

        frac_size *= scale
        text_h *= scale
        gap *= scale
        block_h = frac_size + gap + text_h

        # placement (centered)
        cx = w1 / 2
        y0 = (H - block_h) / 2

        # text on top
        if text:
            engrave_text(
                svg,
                x=cx - frac_size / 2,
                y=y0,
                w=frac_size,
                h=text_h,
                text=text
            )

        # fractal below text
        frac_cy = y0 + text_h + gap + frac_size / 2
        engrave_sierpinski(
            svg,
            cx=cx,
            cy=frac_cy,
            size=frac_size,
            depth=4
        )


    h0 = 0
    for h in hs:
        svg.circle(HOLE_OFFSET, h, HOLE_R)
        svg.line(w1, h0, w1, h - HOLE_R)
        svg.cross(w1, h - HOLE_R, rotate=None)
        h0 = h + HOLE_R
    svg.line(w1, h0, w1, H + MATERIAL_THICKNESS)
    
    xs = equispaced_positions(l)
    x0 = 0
    for x in xs:
        svg.line(x0, H + MATERIAL_THICKNESS, x-HOLE_R, H + MATERIAL_THICKNESS)
        svg.cross(x + HOLE_R, H + MATERIAL_THICKNESS, rotate=90)
        x0 = x + HOLE_R
    svg.line(x0, H + MATERIAL_THICKNESS, l - MATERIAL_THICKNESS, H + MATERIAL_THICKNESS)
    svg.line(0, H + MATERIAL_THICKNESS, 0, 0)
    svg.close()


def write_divider():
    svg = SVG("divider.svg", D, H + MATERIAL_THICKNESS)

    t = MATERIAL_THICKNESS

    # --- Tabs geometry ---
    tab_c_w = 10.0        # central tab width
    tab_s_w = 5.0         # side tab width

    cx = D / 2
    xC_L = cx - tab_c_w / 2
    xC_R = cx + tab_c_w / 2

    xL_L = t
    xL_R = t + tab_s_w

    xR_R = D - t
    xR_L = D - t - tab_s_w

    # --- Outline (clockwise) ---

    # Top
    svg.line(0, 0, D, 0)

    # Right side
    svg.line(D, 0, D, 10)
    svg.line(D, 10, D - t, 10)
    svg.line(D - t, 10, D - t, H)

    # Right tab
    svg.line(D - t, H, xR_R, H)
    svg.line(xR_R, H, xR_R, H + t)
    svg.line(xR_R, H + t, xR_L, H + t)
    svg.line(xR_L, H + t, xR_L, H)

    # Central tab
    svg.line(xR_L, H, xC_R, H)
    svg.line(xC_R, H, xC_R, H + t)
    svg.line(xC_R, H + t, xC_L, H + t)
    svg.line(xC_L, H + t, xC_L, H)

    # Left tab
    svg.line(xC_L, H, xL_R, H)
    svg.line(xL_R, H, xL_R, H + t)
    svg.line(xL_R, H + t, xL_L, H + t)
    svg.line(xL_L, H + t, xL_L, H)

    # Left side up
    svg.line(xL_L, H, t, H)
    svg.line(t, H, t, 10)
    svg.line(t, 10, 0, 10)
    svg.line(0, 10, 0, 0)

    svg.close()


def write_top(text=None):
    w = W + 2*TOP_OFFSET
    d = D + 2*TOP_OFFSET
    svg = SVG("top.svg", w, d)
    svg.rect(0, 0, w, d)

    if text:
        engrave_text(svg, 0, 0, w, d, text)

    off = 2.35
    svg.circle(off, off, HOLE_R)
    svg.circle(w - off, off, HOLE_R)
    svg.circle(w - off, d - off, HOLE_R)
    svg.circle(off, d - off, HOLE_R)

    svg.close()


def write_bottom_with_liner():
    w_out = W + 2 * TOP_OFFSET
    d_out = D + 2 * TOP_OFFSET


    off_bottom = TOP_OFFSET

    svg = SVG("bottom_liner.svg", w_out, d_out)

    # --- Liner outer contour ---
    svg.rect(0, 0, w_out, d_out)

    # --- Bottom panel ---
    svg.rect(off_bottom, off_bottom, W, D)

    # Standard bottom perimeter holes
    xs = equispaced_positions(W)
    ys = equispaced_positions(D)

    for x in xs:
        svg.circle(off_bottom + x, off_bottom + HOLE_OFFSET, HOLE_R)
        svg.circle(off_bottom + x, off_bottom + D - HOLE_OFFSET, HOLE_R)

    for y in ys:
        svg.circle(off_bottom + HOLE_OFFSET, off_bottom + y, HOLE_R)
        svg.circle(off_bottom + W - HOLE_OFFSET, off_bottom + y, HOLE_R)

    # --- Corner holes aligned with spacer ---
    offset_total = MATERIAL_THICKNESS + 2.35

    svg.circle(off_bottom + offset_total,           off_bottom + offset_total,           HOLE_R)
    svg.circle(off_bottom + W - offset_total,       off_bottom + offset_total,           HOLE_R)
    svg.circle(off_bottom + W - offset_total,       off_bottom + D - offset_total,       HOLE_R)
    svg.circle(off_bottom + offset_total,           off_bottom + D - offset_total,       HOLE_R)

    off = 2.35
    svg.circle(off, off, HOLE_R)
    svg.circle(w_out - off, off, HOLE_R)
    svg.circle(w_out - off, d_out - off, HOLE_R)
    svg.circle(off, d_out - off, HOLE_R)
    svg.close()

def write_spacer(DIVIDER):
    """Generate a spacer panel for the bottom."""

    w = W - 2 * MATERIAL_THICKNESS
    d = D - 2 * MATERIAL_THICKNESS

    svg = SVG("bottom_spacer.svg", w, d)

    # Divider slot parameters
    slot_thickness = MATERIAL_THICKNESS
    slot_length = 10.0
    
    if DIVIDER is not None:
        cx = w * DIVIDER
        cy = d / 2

        x = cx - slot_thickness / 2
        y = cy - slot_length / 2

        svg.rect(x, y, slot_thickness, slot_length)

        for i in [0, d]:
            if i==d:
                k=-1
            else:
                k=1
            svg.line(0,i,w*DIVIDER-MATERIAL_THICKNESS/2,i)
            svg.line(0,i,w*DIVIDER-MATERIAL_THICKNESS/2,i)
            svg.line(w*DIVIDER-MATERIAL_THICKNESS/2,i,w*DIVIDER-MATERIAL_THICKNESS/2,i+k*(5))
            svg.line(w*DIVIDER-MATERIAL_THICKNESS/2,i+k*(5),w*DIVIDER+MATERIAL_THICKNESS/2,i+k*(5))
            svg.line(w*DIVIDER+MATERIAL_THICKNESS/2,i+k*(5),w*DIVIDER+MATERIAL_THICKNESS/2,i)
            svg.line(w*DIVIDER+MATERIAL_THICKNESS/2,i,w,i)
    else:
        svg.line(0,0,w,0)
        svg.line(0,d,w,d)
    
    svg.line(0,0,0,d)
    svg.line(w,0,w,d)

    # Corner holes
    off = 2.35
    svg.circle(off, off, HOLE_R)
    svg.circle(w - off, off, HOLE_R)
    svg.circle(w - off, d - off, HOLE_R)
    svg.circle(off, d - off, HOLE_R)

    svg.close()

# ===================== MAIN =====================

if __name__ == "__main__":
    validate_inputs()

    W += 2* MATERIAL_THICKNESS
    D += 2* MATERIAL_THICKNESS

    if D >= W:
        W, D = D, W

    write_side(W, "A", divider=DIVIDER)
    write_side(D, "B", True, TEXT_FRONT)
    write_side(W, "C", divider=DIVIDER, flip=True)
    write_side(D, "D", logo=True)
    write_spacer(DIVIDER)
    if DIVIDER is not None:
        write_divider()
    write_top(TEXT_TOP)
    write_bottom_with_liner()
    combine_svgs_on_stock(STOCK_W, STOCK_H, STOCK_SPACING)
