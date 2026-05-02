// Minimal wall-mount plate for Feather + Power Relay FeatherWing + sCharge S39
//
// Layout: Feather at top (long axis horizontal), sCharge at bottom. Only two
// screw posts on the LEFT end of the Feather. The right end is unsupported --
// the relay body on the FeatherWing rests against the plate at that end.
//
//                     ___________________________________
//                    |   [SCREW]                         |
//                    |             Feather PCB           |   <- Feather
//                    |   [SCREW]                         |
//                    |                                   |
//                    |    o   sCharge S39 brick   o      |   <- sCharge
//                    |___________________________________|
//
//   Feather posts (2, screw-only, at -x end):
//     6 mm OD post with M2 brass heat-set insert at the top. M2 screws through
//     the Feather (and optionally the wing) clamp the assembly. Orient the
//     Feather so its LiPo / buttons short edge is at -x (the screw end).
//   sCharge bosses: 2 raised bosses 54 mm apart (along plate X) with M3 brass
//     inserts. Screws pass through the eyelet slots into the bosses.
//
// Hardware:
//   - Feather:  2x M2 screws + CNC Kitchen M2 x 3 inserts (3.3 mm hole, 4.0 deep)
//   - sCharge:  M3 screws + CNC Kitchen M3 x 3 inserts (4.0 mm hole, 4.0 deep)
//
// Print face-down (flat back on bed). No supports.
//
// All dimensions in mm.

$fn = 64;

// ----- adjustable parameters -----

// plate
plate_t        = 3;    // backplate thickness
plate_corner_r = 4;    // rounded corners

// Feather PCB and corner hole pattern (standard 0.9" x 2.0" Feather, 0.1"
// inset corner holes -> 1.8" long-axis spacing, 0.7" short-axis spacing)
feather_pcb_long  = 50.80;
feather_pcb_short = 22.86;
feather_hole_long  = 45.72;   // long-axis spacing (now along plate X)
feather_hole_short = 17.78;   // short-axis spacing (now along plate Y)

// Screw posts at -x end (spacious LiPo / buttons end of the Feather).
// Height chosen so the wing's relay body rests on the plate at the +x end
// (the right end of the Feather is unsupported by the plate).
post_h                  = 18.5;
post_screw_od           = 6;
post_screw_insert_od    = 3.4;   // CNC Kitchen M2 x 3 (bag: 3.3 mm) + 0.1 fudge
post_screw_insert_depth = 4.0;

// sCharge S39 (ACDC-245C): 46 x 32 x 18 mm body, eyelets extend the long axis
scharge_screw_spacing = 54;   // center-to-center along the brick's long axis (plate X)
scharge_body_short    = 32;   // short axis (across the eyelets)

// boss under each sCharge eyelet -- M3 brass insert at the top
boss_od           = 9;
boss_h            = 5;     // 4 mm pocket + 1 mm of plastic backing below it
boss_insert_od    = 4.1;   // CNC Kitchen M3 x 3 (bag: 4.0 mm) + 0.1 fudge
boss_insert_depth = 4.0;

// component spacing on the plate
edge_margin = 6;       // margin from any component to plate edge
gap         = 8;       // gap between Feather row and sCharge row

// ----- derived layout -----
// Plate width fits the wider of (Feather long axis, sCharge eyelet span + boss)
plate_w = max(feather_pcb_long, scharge_screw_spacing + boss_od) + 2*edge_margin;
plate_h = feather_pcb_short + gap + scharge_body_short + 2*edge_margin;

// Feather centered horizontally, near the top of the plate
feather_x = plate_w / 2;
feather_y = plate_h - edge_margin - feather_pcb_short/2;

// sCharge centered horizontally, near the bottom of the plate
scharge_x = plate_w / 2;
scharge_y = edge_margin + scharge_body_short/2;

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
    for (sy = [-1, 1])
        translate([feather_x - feather_hole_long/2,
                   feather_y + sy * feather_hole_short/2,
                   plate_t])
            screw_post();
}

module screw_post() {
    difference() {
        cylinder(h = post_h, d = post_screw_od);
        translate([0, 0, post_h - post_screw_insert_depth])
            cylinder(h = post_screw_insert_depth + 0.1, d = post_screw_insert_od);
    }
}

module scharge_bosses() {
    for (sx = [-1, 1])
        translate([scharge_x + sx * scharge_screw_spacing/2, scharge_y, plate_t])
            difference() {
                cylinder(h = boss_h, d = boss_od);
                translate([0, 0, boss_h - boss_insert_depth])
                    cylinder(h = boss_insert_depth + 0.1, d = boss_insert_od);
            }
}
