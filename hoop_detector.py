import cv2
import numpy as np

frame = cv2.imread('sample_data/room_redcirc_left_solid.jpg')

frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

red_hsv_lower = np.array([0, 50, 50])
red_hsv_upper = np.array([10, 255, 255])

mask = cv2.inRange(frame_hsv, red_hsv_lower, red_hsv_upper)


kernel = np.ones((5,5), np.uint8)
# mask_corrected = cv2.erode(mask, kernel, iterations=1)
mask_corrected = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask_corrected = cv2.morphologyEx(mask_corrected, cv2.MORPH_CLOSE, kernel)
mask_corrected = cv2.dilate(mask_corrected, kernel, iterations=1)

result = cv2.bitwise_and(frame, frame, mask=mask_corrected)

cv2.imshow("frame", frame)
cv2.imshow("mask", mask)
cv2.imshow("mask_eroded", mask_corrected)
cv2.imshow("result", result)

while True:
    k = cv2.waitKey(0)
    if k == 27:
        break

cv2.destroyAllWindows()

