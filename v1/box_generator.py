#!/usr/bin/env python3
"""
This program generates SVG laser cutter files for a square open bin box.
It runs as a CLI and produces clean, compliant SVG files.
"""

import math
import os
import base64

# --- Constants ---

STROKE_CUT = "rgb(255,0,0)"
STROKE_ENGRAVE = "rgb(0,0,255)"
STROKE_WIDTH = "0.2"

# --- SVG Writer Class ---

class SVGGenerator:
    """A simple self-contained SVG generator."""
    def __init__(self, filename, width, height, unit="mm"):
        self.filename = os.path.join("output", filename)
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        self.width = width
        self.height = height
        self.unit = unit
        self.elements = []
        # Pre-create standard groups
        self.groups = {
            "CUT": [],
            "ENGRAVE": []
        }

    def add_line(self, x1, y1, x2, y2, mode="CUT"):
        """Adds a line to the specified group (CUT or ENGRAVE)."""
        line_str = f'<line x1="{x1:.4f}" y1="{y1:.4f}" x2="{x2:.4f}" y2="{y2:.4f}" />'
        if mode in self.groups:
            self.groups[mode].append(line_str)
        else:
            print(f"Warning: Unknown mode {mode}, defaulting to CUT")
            self.groups["CUT"].append(line_str)

    def add_rect(self, x, y, w, h, mode="CUT"):
        """Adds a rectangle (as lines) for compatibility."""
        self.add_line(x, y, x + w, y, mode)
        self.add_line(x + w, y, x + w, y + h, mode)
        self.add_line(x + w, y + h, x, y + h, mode)
        self.add_line(x, y + h, x, y, mode)

    def add_image(self, x, y, w, h, href, mode="ENGRAVE"):
        """Adds an image tag."""
        img_str = f'<image x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" href="{href}" xlink:href="{href}" />'
        if mode in self.groups:
            self.groups[mode].append(img_str)

    def add_circle(self, cx, cy, r, mode="CUT"):
        """Adds a circle."""
        circle_str = f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r:.4f}" />'
        if mode in self.groups:
            self.groups[mode].append(circle_str)

    def add_polyline(self, points, mode="ENGRAVE"):
        """Adds a polyline from a list of (x,y) tuples."""
        if not points:
            return
        points_str = " ".join([f"{p[0]:.4f},{p[1]:.4f}" for p in points])
        # Polyline element
        poly_str = f'<polyline points="{points_str}" />'
        if mode in self.groups:
            self.groups[mode].append(poly_str)

    def add_text(self, x, y, text, font_size=5, mode="ENGRAVE"):
        """Adds text centered at x,y."""
        # Note: SVG text centering uses text-anchor="middle"
        # We will follow spec: stroke blue, fill none.
        t_str = (f'<text x="{x:.4f}" y="{y:.4f}" font-family="sans-serif" font-size="{font_size}" '
                 f'text-anchor="middle" dominant-baseline="middle">{text}</text>')
        if mode in self.groups:
            self.groups[mode].append(t_str)

    def save(self):
        """Writes the SVG file."""
        with open(self.filename, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            f.write(f'<svg width="{self.width}{self.unit}" height="{self.height}{self.unit}" '
                    f'viewBox="0 0 {self.width} {self.height}" '
                    f'xmlns="http://www.w3.org/2000/svg" '
                    f'xmlns:xlink="http://www.w3.org/1999/xlink">\n')
            
            # Write Groups
            # CUT
            f.write(f'  <g id="CUT" stroke="{STROKE_CUT}" stroke_width="{STROKE_WIDTH}" fill="none">\n')
            for el in self.groups["CUT"]:
                f.write(f'    {el}\n')
            f.write('  </g>\n')

            # ENGRAVE
            f.write(f'  <g id="ENGRAVE" stroke="{STROKE_ENGRAVE}" stroke_width="{STROKE_WIDTH}" fill="none">\n')
            for el in self.groups["ENGRAVE"]:
                f.write(f'    {el}\n')
            f.write('  </g>\n')
            
            f.write('</svg>\n')
        print(f"Successfully generated: {self.filename}")





# --- Geometry Functions ---

def generate_box_svg(params, filename="box_square.svg"):
    """Generates the acrylic finger-joint box layout."""
    # Unpack params
    W = params['W']   # Width (x-dimension of Base)
    D = params['D']   # Depth (y-dimension of Base)
    H = params['H']   # Height
    t = params['t']
    stock_w = params['stock_w']
    stock_h = params['stock_h']

    # --- New Finger Joint Logic ---

    # We need to draw 5 parts: Base, Front, Back, Left, Right.
    # Layout Strategy:
    # Row 1: Front, Back
    # Row 2: Left, Right, Base
    
    # Margin between parts
    margin = 5
    
    # Dimensions:
    # Base: W x D (Inner)
    # Front/Back: (W + 2t) x H (Covers corners)
    # Left/Right: D x H (Fits between Front/Back)
    
    # Parts List with Sizes (W, H)
    parts = {}
    
    # 1. Base (W x D)
    parts['Base'] = {'w': W, 'h': D}
    
    # 2. Front (W+2t x H)
    parts['Front'] = {'w': W + 2*t, 'h': H}
    
    # 3. Back (W+2t x H)
    parts['Back'] = {'w': W + 2*t, 'h': H}
    
    # 4. Left (D x H)
    parts['Left'] = {'w': D, 'h': H}
    
    # 5. Right (D x H)
    parts['Right'] = {'w': D, 'h': H}

    if 'divider_pos' in params:
        # Divider runs parallel to Left/Right walls, splitting Width W
        parts['Divider'] = {'w': D, 'h': H} # Divider width is D, height is H
    
    # 6. Lid (if enabled) - outer dimensions match box
    if params.get('lid', True):
        # Main lid panel: Covers W+2t x D+2t
        lid_w_outer = W + 2*t
        lid_d_outer = D + 2*t
        parts['Lid'] = {'w': lid_w_outer, 'h': lid_d_outer}

    
    # --- Fractal Generator ---
    def generate_sierpinski(cx, cy, size, depth=4):
        """Generates a Sierpinski triangle centered at cx,cy."""
        lines = []
        # Triangle height h = size * sqrt(3)/2
        h = size * math.sqrt(3) / 2
        
        # Vertices relative to center (centroid)
        # Centroid is h/3 from base.
        # Top vertex: (0, -2h/3)
        # Bot Left: (-s/2, h/3)
        # Bot Right: (s/2, h/3)
        
        # But let's define by top vertex (x, y) for recursion simpler?
        # Let's stick to the previous implementation logic or similar.
        # Top (ax, ay), Right (bx, by), Left (cx, cy)
        
        # Calculate vertices centered at cx, cy
        # r = size / sqrt(3) is dist to vertex
        r = size / math.sqrt(3)
        
        ax, ay = cx, cy - r
        bx, by = cx + size/2, cy + r/2
        cx_pt, cy_pt = cx - size/2, cy + r/2
        
        def sierpinski(p1, p2, p3, d):
            if d == 0:
                lines.append([p1, p2, p3, p1])
            else:
                # Midpoints
                p12 = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
                p23 = ((p2[0]+p3[0])/2, (p2[1]+p3[1])/2)
                p31 = ((p3[0]+p1[0])/2, (p3[1]+p1[1])/2)
                
                sierpinski(p1, p12, p31, d-1)
                sierpinski(p12, p2, p23, d-1)
                sierpinski(p31, p23, p3, d-1)

        sierpinski((ax, ay), (bx, by), (cx_pt, cy_pt), depth)
        return lines

    # Layout Calculation
    max_row_h = H
    # total_w_row1 = parts['Front']['w'] + parts['Back']['w'] + parts['Left']['w'] + parts['Right']['w'] + 4*margin
    # Row 1: Front, Back
    # Row 2: Left, Right, Base, Divider?
    
    x_cursor = margin
    y_cursor = margin
    
    # Front
    parts['Front']['x'] = x_cursor
    parts['Front']['y'] = y_cursor
    x_cursor += parts['Front']['w'] + margin
    
    # Back
    parts['Back']['x'] = x_cursor
    parts['Back']['y'] = y_cursor
    
    # Next Row
    y_cursor += H + margin
    x_cursor = margin
    
    # Left
    parts['Left']['x'] = x_cursor
    parts['Left']['y'] = y_cursor
    x_cursor += parts['Left']['w'] + margin
    
    # Right
    parts['Right']['x'] = x_cursor
    parts['Right']['y'] = y_cursor
    x_cursor += parts['Right']['w'] + margin
    
    # Base
    parts['Base']['x'] = x_cursor
    parts['Base']['y'] = y_cursor
    x_cursor += parts['Base']['w'] + margin

    # Divider
    if 'Divider' in parts:
        parts['Divider']['x'] = x_cursor
        parts['Divider']['y'] = y_cursor
        x_cursor += parts['Divider']['w'] + margin
        # Check stock width
        if x_cursor > stock_w:
            # Move to Row 3 if needed
            x_cursor = margin
            y_cursor += max(parts['Base']['h'], parts['Left']['h']) + margin
            parts['Divider']['x'] = x_cursor
            parts['Divider']['y'] = y_cursor
            x_cursor += parts['Divider']['w'] + margin
    
    # Lid
    if 'Lid' in parts:
        # Add extra spacing after divider
        x_cursor += margin * 2  # Extra spacing between divider and lid
        
        # Check if lid fits on current row
        if x_cursor + parts['Lid']['w'] > stock_w:
            # Move to next row
            x_cursor = margin
            # Max height of previous row elements
            prev_row_max_h = 0
            if 'Base' in parts: prev_row_max_h = max(prev_row_max_h, parts['Base']['h'])
            if 'Divider' in parts: prev_row_max_h = max(prev_row_max_h, parts['Divider']['h'])
            if prev_row_max_h == 0: # If no base or divider, use H
                prev_row_max_h = H
            y_cursor += prev_row_max_h + margin
        
        # Calculate vertical space needed for lips (above lid)
        # 4 strips of height t + spacing
        lip_spacing = 5.0
        lip_reserved_h = 4 * (t + lip_spacing)
        
        parts['Lid']['x'] = x_cursor
        # Shift Lid Y down to make room for lips above it
        parts['Lid']['y'] = y_cursor + lip_reserved_h
            
    # Check Layout Bounds
    max_x = 0
    max_y = 0
    for p in parts.values():
        max_x = max(max_x, p['x'] + p['w'])
        max_y = max(max_y, p['y'] + p['h'])
    
    if max_x + margin > stock_w or max_y + margin > stock_h:
        print(f"Error: Layout size ({max_x+margin:.1f} x {max_y+margin:.1f} mm) larger than stock ({stock_w} x {stock_h} mm).")
        return False
        
    svg = SVGGenerator(filename, stock_w, stock_h)
    
    # Finger parameters
    tab_size = 10 # nominal 10mm tabs
    
    def draw_finger_edge(x1, y1, x2, y2, thickness, parity, mode="CUT"):
        """
        Draws a finger-jointed line from (x1, y1) to (x2, y2).
        parity: 1 = start with TAB (stick out), -1 = start with SLOT (dent in).
        Direction: currently horizontal or vertical only.
        thickness: t (depth of tab/slot).
        """
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0: return

        # Calculate tabs (ensure odd number for symmetry)
        n_tabs = max(3, int(length // tab_size))
        if n_tabs % 2 == 0: n_tabs += 1
        actual_tab_w = length / n_tabs
        
        # Geometry vectors
        ux = dx / length
        uy = dy / length
        
        # Initialize traversal
        curr_x, curr_y = x1, y1
        side = parity # 1 = Out, -1 = In
        points = [(x1, y1)]

        # Finger Joint Logic:
        # Parity 1 (Protruding Tab): [Tab (+t), Gap (0), Tab (+t)...]
        # Parity -1 (Recessed Slot): [Gap (0), Tab (+t), Gap (0)...]
        # Note: "Left" of vector (x1->x2) defines the protrusion direction.
        
        for i in range(n_tabs):
            # Calculate segment endpoint
            p_end_center = (x1 + (i+1)*actual_tab_w*ux, y1 + (i+1)*actual_tab_w*uy)
            
            current_offset_mag = thickness if side == 1 else 0
            
            # Calc start/end of this segment at the offset
            seg_start_x = curr_x + (-uy * current_offset_mag) # Move Left
            seg_start_y = curr_y + ( ux * current_offset_mag)
            
            seg_end_x = p_end_center[0] + (-uy * current_offset_mag)
            seg_end_y = p_end_center[1] + ( ux * current_offset_mag)
            
            # If this is not the first point, adding a perpendicular connector from previous
            if i > 0:
                svg.add_line(points[-1][0], points[-1][1], seg_start_x, seg_start_y, mode)
                
            # Corner Logic: Corner is part of a tab (stronger).
            if i == 0:
                 svg.add_line(x1, y1, seg_start_x, seg_start_y, mode)
            
            # Add segment
            svg.add_line(seg_start_x, seg_start_y, seg_end_x, seg_end_y, mode)
            points.append((seg_end_x, seg_end_y))
            
            # Flip side for next segment
            side = -side
            curr_x, curr_y = p_end_center[0], p_end_center[1]
            
        # Connect to final x2,y2
        svg.add_line(points[-1][0], points[-1][1], x2, y2, mode)



    # --- IMPROVED SCREW & FABRICATION LOGIC ---
    # --- IMPROVED SCREW & FABRICATION LOGIC ---
    # Mechanical Intent: Optional reinforcement. Relies on Base-to-Wall connections (clamp).
    # "Fabrication Safe": Holes are kept far from cuts to prevent cracking.
    
    # Fastener Specs: M3 Machine Screw
    screw_diam = 3.2     # 3.2mm Clearance hole for M3 (standard fabrication fit)
    nut_w = 5.5          # M3 Square Nut Width
    nut_h = 2.4          # M3 Square Nut Thickness
    nut_off = 8.0        # Center distance for nut pocket
    
    # Safety Margins
    # Minimum distance from any cut edge (including finger roots)
    # Finger roots penetrate 't' deep. So hole center must be > t + (2*t) = 3*t from edge.
    SAFETY_FACTOR_EDGE = 3.0 # Multiplier of thickness 't'
    
    # Dynamic Offset Calculation
    # Ensures hole is safely inside the "meat" of the panel
    safe_offset = max(t * SAFETY_FACTOR_EDGE, 9.0) # At least 9mm or 3*t
    
    EDGE_OFFSET_X = safe_offset 
    EDGE_OFFSET_Y = safe_offset
    MIN_EDGE = 2.0 * t   # 2x thickness min distance from any feature
    
    # Check if we are doing screws
    do_screws = params.get('screws', True)
    
    # BOM tracking
    screw_count = 0
    nut_count = 0
    
    def validate_hole_position(cx, cy, panel_bounds):
        """
        Auto-repositions hole if it violates edge safety margins.
        """
        x_min, y_min, x_max, y_max = panel_bounds
        hole_radius = screw_diam / 2
        
        # Safe bonding box for hole center
        margin = MIN_EDGE + hole_radius
        
        # Enforce minimums (clamp)
        # Note: EDGE_OFFSET already sets a good target, this clamps manual deviations
        min_cx = x_min + margin
        max_cx = x_max - margin
        min_cy = y_min + margin
        max_cy = y_max - margin
        
        # If panel is too small, this might cross over. 
        # For this box size, we assume valid range exists.
        if min_cx > max_cx: min_cx = max_cx = (x_min + x_max)/2
        if min_cy > max_cy: min_cy = max_cy = (y_min + y_max)/2
        
        return max(min_cx, min(cx, max_cx)), max(min_cy, min(cy, max_cy))
    
    def add_screw_hole(cx, cy, panel_bounds=None):
        """Adds a 3.2mm clearance hole for M3 screw."""
        nonlocal screw_count
        if panel_bounds:
            cx, cy = validate_hole_position(cx, cy, panel_bounds)
        svg.add_circle(cx, cy, screw_diam/2, "CUT")
        screw_count += 1
        return cx, cy
        
    def draw_t_slot(edge_x, edge_y, direction, mode="CUT"):
        """
        Draws a T-Slot for an M3 nut.
        (edge_x, edge_y): Point on the component edge where screw enters.
        direction: 'UP', 'DOWN', 'LEFT', 'RIGHT' (Direction pointing INTO the material).
        """
        # Distances relative to edge
        # Screw Channel: diameter=screw_diam, length=nut_off - nut_h/2.
        # Nut Pocket: Width=nut_w, Height=nut_h (cross).
        # We draw the T Slot shape:
        #      +-------+
        #      |  Nut  |
        #      +--   --+
        #         | |
        #         | | Screw Channel
        #      ---   --- (Edge)
        
        dx, dy = 0, 0
        rot = 0
        if direction == 'UP': dy = -1; rot=90
        elif direction == 'DOWN': dy = 1; rot=-90
        elif direction == 'LEFT': dx = -1; rot=180
        elif direction == 'RIGHT': dx = 1; rot=0
        
        # Center of Nut
        cx = edge_x + dx * nut_off
        cy = edge_y + dy * nut_off
        
        # Draw Screw Channel (Rect width d, len nut_off)
        # We need to cut a slot from edge to nut.
        # If 'RIGHT': x goes edge -> nut. y is center.
        
        # Helper to transform local (u, v) to global (x, y)
        # u = along direction, v = perpendicular (right hand)
        def transform(u, v):
            if direction == 'RIGHT': return edge_x + u, edge_y + v
            if direction == 'LEFT': return edge_x - u, edge_y - v
            if direction == 'DOWN': return edge_x - v, edge_y + u
            if direction == 'UP': return edge_x + v, edge_y - u
            return edge_x, edge_y

        # Slot Points (Clockwise)
        # Start at Edge-Top of channel
        pts = []
        
        # Channel Width half
        cw = screw_diam / 2
        # Nut Width half (Perpendicular)
        nw = nut_w / 2
        # Nut Depth half (Along screw)
        nh = nut_h / 2
        
        dist_to_nut_front = nut_off - nh
        dist_to_nut_back = nut_off + nh
        
        # 1. Edge Top of Channel
        pts.append(transform(0, -cw))
        # 2. Nut Front Top
        pts.append(transform(dist_to_nut_front, -cw))
        # 3. Nut Side Top
        pts.append(transform(dist_to_nut_front, -nw))
        # 4. Nut Back Top
        pts.append(transform(dist_to_nut_back, -nw))
        # 5. Nut Back Bot
        pts.append(transform(dist_to_nut_back, nw))
        # 6. Nut Side Bot
        pts.append(transform(dist_to_nut_front, nw))
        # 7. Nut Front Bot
        pts.append(transform(dist_to_nut_front, cw))
        # 8. Edge Bot of Channel
        pts.append(transform(0, cw))
        
        # Draw closed polygon for T-slot (ensures proper cutting)
        nonlocal nut_count
        for i in range(len(pts)):
            next_i = (i + 1) % len(pts)
            svg.add_line(pts[i][0], pts[i][1], pts[next_i][0], pts[i][1], mode) # Fixed: pts[next_i][1]
            svg.add_line(pts[i][0], pts[i][1], pts[next_i][0], pts[next_i][1], mode)
        nut_count += 1


    # --- Draw Parts ---

    # 1. Base (W x D)
    bx, by = parts['Base']['x'], parts['Base']['y']
    bw, bh = parts['Base']['w'], parts['Base']['h'] # bw = W, bh = D
    
    # ... Draw fingers ...
    # Edge Logic for Base:
    # Base has Tabs (Parity 1) on all sides.
    # It mates with Bottom edges of walls.
    
    # Top (L->R): Mates with Back-Bottom (Slot/P-1). Base->Tab/P1.
    draw_finger_edge(bx, by, bx+bw, by, t, 1, "CUT")
    # Right (T->B): Mates with Right-Bottom (Slot/P-1). Base->Tab/P1.
    draw_finger_edge(bx+bw, by, bx+bw, by+bh, t, 1, "CUT")
    # Bottom (R->L): Mates with Front-Bottom (Slot/P-1). Base->Tab/P1.
    draw_finger_edge(bx+bw, by+bh, bx, by+bh, t, 1, "CUT")
    # Left (B->T): Mates with Left-Bottom (Slot/P-1). Base->Tab/P1.
    draw_finger_edge(bx, by+bh, bx, by, t, 1, "CUT")
    
    # Screws on Base: 2 holes per side (Symmetric Pattern)
    # This anchors the walls firmly without requiring vertical screws.
    if do_screws:
        base_bounds = (bx, by, bx + bw, by + bh)
        
        # Positions: 25% and 75% along each edge
        pos1 = 0.25
        pos2 = 0.75
        
        # Top Edge (Back Wall) - along W
        add_screw_hole(bx + W*pos1, by + EDGE_OFFSET_Y, base_bounds)
        add_screw_hole(bx + W*pos2, by + EDGE_OFFSET_Y, base_bounds)
        
        # Bottom Edge (Front Wall) - along W
        add_screw_hole(bx + W*pos1, by + D - EDGE_OFFSET_Y, base_bounds)
        add_screw_hole(bx + W*pos2, by + D - EDGE_OFFSET_Y, base_bounds)
        
        # Left Edge (Left Wall) - along D
        add_screw_hole(bx + EDGE_OFFSET_X, by + D*pos1, base_bounds)
        add_screw_hole(bx + EDGE_OFFSET_X, by + D*pos2, base_bounds)
        
        # Right Edge (Right Wall) - along D
        add_screw_hole(bx + W - EDGE_OFFSET_X, by + D*pos1, base_bounds)
        add_screw_hole(bx + W - EDGE_OFFSET_X, by + D*pos2, base_bounds)

    # Base panel text engraving (optional)
    if params.get('text_base'):
        text = params['text_base']
        cx = bx + bw/2
        cy = by + bh/2
        
        # Check if text contains separator (|)
        if '|' in text:
            # Split into two lines at the separator
            parts_text = [p.strip() for p in text.split('|')]
            if len(parts_text) == 2:
                # Two lines, same positioning as right wall text
                svg.add_text(cx, cy - 25, parts_text[0], font_size=8, mode="ENGRAVE")
                svg.add_text(cx, cy - 15, parts_text[1], font_size=8, mode="ENGRAVE")
            else:
                # Fallback to single line if more than 2 parts
                svg.add_text(cx, cy - 20, text, font_size=8, mode="ENGRAVE")
        else:
            # Single line text
            svg.add_text(cx, cy - 20, text, font_size=8, mode="ENGRAVE")

    # Edge Logic for Front/Back (Bottom):
    # Base fits INSIDE the walls.
    # Base has Tabs (Parity 1) on all sides.
    # Front/Back Bottom Edge must accept Base Tabs with compatible Slot pattern.
    # The Mating Zone corresponds to the center 'W' width. 
    # Corners (size t) are solid to cover the Left/Right wall edges.
    
    def draw_wall_bottom_with_base_slots(px, py, pw, ph):
        # Path: Start (Bottom Left) -> t (Corner) -> W (Mating Slots) -> t (Corner) -> End
        p_y_bot = py + ph
        # 1. Left Corner
        svg.add_line(px, p_y_bot, px+t, p_y_bot, "CUT")
        # 2. Mating Zone (Parity -1 to Rx Base Tabs)
        draw_finger_edge(px+t, p_y_bot, px+t+W, p_y_bot, t, -1, "CUT")
        # 3. Right Corner
        svg.add_line(px+t+W, p_y_bot, px+t+W+t, p_y_bot, "CUT")


    # 2. Front (W+2t x H)
    fx, fy = parts['Front']['x'], parts['Front']['y']
    fw, fh = parts['Front']['w'], parts['Front']['h'] # fw = W+2t, fh = H
    
    # ... Draw Front ...
    # Top: Flat
    svg.add_line(fx, fy, fx+fw, fy, "CUT")
    # Sides: Mating with Left/Right Walls.
    draw_finger_edge(fx+fw, fy, fx+fw, fy+fh, t, 1, "CUT") # Right Side (Down)
    draw_wall_bottom_with_base_slots(fx, fy, fw, fh)       # Bottom
    draw_finger_edge(fx, fy+fh, fx, fy, t, 1, "CUT")       # Left Side (Up)
    
    if do_screws:
        front_bounds = (fx, fy, fx + fw, fy + fh)
        
        # T-slots at Bottom (to receive Base Screws)
        # Positions based on Base Width (W)
        # Note: Front/Back width 'fw' corresponds to W
        draw_t_slot(fx + fw*0.25, fy + fh, 'UP')
        draw_t_slot(fx + fw*0.75, fy + fh, 'UP')


    # Divider Slot


    # 3. Back Wall
    bax, bay = parts['Back']['x'], parts['Back']['y']
    baw, bah = parts['Back']['w'], parts['Back']['h'] # baw = W+2t, bah = H
    
    svg.add_line(bax, bay, bax+baw, bay, "CUT") # Top
    draw_finger_edge(bax+baw, bay, bax+baw, bay+bah, t, 1, "CUT") # Right
    draw_wall_bottom_with_base_slots(bax, bay, baw, bah)          # Bottom
    draw_finger_edge(bax, bay+bah, bax, bay, t, 1, "CUT")         # Left
    
    if do_screws:
        back_bounds = (bax, bay, bax + baw, bay + bah)
        
        # T-slots at Bottom (to receive Base Screws)
        # T-slots at Bottom (to receive Base Screws)
        # Positions based on Base Width (W)
        # Note: Front/Back width 'fw' corresponds to W
        draw_t_slot(fx + fw*0.25, fy + fh, 'UP')
        draw_t_slot(fx + fw*0.75, fy + fh, 'UP')

    # Divider Slots (Applied to Front and Back)
    if 'divider_pos' in params:
        d_pos = params['divider_pos']
        slot_w = t
        slot_h = H / 2
        slot_y_rel = H / 4
        
        # Divider is placed along Width W.
        # Slots are on Front/Back walls.
        
        # Front Slot
        # Center of slot is at t + (W * d_pos). Warning: Front starts at x=0
        # Actually Front has width W+2t. Inner start is at t.
        # So x relative to left edge = t + (W * d_pos).
        fx_center = fx + t + (W * d_pos)
        svg.add_rect(fx_center - slot_w/2, fy + slot_y_rel, slot_w, slot_h, "CUT")
        
        # Back Slot
        bx_center = bax + t + (W * d_pos)
        svg.add_rect(bx_center - slot_w/2, bay + slot_y_rel, slot_w, slot_h, "CUT")

    # 4. Left Side Wall (D x H)
    lx, ly = parts['Left']['x'], parts['Left']['y']
    lw, lh = parts['Left']['w'], parts['Left']['h'] # lw = D, lh = H
    
    # ... Draw Left ...
    svg.add_line(lx, ly, lx+lw, ly, "CUT") # Top Flat
    draw_finger_edge(lx+lw, ly, lx+lw, ly+lh, t, -1, "CUT") # Right Side
    draw_finger_edge(lx+lw, ly+lh, lx, ly+lh, t, -1, "CUT") # Bot Side
    draw_finger_edge(lx, ly+lh, lx, ly, t, -1, "CUT")       # Left Side
    
    if do_screws:
        # Bottom Edge: Receives Base Screws. Direction UP
        # Base has holes at 25% and 75% of WIDTH here.
        draw_t_slot(lx + D*0.25, ly + lh, 'UP')
        draw_t_slot(lx + D*0.75, ly + lh, 'UP')
    
    # Fractal on Left Wall (Side without text/logo)
    if params.get('fractal'):
        # Center of Left Wall, moved down 10mm
        frac_cx = lx + lw/2
        frac_cy = ly + lh/2 + 10
        # Size: 60% of min dimension
        frac_size = min(lw, lh) * 0.6
        
        triangles = generate_sierpinski(frac_cx, frac_cy, frac_size, 4)
        for tri in triangles:
            svg.add_polyline(tri, "ENGRAVE")


    # 5. Right Side Wall
    rx, ry = parts['Right']['x'], parts['Right']['y']
    rw, rh = parts['Right']['w'], parts['Right']['h'] # rw = D, rh = H
    
    # ... Draw Right ...
    svg.add_line(rx, ry, rx+rw, ry, "CUT")
    draw_finger_edge(rx+rw, ry, rx+rw, ry+rh, t, -1, "CUT")
    draw_finger_edge(rx+rw, ry+rh, rx, ry+rh, t, -1, "CUT")
    draw_finger_edge(rx, ry+rh, rx, ry, t, -1, "CUT")
    
    if do_screws:
        # Bottom: Direction UP
        draw_t_slot(rx + D*0.25, ry + rh, 'UP')
        draw_t_slot(rx + D*0.75, ry + rh, 'UP')
        
    # Text and Logo on Right Wall (Side without Divider)
    if params.get('text_top'):
        text = params['text_top']
        # Center of Right Wall
        cx = rx + rw/2
        cy = ry + rh/2
        
        if text == "DIGITAL MANUFACTURING":
            # Split into two lines, moved up 10mm
            svg.add_text(cx, cy - 25, "DIGITAL", font_size=8, mode="ENGRAVE")
            svg.add_text(cx, cy - 15, "MANUFACTURING", font_size=8, mode="ENGRAVE")
        else:
            svg.add_text(cx, cy - 20, text, font_size=8, mode="ENGRAVE")
    
    # Columbia Logo on Right Wall
    shield_rel_path = "columbia_logo.svg"
    shield_full_path = os.path.join("logo", shield_rel_path)
    if os.path.exists(shield_full_path):
        try:
            with open(shield_full_path, "r") as IMG:
                # Read SVG content and replace the color to match ENGRAVE blue
                svg_content = IMG.read()
                # Replace the dark blue (#002d74) with blue (rgb(0,0,255)) to match text
                svg_content = svg_content.replace('#002d74', 'rgb(0,0,255)')
                shield_b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
                shield_href = f"data:image/svg+xml;base64,{shield_b64}"
                
                # Logo dimensions and positioning on Right Wall
                # Position below "DIGITAL MANUFACTURING" text
                # Text is at cy - 15.
                
                img_w = 80.0   # Doubled to 80mm per request
                img_h = 41.92  # Aspect ratio maintained (approx 1:0.524)
                
                img_x = rx + rw/2 - img_w/2
                img_y = ry + rh/2 - 5  # Moved up 10mm (was +5, now -5)
                
                svg.add_image(img_x, img_y, img_w, img_h, shield_href, "ENGRAVE")
        except Exception as e:
            print(f"Warning: Failed to embed image: {e}")
    


    # 6. Divider (if enabled)
    if 'Divider' in parts:
        dx, dy = parts['Divider']['x'], parts['Divider']['y']
        dw, dh = parts['Divider']['w'], parts['Divider']['h'] # Total W=D, H
        
        # Logic from generate_divider_svg (Tabbed)
        clearance = 0.5
        body_w = D - clearance # Divider width is D
        # To touch bottom (Base), Height should be H - t.
        # Originally was H - t - clearance.
        body_h = H - t
        
        tab_h = (H / 2) - clearance
        tab_w = t
        
        # Vertical Alignment: Divider Top flush with Wall Top
        slot_y_start_rel = (H - (H/2)) / 2 # H/4
        tab_y_start_rel = slot_y_start_rel + (clearance / 2)
        tab_y_end_rel = tab_y_start_rel + tab_h
        
        ox = dx + tab_w
        oy = dy
        
        # Points Logic (Clockwise from Top-Left of Body)
        # 1. Top Edge
        svg.add_line(ox, oy, ox + body_w, oy, "CUT")
        
        # 2. Right Side Upper
        svg.add_line(ox + body_w, oy, ox + body_w, oy + tab_y_start_rel, "CUT")
        
        # 3. Right Tab
        svg.add_line(ox + body_w, oy + tab_y_start_rel, ox + body_w + tab_w, oy + tab_y_start_rel, "CUT") # Out
        svg.add_line(ox + body_w + tab_w, oy + tab_y_start_rel, ox + body_w + tab_w, oy + tab_y_end_rel, "CUT") # Down
        svg.add_line(ox + body_w + tab_w, oy + tab_y_end_rel, ox + body_w, oy + tab_y_end_rel, "CUT") # Back
        
        # 4. Right Side Lower
        svg.add_line(ox + body_w, oy + tab_y_end_rel, ox + body_w, oy + body_h, "CUT")
        
        # 5. Bottom Edge
        svg.add_line(ox + body_w, oy + body_h, ox, oy + body_h, "CUT")
        
        # 6. Left Side Lower
        svg.add_line(ox, oy + body_h, ox, oy + tab_y_end_rel, "CUT")
        
        # 7. Left Tab
        svg.add_line(ox, oy + tab_y_end_rel, ox - tab_w, oy + tab_y_end_rel, "CUT") # Out (Left)
        svg.add_line(ox - tab_w, oy + tab_y_end_rel, ox - tab_w, oy + tab_y_start_rel, "CUT") # Up
        svg.add_line(ox - tab_w, oy + tab_y_start_rel, ox, oy + tab_y_start_rel, "CUT") # Back
        
        # 8. Left Side Upper
        svg.add_line(ox, oy + tab_y_start_rel, ox, oy, "CUT")

    # Lid Drawing Logic
    if 'Lid' in parts:
        lidx, lidy = parts['Lid']['x'], parts['Lid']['y']
        
        # Lid dimensions (Outer)
        # lid_w = W + 2t, lid_h = D + 2t
        lid_w = W + 2*t
        lid_d = D + 2*t
        
        # Main Lid Panel
        svg.add_rect(lidx, lidy, lid_w, lid_d, "CUT")
        
        # Inner Lip Logic
        # 4 Strips. Need to fit INSIDE the box walls.
        # Top/Bottom strips (along W). Left/Right strips (along D).
        
        clearance = 0.3
        lip_h = t
        
        # Draw the 4 lip pieces ABOVE the lid
        
        margin_lid = 5.0
        
        # Strip lengths
        len_w = W - clearance
        # Length of depth strips
        len_d_short = D - clearance - 2*t 
        
        # Position: Stacked above the lid
        # lidy is the Top of the Main Panel.
        # We start drawing strips above it.
        # Strip 1 (Bottom-most strip, closest to lid): lidy - margin - t
        
        curr_lip_y = lidy - margin_lid - t
        
        # 1. Width Strip 1
        svg.add_rect(lidx, curr_lip_y, len_w, t, "CUT")
        
        # 2. Width Strip 2
        curr_lip_y -= (t + margin_lid)
        svg.add_rect(lidx, curr_lip_y, len_w, t, "CUT")
        
        # 3. Depth Strip 1
        if len_d_short > 0:
            curr_lip_y -= (t + margin_lid)
            svg.add_rect(lidx, curr_lip_y, len_d_short, t, "CUT")
            
        # 4. Depth Strip 2
        if len_d_short > 0:
            curr_lip_y -= (t + margin_lid)
            svg.add_rect(lidx, curr_lip_y, len_d_short, t, "CUT")


    svg.save()
    
    # Print Bill of Materials (BOM) for screws
    if do_screws:
        recommended_screw_length = 12 + 2 * t
        print("\n" + "="*60)
        print("BILL OF MATERIALS (BOM) - M3 Fasteners")
        print("="*60)
        print(f"M3 Screws:              {screw_count} pcs")
        print(f"M3 Square Nuts:         {nut_count} pcs")
        print(f"Recommended Length:     {recommended_screw_length:.1f} mm")
        print(f"  (Formula: 12mm + 2×{t}mm material thickness)")
        print("="*60 + "\n")
    
    return True


# --- Wrapper & CLI ---

def print_software_description(params):
    """Prints the description of the software as required by rubric."""
    print("\n--- Software Description (Acrylic) ---")
    print("1. Calculation Steps:")
    print("   - Inputs: Box Width (W), Depth (D), Height (H), Material Thickness (t).")
    print("   - Design: 5-Part Finger Joint Box (Base, Front, Back, Left, Right).")
    if params.get('lid'):
        print("   - Lid: Removable friction-fit lid with inset lip.")
    print("   - Fingers: Calculated dynamically based on edge length (aiming for 10mm tabs).")
    print(f"   - Base Size: {params['W']} x {params['D']} (Tabs Out).")
    print(f"   - Front/Back Size: ({params['W']} + 2t) x {params['H']}. Covers corners.")
    print(f"   - Left/Right Size: {params['D']} x {params['H']}.")
    if params.get('lid'):
        print(f"   - Lid Size: ({params['W']}+2t) x ({params['D']}+2t) with 4 lip sides.")
        print(f"   - Lid Lip: Inner W = {params['W']}-0.3mm, Inner D = {params['D']}-0.3mm.")
    print("2. Conditions:")
    print(f"   - Thickness t ({params.get('t')}mm) used for finger depth.")
    print("   - Layout checked against stock.")
    print("3. Formulas:")
    print("   - Tab Depth = t")
    print("   - Tab Parity ensures A-fits-B (1 vs -1).")
    if params.get('lid'):
        print("   - Lid Lip: Inner dimensions = S - 0.3mm (clearance for friction fit).")
    print("----------------------------\n")

def get_float(prompt, default=None):
    try:
        prompt_str = f"{prompt} [{default}]: " if default is not None else f"{prompt}: "
        val = input(prompt_str)
        if not val and default is not None:
            return default
        return float(val)
    except ValueError:
        print("Invalid number.")
        return get_float(prompt, default)

def get_bool(prompt):
    val = input(f"{prompt} (y/n) [n]: ").lower()
    return val == 'y'

def validate_inputs(params):
    t = params['t']
    if t <= 0: return False, "Thickness must be positive."
    if params['W'] <= 0 or params['D'] <= 0 or params['H'] <= 0: return False, "Dimensions must be positive."
    limit = min(params['W'], params['D'], params['H']) / 2
    if t >= limit:
        return False, f"Thickness {t} is too large for smallest dimension."
    return True, ""

def main():
    print("=== Parametric Acrylic Box Generator ===")
    print("\n-- Acrylic Box Configuration --")
    params = {}
    params['stock_w'] = get_float("Stock Width (mm)", 600)
    params['stock_h'] = get_float("Stock Height (mm)", 600)
    params['t'] = get_float("Material Thickness t (mm)", 3.0)
    
    print("\n-- Dimensions --")
    S_default = 100.0
    params['W'] = get_float("Box Width (Front/Back) W (mm)", S_default)
    params['D'] = get_float("Box Depth (Left/Right) D (mm)", 100.0)
    params['H'] = get_float("Box Height H (mm)", S_default)
    
    print("\n-- Features --")
    # Default Divider to Yes
    do_div = input("Include Divider Insert? (y/n) [y]: ").lower() != 'n'
    if do_div:
        params['divider_pos'] = get_float("Divider Position Ratio (0.0-1.0, 0.5=Center)", 0.5)
        
    do_screws = input("Add M3 T-Slot Screw Reinforcement? (y/n) [n]: ").lower() == 'y'
    params['screws'] = do_screws
    
    do_fractal = input("Engrave Fractal on Side Wall? (y/n) [y]: ").lower() != 'n'
    params['fractal'] = do_fractal
    
    # Lid option (default to yes)
    do_lid = input("Include Removable Lid? (y/n) [y]: ").lower() != 'n'
    params['lid'] = do_lid
    
    print("\n-- Engraving --")
    # Default Base Text
    default_base_text = "DIGITAL MANUFACTURING"
    t_top = input(f"Text on Base [{default_base_text}]: ")
    params['text_top'] = t_top if t_top else default_base_text
    
    # Base panel text (new option)
    default_base_text_bottom = "LORENZO | DIANE"
    t_base = input(f"Text on Bottom (Base Panel) [{default_base_text_bottom}]: ")
    params['text_base'] = t_base if t_base else default_base_text_bottom
    
    # Disable Front Text prompt (keep clean)
    params['text_front'] = ""
    
    # Logo option (default to yes)
    do_logo = input("Engrave Columbia Logo (Front Wall)? (y/n) [y]: ").lower() != 'n'
    params['include_logo'] = do_logo
    # params['include_fractal'] logic handled previously
    
    # Validation
    valid, msg = validate_inputs(params)
    if not valid:
        print(f"\nError: {msg}")
        return
        
    # Execution
    print("\nGenerating files base on Acrylic Finger Joints...")
    
    # Reuse 'box_main.svg' filename or specific
    success = generate_box_svg(params, "box_acrylic_parts.svg")
    
    if success:
        print_software_description(params)

if __name__ == "__main__":
    main()
