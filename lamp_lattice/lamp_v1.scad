// Lampshade Parameters
light_base_dia = 37.4;
light_top_dia = 36.2;
light_height = 18;

wall_thickness = 2;
neck_height = light_height;

// Derived Dimensions
top_radius = (light_base_dia / 2) + wall_thickness; // Outer radius of neck
bottom_radius = 65; // Base radius
total_height = 100;

lattice_rows = 5;
lattice_cols = 12;  // Reduced columns to prevent overlap at top
triangle_size = 6;  // Smaller size to prevent corners touching

// Calculate cone height and angle
cone_height = total_height - neck_height;
cone_angle = atan((bottom_radius - top_radius) / cone_height);

$fn = 100; // Resolution

module lamp_body() {
    union() {
        // Neck (Cylinder)
        translate([0, 0, cone_height])
        difference() {
            cylinder(h = neck_height, r = top_radius);
            translate([0, 0, -1])
            cylinder(h = neck_height + 2, r1 = light_base_dia / 2, r2 = light_top_dia / 2);
        }
        
        // Body (Cone)
        difference() {
            cylinder(h = cone_height, r1 = bottom_radius, r2 = top_radius);
            translate([0, 0, -1])
            cylinder(h = cone_height + 2, r1 = bottom_radius - wall_thickness, r2 = top_radius - wall_thickness);
        }
    }
}

module triangle_cutter() {
    // Triangle shape using 3-sided cylinder
    rotate([0, 90, 0]) // Orient for cutting through wall (Z becomes Radial)
    rotate([0, 0, 180]) // Rotate to point up (Vertex at +Z in lamp frame)
    cylinder(r = triangle_size, h = wall_thickness * 10, $fn=3, center = true);
}

module lattice_pattern() {
    for (row = [0 : lattice_rows - 1]) {
        // Calculate height for this row
        // Interpolate from bottom to just below the neck
        h_frac = (row + 0.5) / lattice_rows;
        z_pos = h_frac * cone_height;
        
        // Calculate radius at this height
        current_r = bottom_radius - (bottom_radius - top_radius) * h_frac;
        
        // No offset for simple grid, or keep offset for honeycomb
        // User didn't specify layout, just shape. Honeycomb usually better for lattice.
        rot_offset = (row % 2) * (360 / lattice_cols / 2);
        
        for (col = [0 : lattice_cols - 1]) {
            angle = col * (360 / lattice_cols) + rot_offset;
            
            translate([0, 0, z_pos])
            rotate([0, 0, angle])
            translate([current_r, 0, 0])
            rotate([0, cone_angle, 0]) // Tilt to match cone surface
            triangle_cutter();
        }
    }
}

module star(n, r_outer, r_inner, h) {
    points = [ for (i = [0 : 2 * n - 1]) let (r = (i % 2 == 0) ? r_outer : r_inner, a = i * 180 / n) [r * cos(a), r * sin(a)] ];
    linear_extrude(height = h, center = true) polygon(points);
}

module base_plate() {
    difference() {
        cylinder(r = bottom_radius, h = wall_thickness);
        translate([0,0, wall_thickness/2]) star(5, 15, 7, wall_thickness + 2);
    }
}

// Main Assembly
color("green") {
    difference() {
        lamp_body();
        lattice_pattern();
    }
    base_plate();
}
