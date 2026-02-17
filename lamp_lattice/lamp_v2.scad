// Lampshade V2 Parameters
light_base_dia = 37.4;
light_top_dia = 36.2;
light_height = 18;

wall_thickness = 2;

// Derived Dimensions
neck_inner_r_base = light_base_dia / 2;
neck_inner_r_top = light_top_dia / 2;

// Body Parameters
total_height = 120; // Slightly taller for twisting effect
base_radius = 65;
top_radius = neck_inner_r_top + wall_thickness; 

// Twist Parameters
twist_angle = 120;
slices = 200; // Resolution along Z for twist

// Lattice Parameters
triangle_size = 6;      // Fixed size
min_distance = 5;       // Minimum distance between triangles
// Cell size roughly: triangle height (~9) + spacing (5) + margin
// Tri 6mm radius -> side 10.4 -> height 9.
// 9 + 5 = 14. Let's use 16mm vertical spacing and similar arc length.
cell_height = 16;       
jitter_amount = 2;      // Random offset max

seed = 42;

$fn = 100;

// Function for radius at height z (Linear taper for now, but twisted by geometry)
function radius_at_z(z) = base_radius - (base_radius - top_radius) * (z / total_height);

module undulating_body() {
    linear_extrude(height = total_height, twist = twist_angle, scale = top_radius / base_radius, slices = slices)
    translate([0,0,0])
    circle(r = base_radius, $fn = 6); // Hexagon base twisted becomes undulating
}

module hollow_body() {
    difference() {
        union() {
            undulating_body();
            // Solid circular collar for light fitting stability
            translate([0, 0, total_height - light_height])
            cylinder(h = light_height, r = top_radius);
        }
        
        // Hollow out inside following the same twist roughly, or just conical?
        // A simple conical hole is safe and easy for the bulb.
        // But to maintain wall thickness, we should probably scale the inner one too.
        
        translate([0,0,-1])
        linear_extrude(height = total_height + 2, twist = twist_angle, scale = (top_radius - wall_thickness) / (base_radius - wall_thickness), slices = slices)
        circle(r = base_radius - wall_thickness, $fn = 6);
        
        // Ensure the light fitting fits perfectly at the top
        // This cuts a precise cylinder/cone for the socket at the top
        translate([0, 0, total_height - light_height])
        cylinder(h = light_height + 1, r1 = neck_inner_r_base, r2 = neck_inner_r_top);
        
        // And clear the path below it for the bulb
        translate([0, 0, -1])
        cylinder(h = total_height, r = neck_inner_r_base);
    }
}

module random_lattice() {
    // Jittered Grid Approach to guarantee spacing
    
    // Calculate number of rows
    // Start a bit up, end near the very top
    z_start = 10;
    z_end = total_height - 5;
    
    num_rows = floor((z_end - z_start) / cell_height);
    
    for (row = [0 : num_rows]) {
        base_z = z_start + row * cell_height;
        
        // Calculate radius and circumference at this height
        r = radius_at_z(base_z);
        circ = 2 * PI * r;
        
        // Calculate columns for this row to maintain cell width ~ cell_height
        num_cols = floor(circ / cell_height);
        ang_step = 360 / num_cols;
        
        // Pseudo-random offset for this row to break vertical alignment
        row_offset = rands(0, 360, 1, seed + row)[0];
        
        for (col = [0 : num_cols - 1]) {
            // Base angle
            base_angle = col * ang_step + row_offset;
            
            // Jitter
            // We use standard rands. To keep it deterministic per cell, seed logic:
            s_cell = seed + row * 100 + col;
            j_z = rands(-jitter_amount, jitter_amount, 1, s_cell)[0];
            j_a = rands(-jitter_amount, jitter_amount, 1, s_cell + 1)[0] / r * 180 / PI; // Approx angle jitter
            
            final_z = base_z + j_z;
            final_a = base_angle + j_a;
            
            // Ensure z is within bounds
            if (final_z > 5 && final_z < total_height - light_height - 5) {
                r_at_z = radius_at_z(final_z);
                
                translate([0, 0, final_z])
                rotate([0, 0, final_a])
                translate([r_at_z, 0, 0])
                // Rotate to match general slope
                rotate([0, atan((base_radius - top_radius)/total_height), 0])
                rotate([0, 90, 0])
                rotate([0,0, rands(0,360,1, s_cell+2)[0]]) // Random rotation of triangle
                cylinder(r = triangle_size, h = wall_thickness * 10, $fn=3, center=true);
            }
        }
    }
}

module base_plate() {
    // Hexagonal base plate to match twisted body bottom?
    // Or circular. User said "circle to the base" in V1.
    // But V1 body was conical. V2 body is twisted hexagon (= undulating).
    // Let's make a base plate that fits the bottom shape.
    linear_extrude(height = wall_thickness)
    circle(r = base_radius, $fn = 6);
}

// Main Assembly
color("green") {
    difference() {
        hollow_body();
        random_lattice();
    }
    base_plate();
}
