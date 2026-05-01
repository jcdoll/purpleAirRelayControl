// Minimal wall-mount plate for Feather + Power Relay FeatherWing + sCharge S39
//
// Single flat backplate, command-strip mounted. Components mount from the front:
//   - Feather stack: 4 printed posts (22 mm) with M2 brass heat-set inserts
//   - sCharge S39 brick: 2 raised bosses with M3 brass heat-set inserts
//
// Hardware:
//   - Feather:  M2 screws + CNC Kitchen M2 x 3 inserts (3.3 mm OD, 4.0 mm depth)
//   - sCharge:  M3 screws + CNC Kitchen M3 x 3 inserts (4.0 mm OD, 4.0 mm depth)
//
// Print face-down (flat back on bed). No supports.
//
// All dimensions in mm.

$fn = 64;

// ----- adjustable parameters -----

// plate
plate_t        = 3;    // backplate thickness
plate_corner_r = 4;    // rounded corners

// Feather hole pattern (standard 0.9" x 2.0" Feather)
// holes are 0.1" inset from each edge -> 0.7" x 1.8" center-to-center
feather_hole_dx = 17.78;  // 0.7"
feather_hole_dy = 45.72;  // 1.8"

// posts that hold the Feather stack -- M2 brass insert at the top
post_h          = 22;    // matches full stack depth (Feather + relay FeatherWing)
post_od         = 6;
post_insert_od    = 3.4;   // CNC Kitchen M2 x 3 (bag: 3.3 mm) + 0.1 fudge
post_insert_depth = 4.0;

// sCharge S39 (ACDC-245C): 46 x 32 x 18 mm body, eyelets extend the long axis
scharge_screw_spacing = 52;   // center-to-center between the two eyelet slots
scharge_body_w        = 32;   // short axis (across the eyelets)

// boss under each sCharge eyelet -- M3 brass insert at the top
boss_od           = 9;
boss_h            = 5;     // 4 mm pocket + 1 mm of plastic backing below it
boss_insert_od    = 4.1;   // CNC Kitchen M3 x 3 (bag: 4.0 mm) + 0.1 fudge
boss_insert_depth = 4.0;

// component spacing on the plate
edge_margin = 6;       // margin from any component to plate edge
gap         = 8;       // gap between Feather stack and sCharge

// ----- derived layout -----
// Feather long axis runs in y; sCharge long axis runs in y, to the right of it
feather_x = edge_margin + 22.86/2;                                // Feather pcb is 22.86 wide
scharge_x = feather_x + 22.86/2 + gap + scharge_body_w/2;
plate_w   = scharge_x + scharge_body_w/2 + edge_margin;

plate_h   = max(50.80, scharge_screw_spacing + 2*boss_od/2) + 2*edge_margin;
feather_y = plate_h / 2;
scharge_y = plate_h / 2;

// ----- render -----

plate();

module plate() {
    union() {
        rounded_plate();
        feather_posts();
        scharge_bosses();
    }
}

module rounded_plate() {
    linear_extrude(height = plate_t)
        offset(r = plate_corner_r)
            offset(r = -plate_corner_r)
                square([plate_w, plate_h]);
}

module feather_posts() {
    for (sx = [-1, 1])
        for (sy = [-1, 1])
            translate([feather_x + sx * feather_hole_dx/2,
                       feather_y + sy * feather_hole_dy/2,
                       plate_t])
                post();
}

module post() {
    difference() {
        cylinder(h = post_h, d = post_od);
        translate([0, 0, post_h - post_insert_depth])
            cylinder(h = post_insert_depth + 0.1, d = post_insert_od);
    }
}

module scharge_bosses() {
    for (sy = [-1, 1])
        translate([scharge_x, scharge_y + sy * scharge_screw_spacing/2, plate_t])
            difference() {
                cylinder(h = boss_h, d = boss_od);
                translate([0, 0, boss_h - boss_insert_depth])
                    cylinder(h = boss_insert_depth + 0.1, d = boss_insert_od);
            }
}
