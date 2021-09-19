$fn = 32;
$fs = 0.5;

// overall case dimensions
w_case = 100;
l_case = 120;
t_case = 35;

// xy offset and diameter of circular cutout for switch
x_switchMount = 80;
y_switchMount= 60;
d_switchMount = 12.2;

// xy offset of board mount from case corner
x_boardMount = 12;
y_boardMount = 30;

// board mount details
d_boardSpacer = 8;
t_boardSpacer = 3;
d_boardScrew = 3;

// board mount hole spacing
w_boardMounts = 44.6;
l_boardMounts = 66.5;

// cavity parameters
t_caseBase = 4; // thickness of base 
t_caseWall = 4; // thickness of lateral walls
t_caseHalfWall = 13; // height of half wall to stabilize but not block micro usb

// dimensions of wall mount
t_wallMountLedge = 10;
w_wallMountLedge = 15;
d_wallMounts = 4; // diameter of mounting hole

// case with switch mount, board mounts, and wall mount holes
union() {
    difference() {
        
        // case cube 
        cube([w_case, l_case, t_case]);
        
        // switch labels
        translate([x_switchMount - d_switchMount, y_switchMount + d_switchMount, -0.5])
            mirror([1,0,0])
                linear_extrude(height = 1)
                    text("on", size = 4);
        translate([x_switchMount - d_switchMount, y_switchMount, -0.5])
            mirror([1,0,0])
                linear_extrude(height = 1)
                    text("purple air", size = 4);
        translate([x_switchMount - d_switchMount, y_switchMount - d_switchMount, -0.5])
            mirror([1,0,0])
                linear_extrude(height = 1)
                    text("off", size = 4);
            
        // cavity
        translate([t_caseWall, t_caseWall, t_caseBase])
            cube([w_case - 2*t_caseWall, l_case - 2*t_caseWall, t_case]);
        
        // half wall for wires
        translate([t_caseWall, 2*t_caseWall, t_caseBase + t_caseHalfWall])
            cube([w_case - 2*t_caseWall, l_case, t_case-t_caseHalfWall]);
        
        // switch mount
        translate([x_switchMount, y_switchMount, 0])
            cylinder(h = t_case, d = d_switchMount);
        
        // cut board screws in the base
        for (dx = [0:1]) {
            for (dy = [0:1]) {
                translate([x_boardMount + dx*w_boardMounts, y_boardMount + dy*l_boardMounts, 0])
                    cylinder(h = t_boardSpacer + t_caseBase, d = d_boardScrew);
            }
        }
        
    }
    
    // build up board standoffs
    for (dx = [0:1]) {
        for (dy = [0:1]) {
            translate([x_boardMount + dx*w_boardMounts, y_boardMount + dy*l_boardMounts, t_caseBase])
                difference() {
                    cylinder(h = t_boardSpacer, d = d_boardSpacer);
                    cylinder(h = t_boardSpacer, d = d_boardScrew);
                }
            }
        }
        
    // wall attachment points
    for (dx = [0, w_case+w_wallMountLedge]) {
        difference() {
            translate([dx-w_wallMountLedge,(l_case-w_wallMountLedge)/2,t_case-t_wallMountLedge])
                cube([w_wallMountLedge, w_wallMountLedge, t_wallMountLedge]);
            translate([dx-w_wallMountLedge/2, l_case/2, 0])
                cylinder(h = t_case, d = d_wallMounts);
        }
    }
}
