#!/usr/bin/env python3
"""
generate_embroidery.py
======================
Generates a Janome JEF embroidery file directly (no embroidery libraries).
Produces a pizza-slice design with 'Diane | Lorenzo' text, fitting in 10×10 cm.

Usage:
    python generate_embroidery.py [options]

Units: 1 JEF unit = 0.1 mm  →  10×10 cm = 1000×1000 JEF units (±500 from center)

Author: Generated for MECEE4606 Digital Manufacturing
"""

import argparse
import math
import struct
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# Stroke font  (simplified Hershey-style glyph data)
# Each glyph: list of strokes; each stroke: list of (x, y) in font units
# Font cap-height ≈ 10 units; scaled to desired mm size at render time.
# ---------------------------------------------------------------------------
GLYPH_WIDTH = 7   # nominal advance width per character (font units)

FONT = {
    # Capital letters
    'A': [[(0,0),(3,10),(6,0)], [(1,4),(5,4)]],
    'B': [[(0,0),(0,10),(4,10),(5,9),(5,6),(4,5),(0,5)], [(4,5),(5,4),(5,1),(4,0),(0,0)]],
    'C': [[(6,8),(5,10),(2,10),(0,8),(0,2),(2,0),(5,0),(6,2)]],
    'D': [[(0,0),(0,10),(3,10),(5,8),(5,2),(3,0),(0,0)]],
    'E': [[(6,10),(0,10),(0,0),(6,0)], [(0,5),(4,5)]],
    'F': [[(0,0),(0,10),(6,10)], [(0,5),(4,5)]],
    'G': [[(6,8),(5,10),(2,10),(0,8),(0,2),(2,0),(5,0),(6,2),(6,5),(3,5)]],
    'H': [[(0,0),(0,10)], [(6,0),(6,10)], [(0,5),(6,5)]],
    'I': [[(3,0),(3,10)], [(1,0),(5,0)], [(1,10),(5,10)]],
    'J': [[(5,10),(5,1),(4,0),(2,0),(1,1),(1,3)]],
    'K': [[(0,0),(0,10)], [(0,5),(6,10)], [(0,5),(6,0)]],
    'L': [[(0,10),(0,0),(6,0)]],
    'M': [[(0,0),(0,10),(3,5),(6,10),(6,0)]],
    'N': [[(0,0),(0,10),(6,0),(6,10)]],
    'O': [[(2,0),(0,2),(0,8),(2,10),(4,10),(6,8),(6,2),(4,0),(2,0)]],
    'P': [[(0,0),(0,10),(4,10),(6,8),(6,6),(4,5),(0,5)]],
    'Q': [[(2,0),(0,2),(0,8),(2,10),(4,10),(6,8),(6,2),(4,0),(2,0)], [(4,2),(6,0)]],
    'R': [[(0,0),(0,10),(4,10),(6,8),(6,6),(4,5),(0,5)], [(3,5),(6,0)]],
    'S': [[(6,8),(5,10),(2,10),(0,8),(1,5),(5,5),(6,2),(5,0),(2,0),(0,2)]],
    'T': [[(3,0),(3,10)], [(0,10),(6,10)]],
    'U': [[(0,10),(0,2),(2,0),(4,0),(6,2),(6,10)]],
    'V': [[(0,10),(3,0),(6,10)]],
    'W': [[(0,10),(1,0),(3,5),(5,0),(6,10)]],
    'X': [[(0,0),(6,10)], [(6,0),(0,10)]],
    'Y': [[(0,10),(3,5),(6,10)], [(3,5),(3,0)]],
    'Z': [[(0,10),(6,10),(0,0),(6,0)]],
    # Lowercase (simplified – same as caps but 7-unit tall)
    'a': [[(5,7),(4,8),(2,8),(0,6),(0,5),(2,4),(5,4),(5,0)], [(5,0),(1,0)]],
    'b': [[(0,10),(0,0)], [(0,5),(3,5),(5,4),(5,1),(3,0),(0,0)]],
    'c': [[(5,6),(4,8),(2,8),(0,6),(0,2),(2,0),(4,0),(5,2)]],
    'd': [[(5,10),(5,0),(2,0),(0,2),(0,6),(2,8),(5,8)]],
    'e': [[(0,4),(5,4),(5,6),(4,8),(2,8),(0,6),(0,2),(2,0),(4,0),(5,1)]],
    'f': [[(1,0),(1,9),(2,10),(4,10)], [(0,6),(3,6)]],
    'g': [[(5,8),(4,8),(2,8),(0,6),(0,2),(2,0),(5,0),(5,8),(5,11),(4,12),(2,12),(1,11)]],
    'h': [[(0,0),(0,10)], [(0,5),(2,8),(4,8),(5,6),(5,0)]],
    'i': [[(3,0),(3,8)], [(3,10),(3,11)]],
    'j': [[(4,8),(4,-1),(3,-2),(1,-2)], [(4,10),(4,11)]],
    'k': [[(0,0),(0,10)], [(0,4),(4,8)], [(1,5),(5,0)]],
    'l': [[(3,10),(3,1),(4,0)]],
    'm': [[(0,0),(0,8)], [(0,7),(2,8),(4,7),(4,0)], [(4,7),(5,8),(7,8),(8,6),(8,0)]],
    'n': [[(0,0),(0,8)], [(0,5),(2,8),(4,8),(5,6),(5,0)]],
    'o': [[(2,0),(0,2),(0,6),(2,8),(4,8),(5,6),(5,2),(4,0),(2,0)]],
    'p': [[(0,-3),(0,8)], [(0,5),(3,8),(5,6),(5,3),(3,0),(0,0)]],
    'q': [[(5,-3),(5,8)], [(5,5),(2,8),(0,6),(0,3),(2,0),(5,0)]],
    'r': [[(0,0),(0,8),(2,8),(4,7)]],
    's': [[(5,6),(4,8),(2,8),(0,6),(1,4),(4,4),(5,2),(4,0),(2,0),(0,2)]],
    't': [[(2,10),(2,1),(3,0)], [(0,6),(5,6)]],
    'u': [[(0,8),(0,2),(2,0),(4,0),(5,2),(5,8)]],
    'v': [[(0,8),(2.5,0),(5,8)]],
    'w': [[(0,8),(1,0),(3,4),(5,0),(6,8)]],
    'x': [[(0,0),(5,8)], [(5,0),(0,8)]],
    'y': [[(0,8),(3,0)], [(5,8),(3,0),(2,-2),(1,-3)]],
    'z': [[(0,8),(5,8),(0,0),(5,0)]],
    # Digits
    '0': [[(2,0),(0,2),(0,8),(2,10),(4,10),(6,8),(6,2),(4,0),(2,0)], [(0,2),(6,8)]],
    '1': [[(1,8),(3,10),(3,0)], [(1,0),(5,0)]],
    '2': [[(0,8),(2,10),(4,10),(6,8),(6,5),(0,0),(6,0)]],
    '3': [[(0,8),(2,10),(4,10),(6,8),(6,6),(4,5),(6,4),(6,2),(4,0),(2,0),(0,2)]],
    '4': [[(0,10),(0,5),(6,5)], [(5,10),(5,0)]],
    '5': [[(6,10),(0,10),(0,6),(5,6),(6,4),(6,2),(4,0),(2,0),(0,2)]],
    '6': [[(5,10),(2,10),(0,8),(0,2),(2,0),(5,0),(6,2),(6,4),(5,6),(0,6)]],
    '7': [[(0,10),(6,10),(2,0)]],
    '8': [[(2,5),(0,3),(0,8),(2,10),(4,10),(6,8),(6,3),(4,5),(6,2),(4,0),(2,0),(0,2),(0,3)],
           [(2,5),(4,5)]],
    '9': [[(6,4),(5,0),(2,0),(0,2),(0,4),(2,6),(6,6),(6,8),(4,10),(2,10),(0,8)]],
    # Special
    ' ': [],
    '|': [[(3,0),(3,10)]],
    '-': [[(0,5),(6,5)]],
    '.': [[(3,0),(3,1)]],
    ',': [[(4,1),(3,0),(3,-1)]],
    '!': [[(3,2),(3,10)], [(3,0),(3,1)]],
    '\'': [[(3,10),(2,8)]],
}


# ---------------------------------------------------------------------------
# JEF stitch encoding helpers
# ---------------------------------------------------------------------------

def encode_stitches(stitch_list):
    """
    Convert list of (cmd, x, y) to JEF binary bytes.
    cmd: 'stitch', 'jump', 'color_change', 'end'
    x, y: displacements in JEF units (0.1 mm), signed integers
    Returns: bytearray
    """
    buf = bytearray()
    for item in stitch_list:
        cmd = item[0]
        if cmd in ('stitch', 'jump'):
            dx, dy = item[1], item[2]
            # Chop into ≤127-unit segments
            while abs(dx) > 127 or abs(dy) > 127:
                sx = max(-127, min(127, dx))
                sy = max(-127, min(127, dy))
                # Jump command: 0x80 0x01 dx dy
                buf += bytes([0x80, 0x01,
                               sx & 0xFF, sy & 0xFF])
                dx -= sx
                dy -= sy
            if cmd == 'jump':
                buf += bytes([0x80, 0x01,
                               dx & 0xFF, dy & 0xFF])
            else:
                buf += bytes([dx & 0xFF, dy & 0xFF])
        elif cmd == 'color_change':
            buf += bytes([0x80, 0x01, 0x00, 0x00])
            buf += bytes([0x80, 0x02, 0x00, 0x00])
        elif cmd == 'end':
            buf += bytes([0x80, 0x10])
    return buf


def abs_to_relative(abs_coords, cmd_type='stitch'):
    """
    Convert list of absolute (x, y) coordinates into relative stitch commands.
    First point is a jump from (0,0), subsequent points are stitches.
    Returns list of (cmd, dx, dy) tuples.
    """
    result = []
    prev_x, prev_y = 0, 0
    for i, (x, y) in enumerate(abs_coords):
        dx = round(x) - prev_x
        dy = round(y) - prev_y
        if i == 0:
            result.append(('jump', dx, dy))
        else:
            result.append((cmd_type, dx, dy))
        prev_x = round(x)
        prev_y = round(y)
    return result


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def running_stitch_line(x0, y0, x1, y1, stitch_mm=1.5):
    """Generate points along a line segment spaced stitch_mm apart (in mm → *10 for JEF)."""
    sl = stitch_mm * 10  # convert to JEF units
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1:
        return [(x0, y0), (x1, y1)]
    steps = max(1, int(length / sl))
    points = []
    for i in range(steps + 1):
        t = i / steps
        points.append((x0 + dx * t, y0 + dy * t))
    return points


def arc_points(cx, cy, radius, start_angle_deg, end_angle_deg, stitch_mm=1.5):
    """Return points along an arc, spaced ~stitch_mm apart."""
    sl = stitch_mm * 10
    arc_len = abs(end_angle_deg - start_angle_deg) * math.pi / 180 * radius
    n = max(2, int(arc_len / sl))
    pts = []
    for i in range(n + 1):
        t = i / n
        angle = math.radians(start_angle_deg + (end_angle_deg - start_angle_deg) * t)
        pts.append((cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle)))
    return pts


def circle_fill(cx, cy, radius, row_spacing_mm=0.4, stitch_mm=1.5):
    """Fill a circle with horizontal satin rows."""
    rs = row_spacing_mm * 10
    sl = stitch_mm * 10
    points = []
    r = int(radius)
    y = -r
    direction = 1
    while y <= r:
        half = math.sqrt(max(0, radius**2 - y**2))
        x0 = cx - half
        x1 = cx + half
        if direction == 1:
            pts = running_stitch_line(x0, cy + y, x1, cy + y, stitch_mm)
        else:
            pts = running_stitch_line(x1, cy + y, x0, cy + y, stitch_mm)
        points.extend(pts)
        y += rs
        direction *= -1
    return points


def wedge_fill(cx, cy, radius, start_angle_deg, end_angle_deg, row_spacing_mm=0.5, stitch_mm=1.5):
    """Fill a pizza wedge with satin rows (horizontal scan lines clipped to wedge)."""
    rs = row_spacing_mm * 10
    sl = stitch_mm * 10
    # Bounding box
    a1 = math.radians(start_angle_deg)
    a2 = math.radians(end_angle_deg)
    all_pts = []
    y = -radius
    direction = 1
    while y <= radius:
        # find x range at this y within the circle
        disc = radius**2 - y**2
        if disc < 0:
            y += rs
            continue
        half = math.sqrt(disc)
        # Clip to wedge angle
        row_pts = []
        for x in [cx - half + i * sl for i in range(int(2 * half / sl) + 2)]:
            px = x
            py = cy + y
            # Check if (px, py) is inside wedge
            angle = math.atan2(py - cy, px - cx)
            # Normalize angle to [a1, a2]
            norm_angle = angle
            # Is point within wedge sector?
            if _angle_in_sector(norm_angle, a1, a2) and math.hypot(px - cx, py - cy) <= radius:
                row_pts.append((px, py))
        if row_pts:
            if direction == -1:
                row_pts = list(reversed(row_pts))
            all_pts.extend(row_pts)
        y += rs
        direction *= -1
    return all_pts


def _angle_in_sector(angle, a1, a2):
    """Check if angle is between a1 and a2 (handles wrap-around)."""
    # Normalize angle to [0, 2pi)
    def norm(a):
        while a < 0:
            a += 2 * math.pi
        while a >= 2 * math.pi:
            a -= 2 * math.pi
        return a

    a = norm(angle)
    s = norm(a1)
    e = norm(a2)
    if s <= e:
        return s <= a <= e
    else:
        return a >= s or a <= e


# ---------------------------------------------------------------------------
# Stroke font rendering
# ---------------------------------------------------------------------------

def render_text(text, x_start, y_start, cap_height_mm=8.0, stitch_mm=1.5,
                glyph_w=GLYPH_WIDTH, glyph_h=10):
    """
    Render text as stroke-font stitches.
    Returns list of absolute (x, y) stitch runs (each run is a list of coords).
    """
    scale = (cap_height_mm * 10) / glyph_h  # font-unit → JEF units

    # Compute total text width to center
    total_w = 0
    for ch in text:
        total_w += (glyph_w + 1) * scale

    x = x_start - total_w / 2
    y = y_start

    all_runs = []
    for ch in text.upper() if text.upper() in FONT else text:
        # Try upper then lower
        glyphs = FONT.get(ch.upper(), FONT.get(ch, FONT.get(' ', [])))
        for stroke in glyphs:
            if not stroke:
                continue
            run = []
            for gx, gy in stroke:
                px = x + gx * scale
                py = y + gy * scale
                run.append((px, py))
            # Interpolate points along strokes
            dense_run = []
            for i in range(len(run) - 1):
                seg = running_stitch_line(run[i][0], run[i][1],
                                          run[i+1][0], run[i+1][1], stitch_mm)
                if dense_run and seg:
                    dense_run.extend(seg[1:])
                else:
                    dense_run.extend(seg)
            if dense_run:
                all_runs.append(dense_run)
        x += (glyph_w + 1) * scale

    return all_runs


def render_text_exact(text, x_start, y_start, cap_height_mm=8.0, stitch_mm=1.5):
    """Render text respecting mixed case with built-in font."""
    scale = (cap_height_mm * 10) / 10.0

    # Compute total text width to center
    total_w = len(text) * (GLYPH_WIDTH + 1) * scale
    x = x_start - total_w / 2
    y = y_start

    all_runs = []
    for ch in text:
        glyphs = FONT.get(ch, FONT.get(ch.upper(), FONT.get(' ', [])))
        for stroke in glyphs:
            if not stroke:
                continue
            run_pts = [(x + gx * scale, y + gy * scale) for gx, gy in stroke]
            dense_run = []
            for i in range(len(run_pts) - 1):
                seg = running_stitch_line(run_pts[i][0], run_pts[i][1],
                                          run_pts[i+1][0], run_pts[i+1][1], stitch_mm)
                if dense_run:
                    dense_run.extend(seg[1:])
                else:
                    dense_run.extend(seg)
            if dense_run:
                all_runs.append(dense_run)
        x += (GLYPH_WIDTH + 1) * scale
    return all_runs


# ---------------------------------------------------------------------------
# JEF file writer
# ---------------------------------------------------------------------------

def write_jef(filename, thread_colors, stitch_data_bytes, num_stitches,
              hoop_mm=100):
    """
    Write a JEF file.
    thread_colors: list of (R, G, B) tuples, one per color segment
    stitch_data_bytes: raw encoded stitch bytes (bytearray)
    num_stitches: total stitch count (int)
    hoop_mm: hoop size (100 = 10x10 cm)
    """
    num_colors = len(thread_colors)
    now = datetime.now()

    # Header is 256 bytes + thread table (32 bytes per color) + stitch data
    thread_table_size = num_colors * 32
    stitch_offset = 256 + thread_table_size

    header = bytearray(256)

    # Byte 0–3: stitch data offset
    struct.pack_into('<I', header, 0, stitch_offset)

    # Bytes 4–11: date ASCII "YYYYMMDD"
    date_str = now.strftime('%Y%m%d')
    header[4:12] = date_str.encode('ascii')

    # Bytes 12–19: time ASCII "HHMMSSxx"
    time_str = now.strftime('%H%M%S00')
    header[12:20] = time_str.encode('ascii')

    # Byte 20: version letter  ('A')
    header[20] = ord('A')

    # Bytes 24–27: number of color changes (= number of threads - 1)
    struct.pack_into('<I', header, 24, num_colors - 1)

    # Bytes 28–31: total stitch count (approximate - includes jumps)
    total_bytes = len(stitch_data_bytes)
    approx_stitches = total_bytes // 2
    struct.pack_into('<I', header, 28, approx_stitches)

    # Hoop extents (4 sets of 4 ints: x_neg, x_pos, y_neg, y_pos for each hoop size)
    # Hoop sizes: 110x110, 50x50, 140x200, custom
    half = hoop_mm * 5  # mm → JEF units (* 10 / 2)
    hoop_data = [
        -half, half, -half, half,  # 110x110 hoop
        -half, half, -half, half,  # 50x50 hoop
        -half, half, -half, half,  # 140x200 hoop
        -half, half, -half, half,  # additional
    ]
    offset = 32
    for val in hoop_data:
        struct.pack_into('<i', header, offset, int(val))
        offset += 4

    # Thread count at offset 128
    struct.pack_into('<I', header, 128, num_colors)

    # Build thread color table (32 bytes per thread)
    thread_table = bytearray(thread_table_size)
    # Standard Janome thread type codes for common colors
    janome_codes = [
        b'\x01\x00\x00\x00',  # generic
    ]
    for i, (r, g, b) in enumerate(thread_colors):
        base = i * 32
        thread_table[base + 0] = r
        thread_table[base + 1] = g
        thread_table[base + 2] = b
        thread_table[base + 3] = 0x00
        # Thread type (bytes 4–7)
        thread_table[base + 4] = 0x00
        thread_table[base + 5] = 0x00
        thread_table[base + 6] = 0x00
        thread_table[base + 7] = 0x00

    with open(filename, 'wb') as f:
        f.write(header)
        f.write(thread_table)
        f.write(stitch_data_bytes)

    return stitch_offset


# ---------------------------------------------------------------------------
# Main design generator
# ---------------------------------------------------------------------------

def generate_pizza_embroidery(
    radius_mm=40,
    slice_angle_deg=90,
    num_pepperoni=3,
    text="Diane | Lorenzo",
    stitch_len_mm=1.5,
    satin_spacing_mm=0.4,
    output="pizza.jef"
):
    """
    Generate a pizza-slice embroidery JEF file.

    Parameters
    ----------
    radius_mm       : outer radius of pizza slice (mm)
    slice_angle_deg : angle of the slice (degrees)
    num_pepperoni   : number of pepperoni circles
    text            : text to embroider below slice
    stitch_len_mm   : running stitch length (mm)
    satin_spacing_mm: fill row spacing (mm)
    output          : output .jef filename
    """
    # JEF units: 1 unit = 0.1 mm
    R = radius_mm * 10          # radius in JEF units
    hoop = 1000                 # 1000 JEF units = 100 mm = 10 cm

    # --- Dynamically center the design vertically ---
    # Design spans: crust_top (cy+R) down to text_bottom (text_y - text_height)
    # text_y = cy - text_gap;  text_height ≈ cap_height (70 JEF units for 7mm)
    text_gap   = 60    # gap between slice tip and top of text (JEF units)
    text_h     = 70    # approximate text cap height in JEF units
    border_pad = 20    # padding from hoop edge for border ring
    # Total vertical span: R (up from tip to crust) + text_gap + text_h
    # For centering: cy + R = -cy + text_gap + text_h  →  cy = (text_gap + text_h - R) / 2
    cy = int((text_gap + text_h - R) / 2)
    cx = 0

    # Slice runs from -slice_angle/2 to +slice_angle/2
    # Pointing upward (90°), so center at 90° from +X axis → point at top
    center_angle = 90.0
    a1 = center_angle - slice_angle_deg / 2   # start angle (degrees)
    a2 = center_angle + slice_angle_deg / 2   # end angle (degrees)

    # -----------------------------------------------------------------------
    # Thread colors:
    # 0: Cheese Yellow      – fills the wedge
    # 1: Crust Dark Orange  – outline + crust arc
    # 2: Pepperoni Red      – pepperoni circles
    # 3: Text Dark Navy     – "Diane | Lorenzo"
    # -----------------------------------------------------------------------
    thread_colors = [
        (255, 215,   0),   # 0 Cheese yellow
        (180,  80,   5),   # 1 Crust brown/orange
        (192,  57,  43),   # 2 Pepperoni red
        ( 20,  20, 100),   # 3 Text navy
    ]

    all_stitch_cmds = []  # list of (cmd, dx_or_abs, dy_or_abs) but we'll work in abs then convert

    def cmds_from_run(abs_points, first=True):
        """Convert list of abs points → relative stitch commands."""
        cmds = []
        prev = (0, 0) if first else None
        for i, pt in enumerate(abs_points):
            x, y = round(pt[0]), round(pt[1])
            if i == 0:
                if prev is not None:
                    dx, dy = x - prev[0], y - prev[1]
                else:
                    dx, dy = x, y
                cmds.append(('jump', dx, dy))
            else:
                prev_pt = abs_points[i - 1]
                dx = x - round(prev_pt[0])
                dy = y - round(prev_pt[1])
                cmds.append(('stitch', dx, dy))
        return cmds

    current_pos = [0, 0]

    def add_run(abs_pts):
        """Emit jump to first point, then stitch through rest."""
        if not abs_pts:
            return
        x0, y0 = round(abs_pts[0][0]), round(abs_pts[0][1])
        dx, dy = x0 - current_pos[0], y0 - current_pos[1]
        all_stitch_cmds.append(('jump', dx, dy))
        current_pos[0] = x0
        current_pos[1] = y0
        for pt in abs_pts[1:]:
            x, y = round(pt[0]), round(pt[1])
            dx = x - current_pos[0]
            dy = y - current_pos[1]
            all_stitch_cmds.append(('stitch', dx, dy))
            current_pos[0] = x
            current_pos[1] = y

    # -----------------------------------------------------------------------
    # COLOR 0: Cheese fill
    # -----------------------------------------------------------------------
    print("Generating cheese fill...")
    crust_width_mm = 7
    crust_width = crust_width_mm * 10
    fill_R = R - crust_width

    # Decorative border ring (running stitch around hoop interior edge)
    border_R = (hoop // 2) - border_pad
    border_arc = arc_points(0, 0, border_R, 0, 360, stitch_len_mm)
    add_run(border_arc)

    # Cheese wedge fill
    fill_pts = wedge_fill(cx, cy, fill_R, a1, a2, satin_spacing_mm, stitch_len_mm)
    if fill_pts:
        add_run(fill_pts)

    # -----------------------------------------------------------------------
    # COLOR CHANGE → COLOR 1: Crust outline + arc satin
    # -----------------------------------------------------------------------
    all_stitch_cmds.append(('color_change',))
    current_pos[0] = 0; current_pos[1] = 0  # viewer resets to origin on color change

    print("Generating crust...")
    # Outline: left radial edge
    a1_rad = math.radians(a1)
    a2_rad = math.radians(a2)

    left_edge = running_stitch_line(
        cx, cy,
        cx + R * math.cos(a1_rad), cy + R * math.sin(a1_rad),
        stitch_len_mm
    )
    add_run(left_edge)

    # Arc (crust)
    arc_pts_outer = arc_points(cx, cy, R, a1, a2, stitch_len_mm)
    add_run(arc_pts_outer)

    # Right radial edge back to center
    right_edge = running_stitch_line(
        cx + R * math.cos(a2_rad), cy + R * math.sin(a2_rad),
        cx, cy,
        stitch_len_mm
    )
    add_run(right_edge)

    # Satin crust band (triple-pass at different radii for thick look)
    for pass_r in [R - crust_width * 0.2, R - crust_width * 0.5, R - crust_width * 0.8]:
        arc_inner = arc_points(cx, cy, pass_r, a1, a2, stitch_len_mm)
        add_run(arc_inner)

    # Radial texture lines across crust (like baked scoring)
    num_radial = 6
    for i in range(1, num_radial):
        ang = a1 + (a2 - a1) * i / num_radial
        ang_r = math.radians(ang)
        inner_pt = (cx + fill_R * math.cos(ang_r), cy + fill_R * math.sin(ang_r))
        outer_pt = (cx + R * math.cos(ang_r),       cy + R * math.sin(ang_r))
        radial = running_stitch_line(inner_pt[0], inner_pt[1],
                                     outer_pt[0], outer_pt[1], stitch_len_mm)
        add_run(radial)

    # -----------------------------------------------------------------------
    # COLOR CHANGE → COLOR 2: Pepperoni
    # -----------------------------------------------------------------------
    all_stitch_cmds.append(('color_change',))
    current_pos[0] = 0; current_pos[1] = 0  # viewer resets to origin on color change

    print("Generating pepperoni...")
    pep_R_jef = 48  # pepperoni radius in JEF units (4.8 mm) – slightly larger
    pep_offset_up = 50  # shift all pepperoni up 5 mm (50 JEF units)
    center_ang_rad = math.radians(center_angle)
    pep_positions = []
    if num_pepperoni >= 1:
        # 1 pepperoni near the tip (bottom of wedge), at ~30% radius
        pr = fill_R * 0.30
        pep_positions.append((cx + pr * math.cos(center_ang_rad),
                               cy + pr * math.sin(center_ang_rad)))
    if num_pepperoni >= 2:
        # Upper-left pepperoni, near the crust
        offset_ang = math.radians(center_angle - slice_angle_deg * 0.28)
        pr2 = fill_R * 0.62
        pep_positions.append((cx + pr2 * math.cos(offset_ang),
                               cy + pr2 * math.sin(offset_ang)))
    if num_pepperoni >= 3:
        # Upper-right pepperoni, near the crust
        offset_ang = math.radians(center_angle + slice_angle_deg * 0.28)
        pr2 = fill_R * 0.62
        pep_positions.append((cx + pr2 * math.cos(offset_ang),
                               cy + pr2 * math.sin(offset_ang)))
    for extra in range(3, num_pepperoni):
        ang = math.radians(a1 + (a2 - a1) * (extra / num_pepperoni))
        pr = fill_R * 0.45
        pep_positions.append((cx + pr * math.cos(ang),
                               cy + pr * math.sin(ang)))
    # Apply the upward shift to all pepperoni
    pep_positions = [(px, py + pep_offset_up) for px, py in pep_positions]

    for pcx, pcy in pep_positions:
        # Outline
        pep_arc = arc_points(pcx, pcy, pep_R_jef, 0, 360, stitch_len_mm)
        add_run(pep_arc)
        # Fill
        pep_fill = circle_fill(pcx, pcy, pep_R_jef, satin_spacing_mm, stitch_len_mm)
        if pep_fill:
            add_run(pep_fill)

    # -----------------------------------------------------------------------
    # COLOR CHANGE → COLOR 3: Text "Diane | Lorenzo"
    # -----------------------------------------------------------------------
    all_stitch_cmds.append(('color_change',))
    current_pos[0] = 0; current_pos[1] = 0  # viewer resets to origin on color change

    print("Generating text...")
    # Position text just below the slice tip, using the computed gap
    text_y = cy - text_gap          # tip is at cy; text sits text_gap below
    text_y = max(-460, text_y)      # safety clamp within hoop
    text_runs = render_text_exact(text, 0, text_y, cap_height_mm=7.0, stitch_mm=stitch_len_mm)
    for run in text_runs:
        add_run(run)

    # Double-stitch the text for bolder appearance
    for run in text_runs:
        add_run(list(reversed(run)))

    # -----------------------------------------------------------------------
    # End of design
    # -----------------------------------------------------------------------
    all_stitch_cmds.append(('end',))

    # -----------------------------------------------------------------------
    # Encode stitches
    # -----------------------------------------------------------------------
    print("Encoding stitches...")
    stitch_bytes = encode_stitches(all_stitch_cmds)

    # Count actual stitches (non-jump, non-cmd 2-byte entries)
    num_stitches = sum(1 for c in all_stitch_cmds if c[0] == 'stitch')

    # -----------------------------------------------------------------------
    # Write JEF file
    # -----------------------------------------------------------------------
    write_jef(output, thread_colors, stitch_bytes, num_stitches, hoop_mm=100)

    filesize = os.path.getsize(output)
    print(f"\n✅ Written '{output}'")
    print(f"   File size     : {filesize} bytes")
    print(f"   Thread colors : {len(thread_colors)}")
    print(f"   Color changes : {len(thread_colors) - 1}")
    print(f"   Stitch cmds   : {len(all_stitch_cmds)}")
    print(f"   Stitches      : {num_stitches}")
    print(f"   Design area   : {radius_mm*2}×{radius_mm*2} mm (within 100×100 mm hoop)")

    return output


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a pizza-slice JEF embroidery file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--radius',      type=float, default=40.0,
                        help="Pizza slice outer radius (mm)")
    parser.add_argument('--angle',       type=float, default=90.0,
                        help="Slice angle (degrees)")
    parser.add_argument('--pepperoni',   type=int,   default=3,
                        help="Number of pepperoni toppings")
    parser.add_argument('--text',        type=str,   default="Diane | Lorenzo",
                        help="Text to embroider below the slice")
    parser.add_argument('--stitch-len',  type=float, default=1.5,
                        help="Running stitch length (mm)")
    parser.add_argument('--satin-gap',   type=float, default=0.45,
                        help="Fill row spacing for satin fill (mm)")
    parser.add_argument('--output',      type=str,   default="pizza.jef",
                        help="Output JEF filename")
    args = parser.parse_args()

    print("=" * 55)
    print("  Pizza Embroidery Generator – MECEE4606")
    print("=" * 55)
    print(f"  Radius      : {args.radius} mm")
    print(f"  Slice angle : {args.angle}°")
    print(f"  Pepperoni   : {args.pepperoni}")
    print(f"  Text        : '{args.text}'")
    print(f"  Stitch len  : {args.stitch_len} mm")
    print(f"  Satin gap   : {args.satin_gap} mm")
    print(f"  Output      : {args.output}")
    print("-" * 55)

    generate_pizza_embroidery(
        radius_mm=args.radius,
        slice_angle_deg=args.angle,
        num_pepperoni=args.pepperoni,
        text=args.text,
        stitch_len_mm=args.stitch_len,
        satin_spacing_mm=args.satin_gap,
        output=args.output,
    )


if __name__ == '__main__':
    main()
