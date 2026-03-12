#!/usr/bin/env python3
"""
generate_fractal_v2.py
======================
Generates a Koch snowflake fractal embroidery JEF file – single-color,
continuous stitch design with no text.

Changes from v1:
  - Single thread color (one continuous path, no color changes)
  - No text
  - Outer snowflake → inner snowflake → border ring stitched continuously
  - Double-pass on each element for bolder look

Usage:
    python3 generate_fractal_v2.py [options]

Units: 1 JEF unit = 0.1 mm  →  10×10 cm hoop = 1000×1000 JEF units
"""

import argparse
import math
import struct
import os
from datetime import datetime

# Reuse helpers from generate_embroidery.py in the same folder
import sys
sys.path.insert(0, os.path.dirname(__file__))
from generate_embroidery import (
    encode_stitches, running_stitch_line, arc_points,
)


# ---------------------------------------------------------------------------
# Koch snowflake fractal
# ---------------------------------------------------------------------------

def koch_points(p1, p2, depth):
    """
    Recursively subdivide segment p1→p2 using Koch curve rule.
    Returns ordered list of (x, y) points (includes p1, excludes p2
    so segments can be chained without duplicating junction points).
    """
    if depth == 0:
        return [p1]

    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1

    # Trisection points
    A = (x1 + dx / 3,       y1 + dy / 3)
    B = (x1 + 2 * dx / 3,   y1 + 2 * dy / 3)

    # Peak of equilateral triangle on the middle third
    angle = math.atan2(dy, dx) - math.pi / 3   # rotate -60°
    length = math.hypot(dx, dy) / 3
    P = (A[0] + length * math.cos(angle),
         A[1] + length * math.sin(angle))

    return (koch_points(p1, A, depth - 1) +
            koch_points(A,  P, depth - 1) +
            koch_points(P,  B, depth - 1) +
            koch_points(B, p2, depth - 1))


def snowflake_points(cx, cy, radius, depth):
    """
    Return all edge points of a Koch snowflake (equilateral triangle base).
    """
    # Base equilateral triangle vertices (point up: vertex at top)
    angles = [90, 90 - 120, 90 - 240]  # top, lower-right, lower-left
    verts = [(cx + radius * math.cos(math.radians(a)),
              cy + radius * math.sin(math.radians(a)))
             for a in angles]

    pts = []
    for i in range(3):
        p1 = verts[i]
        p2 = verts[(i + 1) % 3]
        pts.extend(koch_points(p1, p2, depth))

    # Close the loop
    pts.append(pts[0])
    return pts


def densify(pts, stitch_mm=1.5):
    """
    Insert intermediate points along each segment so stitch spacing ≤ stitch_mm.
    """
    out = []
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        seg = running_stitch_line(x0, y0, x1, y1, stitch_mm)
        if out:
            out.extend(seg[1:])
        else:
            out.extend(seg)
    return out


# ---------------------------------------------------------------------------
# JEF write helper
# ---------------------------------------------------------------------------

def write_jef(filename, thread_colors, stitch_data_bytes, num_stitches, hoop_mm=100):
    num_colors = len(thread_colors)
    now = datetime.now()
    thread_table_size = num_colors * 32
    stitch_offset = 256 + thread_table_size

    header = bytearray(256)
    struct.pack_into('<I', header, 0, stitch_offset)
    header[4:12] = now.strftime('%Y%m%d').encode('ascii')
    header[12:20] = now.strftime('%H%M%S00').encode('ascii')
    header[20] = ord('A')
    struct.pack_into('<I', header, 24, num_colors - 1)
    struct.pack_into('<I', header, 28, len(stitch_data_bytes) // 2)

    half = hoop_mm * 5
    hoop_data = [-half, half, -half, half] * 4
    off = 32
    for val in hoop_data:
        struct.pack_into('<i', header, off, int(val))
        off += 4
    struct.pack_into('<I', header, 128, num_colors)

    thread_table = bytearray(thread_table_size)
    for i, (r, g, b) in enumerate(thread_colors):
        base = i * 32
        thread_table[base], thread_table[base+1], thread_table[base+2] = r, g, b

    with open(filename, 'wb') as f:
        f.write(header)
        f.write(thread_table)
        f.write(stitch_data_bytes)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_fractal_v2(
    depth=4,
    radius_mm=40,
    stitch_len_mm=1.5,
    output="fractal_v2.jef"
):
    """
    Generate a single-color, continuous Koch snowflake fractal embroidery JEF.

    Parameters
    ----------
    depth         : Koch recursion depth (3–5 recommended)
    radius_mm     : circumradius of the base triangle (mm)
    stitch_len_mm : running stitch length (mm)
    output        : output .jef filename
    """
    R = radius_mm * 10     # JEF units
    hoop = 1000

    # Center the snowflake in the hoop (no text, so true center)
    cx = 0
    cy = 0

    # Single thread color – Dark Slate Blue
    thread_colors = [
        (72, 61, 139),   # Dark Slate Blue
    ]

    all_stitch_cmds = []
    current_pos = [0, 0]

    def add_run(abs_pts):
        """Emit jump to first point, then stitch through the rest."""
        if not abs_pts:
            return
        x0, y0 = round(abs_pts[0][0]), round(abs_pts[0][1])
        dx, dy = x0 - current_pos[0], y0 - current_pos[1]
        all_stitch_cmds.append(('jump', dx, dy))
        current_pos[0] = x0
        current_pos[1] = y0
        for pt in abs_pts[1:]:
            x, y = round(pt[0]), round(pt[1])
            all_stitch_cmds.append(('stitch', x - current_pos[0], y - current_pos[1]))
            current_pos[0] = x
            current_pos[1] = y


    # -------------------------------------------------------------------
    # 1. Border ring (outermost element)
    # -------------------------------------------------------------------
    print("Generating border ring...")
    border_pad = 20
    border_R = (hoop // 2) - border_pad
    border_arc = arc_points(0, 0, border_R, 0, 360, stitch_len_mm)
    add_run(border_arc)
    # Double-pass for bolder border
    add_run(list(reversed(border_arc)))

    # -------------------------------------------------------------------
    # 2. Outer Koch snowflake (full depth)
    # -------------------------------------------------------------------
    print(f"Generating outer snowflake (depth={depth})...")
    outer_pts = snowflake_points(cx, cy, R, depth)
    outer_dense = densify(outer_pts, stitch_len_mm)
    add_run(outer_dense)
    # Double-pass for bolder look
    add_run(list(reversed(outer_dense)))

    # -------------------------------------------------------------------
    # 3. Inner Koch snowflake (depth-1, smaller radius)
    # -------------------------------------------------------------------
    inner_depth = max(1, depth - 1)
    inner_R = R * 0.55
    print(f"Generating inner snowflake (depth={inner_depth})...")
    inner_pts = snowflake_points(cx, cy, inner_R, inner_depth)
    inner_dense = densify(inner_pts, stitch_len_mm)
    add_run(inner_dense)
    # Double-pass
    add_run(list(reversed(inner_dense)))


    # -------------------------------------------------------------------
    # End
    # -------------------------------------------------------------------
    all_stitch_cmds.append(('end',))

    print("Encoding stitches...")
    stitch_bytes = encode_stitches(all_stitch_cmds)
    num_stitches = sum(1 for c in all_stitch_cmds if c[0] == 'stitch')

    write_jef(output, thread_colors, stitch_bytes, num_stitches, hoop_mm=100)

    filesize = os.path.getsize(output)
    print(f"\n✅ Written '{output}'")
    print(f"   File size     : {filesize} bytes")
    print(f"   Fractal depth : {depth}")
    print(f"   Thread colors : {len(thread_colors)} (single color)")
    print(f"   Stitch cmds   : {len(all_stitch_cmds)}")
    print(f"   Stitches      : {num_stitches}")
    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a single-color Koch snowflake fractal JEF embroidery file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--depth',      type=int,   default=4,
                        help="Koch recursion depth (3-5 recommended)")
    parser.add_argument('--radius',     type=float, default=40.0,
                        help="Circumradius of base triangle (mm)")
    parser.add_argument('--stitch-len', type=float, default=1.5,
                        help="Running stitch length (mm)")
    parser.add_argument('--output',     type=str,   default="fractal_v2.jef",
                        help="Output JEF filename")
    args = parser.parse_args()

    print("=" * 55)
    print("  Koch Snowflake Fractal v2 – Single Color – MECEE4606")
    print("=" * 55)
    print(f"  Depth       : {args.depth}")
    print(f"  Radius      : {args.radius} mm")
    print(f"  Stitch len  : {args.stitch_len} mm")
    print(f"  Output      : {args.output}")
    print("-" * 55)

    generate_fractal_v2(
        depth=args.depth,
        radius_mm=args.radius,
        stitch_len_mm=args.stitch_len,
        output=args.output,
    )


if __name__ == '__main__':
    main()
