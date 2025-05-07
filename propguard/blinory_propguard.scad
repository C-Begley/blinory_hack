/*
 * Copyright (c) 2023 Wouter Symons
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */
include <BOSL2/constants.scad>
include <BOSL2/std.scad>
include <BOSL2/transforms.scad>

$fn = 60;

motor_d = 20;
motor_h = 10;
wall_t = 4;
arm_wall_t = wall_t * 1.3;
leg_h = 11;
leg_w = 10.5;
leg_l = 30;
floor_t = 2;
sf = 0.5;       // Shrink fit
prop_h = 14;   // Extra height of prop above motor_h
prop_r = 65;    // length of prop measured from center of motor
prop_margin = 8;// Safety margin
guard_angle = 140;
guard_beam_n = 3;
guard_beam_t = wall_t;
guard_beam_l = prop_r - motor_d/2 - wall_t + guard_beam_t + prop_margin;
guard_beam_knee = prop_h;
/* TYPE = "FRONT_LEFT"; */
TYPE = "FRONT_RIGHT";
/* TYPE = "BACK"; */
guard_angle_front = 35;                     //Only for FRONT_ types
guard_long_beam_l = guard_beam_l + 46.5;    //Only for FRONT_ types
guard_beam_connector_orb_d = guard_beam_t*2;
guard_beam_connector_orb_flatten = [0.9, 1.5, 1.2];
extension_front = 110;                      //Only for FRONT_ types


text_shift = prop_r/3;
textdepth = 1.5;
enable_text = false;

foot_hole_d = 10;


$align_msg=false;

speed_up_render = 1;    // Set this  to a higher value (e.g. 5) to increase render speed during development

diff()
tube(id1=motor_d-sf, id2=motor_d, od=motor_d+wall_t, h=motor_h){
    tag("remove") position(LEFT) right(wall_t/2) cuboid([wall_t, leg_w, leg_h+floor_t+2]);
    align(BOTTOM){
        zcyl(d=motor_d+wall_t, h=floor_t)
        // Hole in floor for drone feet
        align(BOTTOM,RIGHT) {
            left(wall_t/2) up(floor_t+0.1)
            tag("remove") yscale(1.5)zcyl(d=foot_hole_d, h=floor_t+0.2);
        }
    }
    align(LEFT){
    down(floor_t/2) right(arm_wall_t/2) cuboid([leg_l+wall_t/2, leg_w+arm_wall_t, leg_h + floor_t/2]);
    tag("remove") attach(CTR) right(wall_t/2) cuboid([leg_l+wall_t/2+1, leg_w, leg_h+floor_t+1.01]);
    }

    // guard beams
    for(i = [(TYPE=="FRONT_LEFT"?0:-guard_angle/2)
            :guard_angle/(guard_beam_n-1)-0.01
            :(TYPE=="FRONT_RIGHT"?1:guard_angle/2)]){
        zrot(i) align(RIGHT, TOP)
            left(0.3)//Snug fit of cuboid to round surface of tube
            cuboid([guard_beam_l-guard_beam_knee , guard_beam_t, guard_beam_t]){
                // Make tip of beam an angle.
                //TODO: I'm not proud of this implementation. There has to be a better way.
                n_seg = 40 / speed_up_render;
                align(RIGHT)
                left(guard_beam_t)
                for(x = [0 : guard_beam_knee/n_seg : guard_beam_knee] )
                {
                    move([x,0,(x*x*x)/(guard_beam_knee*guard_beam_knee)]) cuboid([guard_beam_t, guard_beam_t, guard_beam_t]);
                }
                align(RIGHT)
                    move([guard_beam_connector_orb_d/1, 0, guard_beam_knee + guard_beam_connector_orb_d/3])
                    scale(guard_beam_connector_orb_flatten)
                    sphere(d=guard_beam_connector_orb_d);
                if (enable_text){
                    tag("remove") color("red") position(TOP)
                    down(textdepth-0.01) fwd((guard_beam_t*0.8)/2)
                    left(text_shift) linear_extrude(textdepth)
                        text("REDWIRE SPACE", size=guard_beam_t*0.8);

                }
                // attachment to base
                align(LEFT) right(guard_beam_t/1.5)
                    back(guard_beam_t)
                    wedge([guard_beam_t, guard_beam_t, guard_beam_t], orient=RIGHT);
                align(LEFT) fwd(guard_beam_t*1.5)
                    right(guard_beam_t/5)   //I don't know how this bottom one works...
                    zrot(-90)
                    wedge([guard_beam_t, guard_beam_t, guard_beam_t], orient=RIGHT);
                align(LEFT)
                    zrot(-90)
                    move([wall_t/2, wall_t/2-0.1, -guard_beam_t+0.01])
                    wedge([guard_beam_t, guard_beam_t, guard_beam_t], orient=BACK);
            }
    }
    // longer guard beams
    if (TYPE == "FRONT_LEFT" || TYPE == "FRONT_RIGHT") {
        inverse = (TYPE=="FRONT_LEFT"?1:-1);
        zrot(-guard_angle/2*inverse) align(RIGHT, TOP)
                left(0.3)//Snug fit of cuboid to round surface of tube
                cuboid([guard_long_beam_l-guard_beam_knee , guard_beam_t, guard_beam_t]){
                    // Make tip of beam an angle.
                    //TODO: I'm not proud of this implementation. There has to be a better way.
                    n_seg = 40 / speed_up_render;
                    align(RIGHT)
                    left(guard_beam_t)
                    for(x = [0 : guard_beam_knee/n_seg : guard_beam_knee] )
                    {
                        move([x,0,(x*x*x)/(guard_beam_knee*guard_beam_knee)]) cuboid([guard_beam_t, guard_beam_t, guard_beam_t]);
                    }
                    align(RIGHT)
                        move([guard_beam_connector_orb_d*1.2, -inverse*guard_beam_connector_orb_d*0.3, guard_beam_knee + guard_beam_connector_orb_d/3])
                    zrot(inverse*guard_angle_front)
                    scale(guard_beam_connector_orb_flatten)
                    sphere(d=guard_beam_connector_orb_d);
                    if (enable_text){
                        tag("remove") color("red") position(TOP)
                        down(textdepth-0.01) fwd((guard_beam_t*0.8)/2)
                        left(text_shift) linear_extrude(textdepth)
                            text("REDWIRE SPACE", size=guard_beam_t*0.8);

                    }
                    // attachment to base for longer arm
                    align(LEFT) right(guard_beam_t/1.5)
                        back(guard_beam_t)
                        wedge([guard_beam_t, guard_beam_t, guard_beam_t], orient=RIGHT);
                    align(LEFT) fwd(guard_beam_t*1.5)
                        right(guard_beam_t/5)   //I don't know how this bottom one works...
                        zrot(-90)
                        wedge([guard_beam_t, guard_beam_t, guard_beam_t], orient=RIGHT);
                    align(LEFT)
                        zrot(-90)
                        move([wall_t/2, wall_t/2-0.1, -guard_beam_t+0.01])
                        wedge([guard_beam_t, guard_beam_t, guard_beam_t], orient=BACK);
                }
    }
    // Outer arc
    for(a = [-(TYPE=="FRONT_LEFT"?guard_angle_front:guard_angle)/2-1.0
                :1 * speed_up_render
                : (TYPE=="FRONT_RIGHT"?guard_angle_front:guard_angle)/2+1.0]){
        left(0.3)//Move together with beam
        align(TOP) zrot(a)up(prop_h) right(guard_beam_l + guard_beam_knee - guard_beam_t)
            cuboid([guard_beam_t, guard_beam_t/2, guard_beam_t]);
    }
    if (TYPE == "FRONT_LEFT" || TYPE == "FRONT_RIGHT") {
        // Arc extension
        inverse = (TYPE=="FRONT_LEFT"?1:-1);
        zrot(-guard_angle_front/2*inverse) align(TOP, RIGHT)
            left(-guard_beam_l+0.3)
            up(prop_h)
            fwd(extension_front/2*inverse)
            cuboid([guard_beam_t, extension_front, guard_beam_t]);
    }
}


