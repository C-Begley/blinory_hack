'''
Copyright (C) 2025

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import cv2
import numpy as np

# Load the image

vid=cv2.VideoCapture(0)
frame_width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_width = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

while(vid.isOpened()):
    ret,frame=vid.read()
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = detector.detectMarkers(grey)
    cv2.imshow('Video',frame)
    if ids is not None:
        x_sum = corners[0][0][0][0]+ corners[0][0][1][0]+ corners[0][0][2][0]+ corners[0][0][3][0]
        y_sum = corners[0][0][0][1]+ corners[0][0][1][1]+ corners[0][0][2][1]+ corners[0][0][3][1]

        x_centerPixel = x_sum*.25
        y_centerPixel = y_sum*.25
        print("Other drone at :", x_centerPixel, y_centerPixel)
    if cv2.waitKey(1) & 0xFF ==ord('q'):
        break
   
vid.release()
cv2.destroyAllWindows()


