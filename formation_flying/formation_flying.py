#!/usr/bin/env python
import cv2 
import numpy as np
import math
import constants as c
import time as t

import sys
sys.path.append("..")
from blinory import Drone


def calculate_euler_angles(rvec):
    # Convert rotation vector to rotation matrix
    R, v = cv2.Rodrigues(rvec)

    # Extract roll, pitch, yaw from the rotation matrix
    sy = math.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)

    roll  = math.atan2(R[2, 1], R[2, 2])
    pitch = math.atan2(-R[2, 0], sy)
    yaw   = math.atan2(R[1, 0], R[0, 0])
    # Convert radians to degrees
    return np.degrees([roll, pitch, yaw])

def update_value(val, tol):
    if(val > tol):
        return val - tol
    elif (val < (-tol)):
        return val + tol
    else:
        return 0

class formation_flyer():
    def __init__(self, frame_width = 1024, frame_height = 1024, display_frame=True, draw_marker=True): 
        self.x_tol = 10
        self.y_tol = 10
        self.roll_tol = 10
        self.yaw_tol = 10
        self.pitch_tol = 10

        self.x_cor = 0
        self.y_cor = 0
        self.roll_cor = 0
        self.yaw_cor = 0
        self.pitch_cor = 0

        self.correction = False

        self.set_dimensions(frame_width, frame_height)

        self.display_frame = display_frame
        self.draw_marker = draw_marker

        # Load the camera parameters from the saved file
        with np.load(c.calibration_data) as X:
            self.mtx, self.dist = [X[i] for i in ('camera_matrix','dist_coeffs')]

        #Setup arUco detector
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    def set_dimensions(self, frame_width, frame_height):
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.centre_x = frame_width/2
        self.centre_y = frame_height/2

    def get_centre(self, corners):
        x_sum = corners[0][0][0][0]+ corners[0][0][1][0]+ corners[0][0][2][0]+ corners[0][0][3][0]
        y_sum = corners[0][0][0][1]+ corners[0][0][1][1]+ corners[0][0][2][1]+ corners[0][0][3][1]
        
        self.x_cor = update_value(self.centre_x-(x_sum*.25), self.x_tol)
        self.y_cor = update_value(self.centre_y-(y_sum*.25), self.y_tol)

    def get_angles(self, frame, corners, ids):
        # Draw a square around detected markers in the video frame
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # Flatten the corners to match the expected input shape for solvePnP
        img_points = np.array(corners, dtype=np.float32).reshape(-1, 2)
        ret, rvecs, tvecs = cv2.solvePnP(c.obj_points, img_points, self.mtx, self.dist)

        transform_translation_x = rvecs[0]
        transform_translation_y = rvecs[1]
        transform_translation_z = rvecs[2]
    
        euler = calculate_euler_angles(rvecs)

        self.roll_cor = update_value(euler[2], self.roll_tol)
        self.pitch_cor = update_value(euler[0], self.pitch_tol)
        self.yaw_cor = update_value(euler[1], self.yaw_tol)

    def find_corrections(self, frame, corners, ids):
        if ids is not None:
            if(len(ids)>1):
                print("More markers received than expected")
            else:
                self.get_centre(corners)
                self.get_angles(frame, corners, ids)
                if(self.draw_marker):
                    cv2.aruco.drawDetectedMarkers(frame, corners, ids)

    def process_frame(self, frame):   
        
        #Convert to grey to make detection easier
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        #Detect AruCo marker
        corners, ids, rejected = self.detector.detectMarkers(grey)
        
        # Check that at least one ArUco marker was detected
        if ids is not None:
            if(len(ids)>1):
                print("More markers received than expected")
            else:
                self.find_corrections(frame,corners,ids)
        
        if(self.display_frame):
            cv2.imshow('frame',frame)

        if(1):
            print("Move x: {:2f}, y: {:2f}, roll : {:2f}, pitch: {:2f}, yaw: {:2f}".format(
                self.x_cor, self.y_cor, self.roll_cor, self.pitch_cor, self.yaw_cor))

        self.correction = (self.x_cor != 0) or (self.y_cor != 0) or (self.yaw_cor !=0)

    def run_webcam(self, vid):

        self.vid = vid
        frame_width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.set_dimensions(frame_width, frame_height)

        while(True):
            ret, frame = self.vid.read() 
            self.process_frame(frame)
            # If "q" is pressed on the keyboard, 
            # exit this loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Close down the video stream
        self.vid.release()
        cv2.destroyAllWindows()

def main():
    vid=cv2.VideoCapture(0)
    drone = Drone()
    flyer = formation_flyer()
    flyer.run_webcam(vid)

if __name__ == '__main__':
    print(__doc__)
    main()
