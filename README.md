# Redwire space Drone Challenge

This repository contains the source code for Redwire Belgium's team, J-CLAW, participating in the Redwire Space Hack-A-Drone challenge.

Please note that the master branch is heavily outdated and should be considered as defunct. Each challenge has received its own feature branch. Despite having the same ancestor, they will not be merged back together due to having branched off too far.

## Branch overview

* Branch **hoop_flying_optimizations** contains the source code for Challenge 2: autonomous flying.
* Branch **formation flying** contains the source code for Challenge 3: "perform a trick" (PROBA3 Formation flying)
* Branch **rebase_led_code_update** contains the source code for Challenge 4: "exhibit artistic innovation" (Long exposure letter/logo drawing)
* Branches **prop_guard** and **arucoo_mount** contain the OpenSCAD source code to generate the 3D models for the prop guard and the arucoo code mount respectively.

## Files of interest

* control_panel.py: contains the UI as well as the control algorithms for the hoop flying, formation flying and LED drawing.
* hoop_detector.py: contains the code to pull in the stream and detect the hoops
* start_control_panel.sh: contains a convenience script to easily connect to the drone. (Only tested on Ubuntu and Arch Linux.)
* blinory.py: constains drone controlling functionalities

