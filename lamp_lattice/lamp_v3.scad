// One Thousand Museum Inspired Lamp Generator
// Provides an exoskeleton structure mimicking Zaha Hadid's Miami tower

/* [Render Options] */
// Which part to render: 0=All (Assembly), 1=Base Core, 2=Exoskeleton Shell, 3=Diffuser
part_to_render = 0; 

/* [Form Profile] */
total_height = 280;
base_diameter = 140;
waist_diameter = 85; 
top_diameter = 110;
waist_height = 80;

/* [Exoskeleton Columns] */
main_column_count = 4;
main_column_width = 32;
main_column_depth = 22;

diag_count = 4;
diag_width = 16;
diag_depth = 14;
diag_twist = 135; // Total degrees of twist for diagonals

/* [Base Arches] */
arch_width = 30;  // Base radius size for the parabolic arch width
arch_depth = 28;  // How deep the arch cuts inwards

/* [Electrical Integration] */
light_source = 1; // 1 = LED Puck, 2 = E26 Socket
led_cavity_diameter = 70;
led_cavity_depth = 25; 
e26_cavity_diameter = 40;
e26_cavity_depth = 55;
cable_channel_diameter = 8;
base_core_height = 60; // How tall the inner solid base is

/* [Tolerances] */
shell_thickness = 4;
diffuser_thickness = 1.6;
tolerance = 0.5; // 3D printing clearance
$fn = 100;

// --- Derived Variables ---
h1 = waist_height;
h2 = total_height - waist_height;
s1 = waist_diameter / base_diameter;
s2 = top_diameter / waist_diameter;
t1 = diag_twist * (h1 / total_height);
t2 = diag_twist * (h2 / total_height);

light_dia = light_source == 1 ? led_cavity_diameter : e26_cavity_diameter;
light_depth = light_source == 1 ? led_cavity_depth : e26_cavity_depth;
base_core_dia = base_diameter - main_column_depth*1.5 - tolerance*4;


// --- 2D Profiles ---

module main_columns_2d(d) {
    for(i=[0:main_column_count-1]) {
        rotate([0, 0, i * (360/main_column_count)])
        translate([(d - main_column_depth)/2, 0, 0])
        scale([main_column_depth/main_column_width, 1])
        circle(d=main_column_width);
    }
}

module diag_ribs_2d(d) {
    for(i=[0:diag_count-1]) {
        // Offset so they cross perfectly
        rotate([0, 0, i * (360/diag_count) + (180/diag_count)])
        translate([(d - diag_depth)/2, 0, 0])
        scale([diag_depth/diag_width, 1])
        circle(d=diag_width);
    }
}

// --- 3D Architecture ---

module shell_exoskeleton() {
    base_d = base_diameter;
    // Lower Section (Base to Waist)
    union() {
        linear_extrude(height=h1, twist=0, scale=s1, slices=100)
            main_columns_2d(base_d);
            
        linear_extrude(height=h1, twist=t1, scale=s1, slices=100)
            diag_ribs_2d(base_d);
            
        linear_extrude(height=h1, twist=-t1, scale=s1, slices=100)
            diag_ribs_2d(base_d);
            
        // Inner skirt to bind them all at the bottom
        cylinder(d=base_core_dia + 8, h=base_core_height);
    }
    
    // Upper Section (Waist to Top)
    translate([0,0,h1])
    union() {
        linear_extrude(height=h2, twist=0, scale=s2, slices=150)
            scale([s1, s1])
            main_columns_2d(base_d);
            
        linear_extrude(height=h2, twist=t2, scale=s2, slices=150)
            rotate([0, 0, -t1])
            scale([s1, s1])
            diag_ribs_2d(base_d);
            
        linear_extrude(height=h2, twist=-t2, scale=s2, slices=150)
            rotate([0, 0, t1]) 
            scale([s1, s1])
            diag_ribs_2d(base_d);
    }
    
    // Top binding ring
    translate([0, 0, total_height - 5])
    linear_extrude(height=5)
        circle(d=top_diameter - 2);
}

module arch_cutout() {
    // Elegant parabolic cutouts for the base entrances
    translate([0, base_diameter/2, 0])
    scale([arch_width, arch_depth, waist_height * 1.05])
    sphere(r=1, $fn=80);
    
    // Bottom straight passthrough to desk
    translate([0, base_diameter/2, -50])
    scale([arch_width, arch_depth, 1])
    cylinder(r=1, h=50, $fn=80);
}

module all_arches() {
    for(i=[0:main_column_count-1]) {
        rotate([0, 0, i * (360/main_column_count) + (180/main_column_count)])
        arch_cutout();
    }
}

module diffuser_hollow(clearance=0) {
    inner_base_d = base_core_dia + clearance*2 + 2; // +2 so it overlaps exoskeleton slightly
    
    linear_extrude(height=h1+0.1, scale=s1, slices=100)
        circle(d=inner_base_d);
        
    translate([0, 0, h1])
    linear_extrude(height=h2+0.1, scale=s2, slices=150)
        scale([s1, s1])
        circle(d=inner_base_d);
}

// --- Printable Parts ---

module shell_part() {
    difference() {
        shell_exoskeleton();
        
        // Sculpt the arches
        all_arches();
        
        // Carve out center completely
        translate([0, 0, -1])
        diffuser_hollow(clearance = tolerance);
        
        // Socket for the base core
        translate([0, 0, -1])
        cylinder(d=base_core_dia + tolerance*2, h=base_core_height + 1);
        
        // Base alignment notch
        translate([0, base_core_dia/2, base_core_height - 5])
        cube([6, 12, 12], center=true);
    }
}

module diffuser_print_part() {
    difference() {
        union() {
            difference() {
                diffuser_hollow(clearance=0);
                translate([0, 0, -1])
                diffuser_hollow(clearance= -diffuser_thickness);
            }
        }
        // Slice off the bottom so it rests right on top of the base core
        translate([0, 0, -50])
        cylinder(d=base_diameter*2, h=50 + base_core_height);
    }
}

module base_part() {
    difference() {
        union() {
            cylinder(d=base_core_dia, h=base_core_height);
            
            // Alignment notch
            translate([0, base_core_dia/2, base_core_height - 5])
            cube([6 - tolerance*2, 10, 10], center=true);
        }
        
        // Make sure arches don't touch the outer bounds of base
        all_arches();
        
        // Light source
        translate([0, 0, base_core_height - light_depth])
        cylinder(d=light_dia, h=light_depth + 1);
        
        // Central cable logic
        cylinder(d=cable_channel_diameter, h=base_core_height);
        translate([0, -base_core_dia/2, 6])
        rotate([90, 0, 0])
        cylinder(d=cable_channel_diameter, h=base_core_dia);
        
        // Hollow weight/saving space
        translate([0, 0, -1])
        difference() {
            cylinder(d=base_core_dia - 20, h=base_core_height - 20);
            cylinder(d=cable_channel_diameter + 15, h=base_core_height);
        }
    }
}

// --- Render Setup ---

if (part_to_render == 0) {
    color("#FAFAFA") shell_part();
    color("#444444") base_part();
    color("#FFFFFF88") diffuser_print_part();
} else if (part_to_render == 1) {
    base_part();
} else if (part_to_render == 2) {
    shell_part();
} else if (part_to_render == 3) {
    diffuser_print_part();
}
