#!/usr/bin/env python
import cv2 
import numpy as np
import math
import constants as c


def  caclulate_euler_angles(rvec):
    # Convert rotation vector to rotation matrix
    R, v = cv2.Rodrigues(rvec)

    # Extract roll, pitch, yaw from the rotation matrix
    sy = math.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)

    roll  = math.atan2(R[2, 1], R[2, 2])
    pitch = math.atan2(-R[2, 0], sy)
    yaw   = math.atan2(R[1, 0], R[0, 0])
    # Convert radians to degrees
    return np.degrees([roll, pitch, yaw])
 
def main(): 

    # Load the camera parameters from the saved file
    with np.load(c.calibration_data) as X:
        mtx, dist = [X[i] for i in ('camera_matrix','dist_coeffs')]

    # Start the video stream     
    vid=cv2.VideoCapture(0)
    frame_width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_width = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

    #Setup arUco detector
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

    while(True):
        # Capture frame
        ret, frame = vid.read()    
        
        #Convert to grey to make detection easier
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        #Detect colours
        corners, ids, rejected = detector.detectMarkers(grey)
        
        # Check that at least one ArUco marker was detected
        if ids is not None:
            if(len(ids)>1):
                print("More markers received than expected")
            else:
                # Draw a square around detected markers in the video frame
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)

                # Flatten the corners to match the expected input shape for solvePnP
                img_points = np.array(corners, dtype=np.float32).reshape(-1, 2)
                ret, rvecs, tvecs = cv2.solvePnP(c.obj_points, img_points, mtx, dist)
            
                transform_translation_x = rvecs[0]
                transform_translation_y = rvecs[1]
                transform_translation_z = rvecs[2]

                # # Store the rotation information
               
                euler = caclulate_euler_angles(rvecs)
                print("roll : {:2f}, pitch: {:2f}, yaw: {:2f}".format(euler[2], euler[0], euler[1]), end = '\r')
         
        # Display the resulting frame
        cv2.imshow('frame',frame)
                    
        # If "q" is pressed on the keyboard, 
        # exit this loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Close down the video stream
    vid.release()
    cv2.destroyAllWindows()
     
if __name__ == '__main__':
    print(__doc__)
    main()
