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


