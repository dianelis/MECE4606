#!/usr/bin/env python3
"""
jef_to_svg.py
=============
Reads a Janome JEF embroidery file and converts the actual stitch data
into an SVG file for accurate visual preview.

Usage:
    python3 jef_to_svg.py <input.jef> [output.svg]

    If output is omitted, it uses the same base name as the input.
"""

import struct
import sys
import os
import math


# ---------------------------------------------------------------------------
# Default thread colors (used if the JEF thread table has no RGB data).
# Indexed by color segment order (0, 1, 2, ...).
# ---------------------------------------------------------------------------
FALLBACK_COLORS = [
    "#FFD700",   # 0 Cheese yellow
    "#B45009",   # 1 Crust brown
    "#C0392B",   # 2 Pepperoni red
    "#141464",   # 3 Text navy
    "#228B22",   # 4 Green
    "#9B59B6",   # 5 Purple
    "#E67E22",   # 6 Orange
    "#1ABC9C",   # 7 Teal
]


# ---------------------------------------------------------------------------
# JEF parser
# ---------------------------------------------------------------------------

def parse_jef(filename):
    """
    Parse a JEF file and return:
        - colors: list of (r, g, b) per thread
        - segments: list of stitch-point lists, one per thread color
          Each point: (x, y, is_jump)
    Coordinates are absolute, in JEF units (0.1 mm), centered at (0, 0).
    """
    with open(filename, 'rb') as f:
        data = f.read()

    if len(data) < 256:
        raise ValueError("File too short to be a valid JEF file.")

    # Header fields
    stitch_offset = struct.unpack_from('<I', data, 0)[0]
    num_colors    = struct.unpack_from('<I', data, 128)[0]

    # Thread color table (32 bytes per thread, starts at byte 256)
    colors = []
    for i in range(num_colors):
        base = 256 + i * 32
        if base + 3 <= len(data):
            r, g, b = data[base], data[base + 1], data[base + 2]
            colors.append((r, g, b))
        else:
            colors.append(None)

    # Stitch data
    stitch_data = data[stitch_offset:]

    segments = []   # list of lists of (x, y, is_jump)
    current_segment = []
    x, y = 0, 0
    i = 0

    while i < len(stitch_data) - 1:
        b0 = stitch_data[i]
        b1 = stitch_data[i + 1]

        if b0 == 0x80:
            cmd = b1
            if cmd == 0x10:
                # End of design
                break
            elif cmd == 0x02:
                # Color change
                if current_segment:
                    segments.append(current_segment)
                current_segment = []
                x, y = 0, 0   # position resets after color change
                i += 2
                continue
            elif cmd == 0x01:
                # Jump stitch — next 2 bytes are signed dx, dy
                if i + 3 < len(stitch_data):
                    dx = struct.unpack_from('b', stitch_data, i + 2)[0]
                    dy = struct.unpack_from('b', stitch_data, i + 3)[0]
                    x += dx
                    y += dy
                    current_segment.append((x, y, True))
                i += 4
                continue
            else:
                i += 2
                continue
        else:
            # Normal stitch: two signed bytes dx, dy
            dx = struct.unpack_from('b', stitch_data, i)[0]
            dy = struct.unpack_from('b', stitch_data, i + 1)[0]
            x += dx
            y += dy
            current_segment.append((x, y, False))
            i += 2

    if current_segment:
        segments.append(current_segment)

    return colors, segments


# ---------------------------------------------------------------------------
# SVG renderer
# ---------------------------------------------------------------------------

def segments_to_svg(colors, segments, output_svg,
                    hoop_mm=100, scale=4.0, show_jumps=False):
    """
    Render parsed JEF stitch segments to an SVG file.

    Parameters
    ----------
    colors      : list of (r,g,b) per segment (may be shorter than segments)
    segments    : list of [(x, y, is_jump), ...] per color
    output_svg  : output file path
    hoop_mm     : hoop size in mm (default 100 = 10x10 cm)
    scale       : SVG pixels per JEF unit (default 4 → 1 mm = 4 px)
    show_jumps  : if True, draw jump moves as faint dashed lines
    """
    hoop_jef   = hoop_mm * 10          # hoop in JEF units
    canvas     = hoop_jef * scale      # SVG canvas size in px
    cx = cy    = canvas / 2            # center of canvas

    def to_svg(jef_x, jef_y):
        """JEF coords (y-up, centered at 0) → SVG coords (y-down)."""
        return cx + jef_x * scale, cy - jef_y * scale

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'width="{canvas:.0f}" height="{canvas:.0f}" '
                 f'style="background:#f8f4f0">')

    # Hoop boundary
    lines.append(f'  <rect x="0" y="0" width="{canvas:.0f}" height="{canvas:.0f}" '
                 f'fill="none" stroke="#ccc" stroke-width="2"/>')
    # Hoop center crosshair (faint)
    lines.append(f'  <line x1="{cx:.1f}" y1="0" x2="{cx:.1f}" y2="{canvas:.0f}" '
                 f'stroke="#ddd" stroke-width="0.5"/>')
    lines.append(f'  <line x1="0" y1="{cy:.1f}" x2="{canvas:.0f}" y2="{cy:.1f}" '
                 f'stroke="#ddd" stroke-width="0.5"/>')

    for seg_idx, points in enumerate(segments):
        # Resolve color
        if seg_idx < len(colors) and colors[seg_idx] is not None:
            r, g, b = colors[seg_idx]
            # Use fallback if all zeros (uninitialised thread entry)
            if r == 0 and g == 0 and b == 0:
                color = FALLBACK_COLORS[seg_idx % len(FALLBACK_COLORS)]
            else:
                color = f"rgb({r},{g},{b})"
        else:
            color = FALLBACK_COLORS[seg_idx % len(FALLBACK_COLORS)]

        # Split into continuous runs (break on jumps)
        runs = []
        current_run = []
        jump_moves = []

        for x, y, is_jump in points:
            if is_jump:
                if current_run:
                    runs.append(current_run)
                    current_run = []
                if show_jumps and len(current_run) == 0:
                    jump_moves.append((x, y))
                current_run = [(x, y)]
            else:
                current_run.append((x, y))

        if current_run:
            runs.append(current_run)

        lines.append(f'  <!-- Color {seg_idx}: {color} ({len(points)} pts, {len(runs)} runs) -->')

        # Draw jump paths (optional, faint)
        if show_jumps and jump_moves:
            for jx, jy in jump_moves:
                sx, sy = to_svg(jx, jy)
                lines.append(f'  <circle cx="{sx:.1f}" cy="{sy:.1f}" r="1" '
                              f'fill="none" stroke="#ccc" stroke-width="0.5"/>')

        # Draw stitch runs as polylines
        for run in runs:
            if len(run) < 2:
                continue
            pts_str = " ".join(f"{to_svg(x,y)[0]:.1f},{to_svg(x,y)[1]:.1f}"
                               for x, y in run)
            lines.append(f'  <polyline points="{pts_str}" '
                         f'fill="none" stroke="{color}" stroke-width="1.2" '
                         f'stroke-linecap="round" stroke-linejoin="round"/>')

    # Legend
    legend_x, legend_y = 10, 10
    lines.append(f'  <rect x="{legend_x}" y="{legend_y}" '
                 f'width="160" height="{max(1,len(segments))*22+10}" '
                 f'fill="white" fill-opacity="0.8" rx="4"/>')
    for seg_idx in range(len(segments)):
        if seg_idx < len(colors) and colors[seg_idx] is not None:
            r, g, b = colors[seg_idx]
            c = f"rgb({r},{g},{b})" if (r or g or b) else FALLBACK_COLORS[seg_idx % len(FALLBACK_COLORS)]
        else:
            c = FALLBACK_COLORS[seg_idx % len(FALLBACK_COLORS)]
        ly = legend_y + 10 + seg_idx * 22
        lines.append(f'  <rect x="{legend_x+8}" y="{ly}" width="16" height="14" '
                     f'fill="{c}" rx="2"/>')
        lines.append(f'  <text x="{legend_x+30}" y="{ly+11}" '
                     f'font-family="sans-serif" font-size="11" fill="#333">'
                     f'Thread {seg_idx+1}</text>')

    lines.append('</svg>')

    with open(output_svg, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✅ SVG written: {output_svg}")
    print(f"   Canvas size : {canvas:.0f}×{canvas:.0f} px  (scale {scale}×)")
    print(f"   Threads     : {len(segments)}")
    for i, seg in enumerate(segments):
        stitches = sum(1 for _, _, j in seg if not j)
        jumps    = sum(1 for _, _, j in seg if j)
        print(f"   Thread {i+1:2d}   : {stitches} stitches, {jumps} jumps")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 jef_to_svg.py <input.jef> [output.svg] [--show-jumps]")
        sys.exit(1)

    jef_file   = sys.argv[1]
    show_jumps = "--show-jumps" in sys.argv

    # Output filename
    if len(sys.argv) >= 3 and not sys.argv[2].startswith("--"):
        svg_file = sys.argv[2]
    else:
        base = os.path.splitext(jef_file)[0]
        svg_file = base + "_preview.svg"

    print(f"Reading {jef_file} ...")
    colors, segments = parse_jef(jef_file)
    print(f"  Found {len(colors)} thread entries, {len(segments)} stitch segments")

    segments_to_svg(colors, segments, svg_file, show_jumps=show_jumps)


if __name__ == "__main__":
    main()
