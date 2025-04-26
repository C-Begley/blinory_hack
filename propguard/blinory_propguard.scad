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
leg_h = 11;
leg_w = 10.5;
leg_l = 10;
floor_t = 2;
sf = 0.5;       // Shrink fit
prop_h = 11;   // Extra height of prop above motor_h
prop_r = 65;    // length of prop measured from center of motor
prop_margin = 5;// Safety margin
guard_angle = 90;
guard_beam_t = wall_t;
guard_beam_l = prop_r - motor_d/2 - wall_t + guard_beam_t + prop_margin;
cheatval = 6;   //I honestly don't know why I needed this.
                // I can't mathz

text_shift = prop_r/2;
textdepth = 1.5;


diff()
tube(id1=motor_d-sf, id2=motor_d, od=motor_d+wall_t, h=motor_h){
    tag("remove") position(LEFT) right(wall_t/2) cuboid([wall_t, leg_w, leg_h+2]);
    align(BOTTOM)
        zcyl(d=motor_d+wall_t, h=floor_t);
    align(LEFT){
    right(wall_t/2) cuboid([leg_l+wall_t/2, leg_w+wall_t, leg_h]);
    tag("remove") attach(CTR) right(wall_t/2) cuboid([leg_l+wall_t/2+1, leg_w, leg_h+1]);
    }
    // guard beams
    for(i = [-1, 1]){
        zrot(i * guard_angle/2) align(RIGHT)
            cuboid([guard_beam_l, guard_beam_t, guard_beam_t]){
                align(TOP,RIGHT) cuboid([wall_t, guard_beam_t, prop_h]);
                tag("remove") color("red") position(TOP) down(textdepth-0.01) fwd((guard_beam_t*0.8)/2)
                left(text_shift) linear_extrude(textdepth)
                    text("REDWIRE SPACE / J-CLAW", size=guard_beam_t*0.8);
            }
    }
    // Outer arc
    for(a = [-guard_angle/2 - cheatval:1:guard_angle/2 +cheatval]){
        align(RIGHT) zrot(a)up(prop_h) right(guard_beam_l)  cuboid([guard_beam_t, guard_beam_t/2, guard_beam_t]);
    }
}


