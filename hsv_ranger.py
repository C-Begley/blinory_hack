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
#finding hsv range of target object(pen)
from auto_connect import auto_connect
from time import sleep
import cv2
import numpy as np
import time
import pylwdrone
import h264decoder
# A required callback method that goes into the trackbar function.
def nothing(x):
    pass

# Initializing the webcam feed.
# cap = cv2.VideoCapture(0)
# cap.set(3,1280)
# cap.set(4,720)
drone_stream = pylwdrone.LWDrone()
decoder = h264decoder.H264Decoder()
# set_frame_dimensions((1152, 2048))

if auto_connect() < 0:  #TODO: maybe make this one configurable? On/Off?
    print("Error connecting to drone. Was it on?")
sleep(1)

# Create a window named trackbars.
cv2.namedWindow("Trackbars")

# Now create 6 trackbars that will control the lower and upper range of
# H,S and V channels. The Arguments are like this: Name of trackbar,
# window name, range,callback function. For Hue the range is 0-179 and
# for S,V its 0-255.
cv2.createTrackbar("L - H", "Trackbars", 0, 179, nothing)
cv2.createTrackbar("L - S", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("L - V", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("U - H", "Trackbars", 179, 179, nothing)
cv2.createTrackbar("U - S", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("U - V", "Trackbars", 255, 255, nothing)

frame = None

for _frame in drone_stream.start_video_stream():
    framedatas=decoder.decode(bytes(_frame.frame_bytes))
    for framedata in framedatas:
        (frame, w, h, ls) = framedata
        if frame is not None:
            frame = np.frombuffer(frame, dtype=np.ubyte, count=len(frame))
            frame = frame.reshape((h, ls//3, 3))
            frame = frame[:,:w,:]
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  #TODO: make more efficient
                                                                    # by not doing 2 conversions

            # # Start reading the webcam feed frame by frame.
            # ret, frame = cap.read()
            # if not ret:
            #     break
            # Flip the frame horizontally (Not required)
            # frame = cv2.flip( frame, 1 )

            # Convert the BGR image to HSV image.
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Get the new values of the trackbar in real time as the user changes
            # them
            l_h = cv2.getTrackbarPos("L - H", "Trackbars")
            l_s = cv2.getTrackbarPos("L - S", "Trackbars")
            l_v = cv2.getTrackbarPos("L - V", "Trackbars")
            u_h = cv2.getTrackbarPos("U - H", "Trackbars")
            u_s = cv2.getTrackbarPos("U - S", "Trackbars")
            u_v = cv2.getTrackbarPos("U - V", "Trackbars")

            # Set the lower and upper HSV range according to the value selected
            # by the trackbar
            lower_range = np.array([l_h, l_s, l_v])
            upper_range = np.array([u_h, u_s, u_v])

            # Filter the image and get the binary mask, where white represents
            # your target color
            mask = cv2.inRange(hsv, lower_range, upper_range)

            # You can also visualize the real part of the target color (Optional)
            res = cv2.bitwise_and(frame, frame, mask=mask)

            # Converting the binary mask to 3 channel image, this is just so
            # we can stack it with the others
            mask_3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

            # stack the mask, orginal frame and the filtered result
            # stacked = np.hstack((mask_3,frame,res))
            stacked = np.hstack((frame,res))

            # Show this stacked frame at 40% of the size.
            cv2.imshow('Trackbars',cv2.resize(stacked,None,fx=0.3,fy=0.4))

            # If the user presses ESC then exit the program
            key = cv2.waitKey(1)
            if key == 27:
                break

            # If the user presses `s` then print this array.
            if key == ord('s'):

                thearray = [[l_h,l_s,l_v],[u_h, u_s, u_v]]
                print(thearray)

                # Also save this array as penval.npy
                np.save('hsv_value',thearray)
                break
# If the drone disconnects due to time out, let's continue with the last frame
while True:
    # Convert the BGR image to HSV image.
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get the new values of the trackbar in real time as the user changes
    # them
    l_h = cv2.getTrackbarPos("L - H", "Trackbars")
    l_s = cv2.getTrackbarPos("L - S", "Trackbars")
    l_v = cv2.getTrackbarPos("L - V", "Trackbars")
    u_h = cv2.getTrackbarPos("U - H", "Trackbars")
    u_s = cv2.getTrackbarPos("U - S", "Trackbars")
    u_v = cv2.getTrackbarPos("U - V", "Trackbars")

    # Set the lower and upper HSV range according to the value selected
    # by the trackbar
    lower_range = np.array([l_h, l_s, l_v])
    upper_range = np.array([u_h, u_s, u_v])

    # Filter the image and get the binary mask, where white represents
    # your target color
    mask = cv2.inRange(hsv, lower_range, upper_range)

    # You can also visualize the real part of the target color (Optional)
    res = cv2.bitwise_and(frame, frame, mask=mask)

    # Converting the binary mask to 3 channel image, this is just so
    # we can stack it with the others
    mask_3 = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    # stack the mask, orginal frame and the filtered result
    # stacked = np.hstack((mask_3,frame,res))
    stacked = np.hstack((frame,res))

    # Show this stacked frame at 40% of the size.
    cv2.imshow('Trackbars',cv2.resize(stacked,None,fx=0.3,fy=0.4))

    # If the user presses ESC then exit the program
    key = cv2.waitKey(1)
    if key == 27:
        break

    # If the user presses `s` then print this array.
    if key == ord('s'):

        thearray = [[l_h,l_s,l_v],[u_h, u_s, u_v]]
        print(thearray)

        # Also save this array as penval.npy
        np.save('hsv_value',thearray)
        break

# Release the camera & destroy the windows.
# cap.release()
while True:
    k = cv2.waitKey(0)
    if k == 27:
        break
cv2.destroyAllWindows()

