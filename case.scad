$fn = 64;
$fs = 0.5;

// the case consists of two parts: box + shelf
// - the box includes mounting points for the arduino and switch. it slots onto the shelf but can be removed.
// - the shelf is fastened to the wall and supports the box.
//
// the two part designs simplifies installation and removing the arduino portion as needed for re-flashing, etc
//
// this file handles both parts of the case via a flag (part)
// part == 0 -> for development, render both with the shelf grayed out
// part == 1 -> render the box only
// part == 2 -> render the shelf only after flipping it for ease of printing
//
// a batch script automatically runs the part == 1/2 conditions to export stl files
//
// all dimensions are in mm
//
// notes
// 1) some cutouts are intentionally oversized so that they render properly with CGAL (quick preview)
//    they do not impact the output geometry at all
//
// 2) there is an adjustable parameter (epsInterference) that can increased to make the two pieces fit more loosely

// small offset to reduce interference as needed
epsInterference = 0.2;

// overall case dimensions
w_case = 100;
l_case = 120;
t_case = 40;

// xy offset and diameter of circular cutout for switch
x_switchMount = 80;
y_switchMount= 50;
d_switchMount = 12 + epsInterference; // 12.2 is good for me

// xy offset of board mount from case corner
x_boardMount = 12;
y_boardMount = 35;

// board mount details
d_boardSpacer = 8;
t_boardSpacer = 3 + 4; // added 4 here and removed holes from the base, ideally add washers
d_boardScrew = 3;

// board mount hole spacing
w_boardMounts = 44.6;
l_boardMounts = 66.5;

// cavity parameters
t_caseBase = 4; // thickness of base 
t_caseWall = 4; // thickness of lateral walls
t_caseHalfWall = 13; // height of half wall to stabilize but not block micro usb

// dimensions of wall mount
t_wallMountLedge = 4;
w_wallMountLedge = 10;
d_wallMounts = 4; // diameter of mounting hole

// slot dimensions
x_slotInset = 20;
w_slot = 4;
w_slotGrip = 3*w_slot;
t_slot = t_case/2;

// render
part = 0;
if (part == 1) {
    box();
} else if (part == 2) {
    mirror([0,0,1])
        wallMount();
} else {
    box();
    %wallMount();
}

// box to hold the arduino and switch
module box() {
    union() {
        difference() {
            
            // case cube 
            roundedcube([w_case, l_case, t_case]);
            
            // switch labels
            translate([x_switchMount - d_switchMount, y_switchMount + d_switchMount, -0.5])
                mirror([1,0,0])
                    linear_extrude(height = 1)
                        text("on", size = 4, font="Helvetica:style=Bold");
            translate([x_switchMount - d_switchMount, y_switchMount, -0.5])
                mirror([1,0,0])
                    linear_extrude(height = 1)
                        text("purple air", size = 4, font="Helvetica:style=Bold");
            translate([x_switchMount - d_switchMount, y_switchMount - d_switchMount, -0.5])
                mirror([1,0,0])
                    linear_extrude(height = 1)
                        text("off", size = 4, font="Helvetica:style=Bold");
                
            // cavity
            translate([t_caseWall, t_caseWall, t_caseBase])
                roundedcube([w_case - 2*t_caseWall, l_case - 2*t_caseWall, t_case]);
            
            // half wall for wires
            translate([t_caseWall, 2*t_caseWall, t_caseBase + t_caseHalfWall])
                cube([w_case - 2*t_caseWall, l_case, t_case-t_caseHalfWall]);
            
            // switch mount
            translate([x_switchMount, y_switchMount, -t_case/2])
                cylinder(h = t_case, d = d_switchMount);
            
            // half thickness slots
            for (dx = [0, w_case-2*x_slotInset]) {
                translate([dx + x_slotInset, -t_caseWall, t_case - t_slot])
                    cube([w_slot, 3*t_caseWall, 2*t_slot]);
            }
        }
        
        // build up board standoffs
        for (dx = [0:1]) {
            for (dy = [0:1]) {
                translate([x_boardMount + dx*w_boardMounts, y_boardMount + dy*l_boardMounts, t_caseBase])
                    difference() {
                        cylinder(h = t_boardSpacer, d = d_boardSpacer);
                        cylinder(h = 2*t_boardSpacer, d = d_boardScrew);
                    }
            }
        }
    }
}

// stationary portion that mounts to the wall or other surface
module wallMount() {
    difference() {
        union() {
            // full thickness ledge
            translate([0, -t_caseWall, 0])
                roundedcube([w_case, t_caseWall, t_case]);
            
            // thin wall mount
            translate([0, -w_wallMountLedge-t_caseWall, t_case - t_wallMountLedge])
                roundedcube([w_case, t_caseWall + w_wallMountLedge, t_wallMountLedge]);
            
            // half thickness slot
            for (dx = [0, w_case-2*x_slotInset]) {
                // slot
                translate([dx + x_slotInset + epsInterference, 0, t_case - t_slot + epsInterference])
                    cube([w_slot - 2*epsInterference, t_caseWall + 2*epsInterference, t_slot - epsInterference]);
                
                // grip (rounded)
                translate([dx + x_slotInset + epsInterference + w_slot/2 - w_slotGrip/2 - epsInterference, t_caseWall + 2*epsInterference, t_case - t_slot + epsInterference])
                    roundedcube([w_slotGrip, t_caseWall + 2*epsInterference, t_slot - epsInterference]);
            }
        }
        
        // screw holes
        for (dx = [0, w_case-w_wallMountLedge]) {
            translate([dx+w_wallMountLedge/2, -t_caseWall-w_wallMountLedge/2, 0])
                cylinder(h = 2*t_case, d = d_wallMounts);
        }    
    }
}


module roundedcube(size = [1, 1, 1], center = false, radius = 1, apply_to = "z") {
	// If single value, convert to [x, y, z] vector
	size = (size[0] == undef) ? [size, size, size] : size;

	translate_min = radius;
	translate_xmax = size[0] - radius;
	translate_ymax = size[1] - radius;
	translate_zmax = size[2] - radius;

	diameter = radius * 2;

	obj_translate = (center == false) ?
		[0, 0, 0] : [
			-(size[0] / 2),
			-(size[1] / 2),
			-(size[2] / 2)
		];

	translate(v = obj_translate) {
		hull() {
			for (translate_x = [translate_min, translate_xmax]) {
				x_at = (translate_x == translate_min) ? "min" : "max";
				for (translate_y = [translate_min, translate_ymax]) {
					y_at = (translate_y == translate_min) ? "min" : "max";
					for (translate_z = [translate_min, translate_zmax]) {
						z_at = (translate_z == translate_min) ? "min" : "max";

						translate(v = [translate_x, translate_y, translate_z])
						if (
							(apply_to == "all") ||
							(apply_to == "xmin" && x_at == "min") || (apply_to == "xmax" && x_at == "max") ||
							(apply_to == "ymin" && y_at == "min") || (apply_to == "ymax" && y_at == "max") ||
							(apply_to == "zmin" && z_at == "min") || (apply_to == "zmax" && z_at == "max")
						) {
							sphere(r = radius);
						} else {
							rotate = 
								(apply_to == "xmin" || apply_to == "xmax" || apply_to == "x") ? [0, 90, 0] : (
								(apply_to == "ymin" || apply_to == "ymax" || apply_to == "y") ? [90, 90, 0] :
								[0, 0, 0]
							);
							rotate(a = rotate)
							cylinder(h = diameter, r = radius, center = true);
						}
					}
				}
			}
		}
	}
}