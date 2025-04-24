import cv2
import imutils
import numpy as np

from time import sleep
from sklearn.cluster import KMeans
from vidgear.gears import WriteGear #Used this one instead of OpenCV's write function
                                    #Because the latter didn't work for me.

red_hsv_lower = np.array([0, 50, 50])
red_hsv_upper = np.array([10, 255, 255])
blue_hsv_lower = np.array([100, 40, 30])
blue_hsv_upper = np.array([125, 255, 150])

# TODO: --> args?
MODE = "video"
SAVE = False #Very heavy and slow process! Disable when running with Drone!

def make_size_reasonable(img):
    return cv2.resize(img, (800,800), interpolation=cv2.INTER_LINEAR)

def compute_cluster_center(cluster):
    if len(cluster) == 0:
        return None
    # Calculate average angle and its perpendicular direction
    avg_angle = np.mean([np.arctan2(y2 - y1, x2 - x1) for x1, y1, x2, y2 in cluster])
    perp_angle = avg_angle + np.pi/2  # Perpendicular direction

    # Project midpoints onto perpendicular direction
    midpoints = np.array([[(x1 + x2)/2, (y1 + y2)/2] for x1, y1, x2, y2 in cluster])
    dir_vector = np.array([np.cos(perp_angle), np.sin(perp_angle)])
    projections = midpoints @ dir_vector

    # Get lines with min/max projections and their midpoints
    min_idx, max_idx = np.argmin(projections), np.argmax(projections)
    mid_min = midpoints[min_idx]
    mid_max = midpoints[max_idx]

    # Center is the average of the two midpoints
    return ((mid_min[0] + mid_max[0])/2, (mid_min[1] + mid_max[1])/2)

def calculate_aspect_ratio(points):
    # Reshape input to 4x2 numpy array
    pts = np.array(points).reshape(4, 2)

    # Calculate all four side lengths
    side_lengths = []
    for i in range(4):
        x1, y1 = pts[i]
        x2, y2 = pts[(i+1)%4]
        side_lengths.append(np.linalg.norm([x2-x1, y2-y1]))

    # Calculate average lengths for opposite sides
    length = (side_lengths[0] + side_lengths[2]) / 2
    width = (side_lengths[1] + side_lengths[3]) / 2

    # Return ratio with longer dimension as numerator
    return max(length, width) / min(length, width)

def calculate_rotation_angle(points):
    # Reshape points to 4x2 array
    pts = np.array(points).reshape(4, 2)

    # Calculate all four side lengths
    side_lengths = []
    for i in range(4):
        x1, y1 = pts[i]
        x2, y2 = pts[(i+1)%4]
        side_lengths.append(np.linalg.norm([x2-x1, y2-y1]))

    # Average opposite sides
    length = (side_lengths[0] + side_lengths[2]) / 2
    width = (side_lengths[1] + side_lengths[3]) / 2

    # Select appropriate side based on longest dimension
    if length >= width:
        # Use first length side (points 0->1)
        p1, p2 = pts[0], pts[1]
    else:
        # Use first width side (points 1->2)
        p1, p2 = pts[1], pts[2]

    # Calculate vector components
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    # Calculate angle in degrees
    angle_deg = np.degrees(np.arctan2(dy, dx))

    # Normalize to 0-180° range
    angle_deg = angle_deg % 180
    if angle_deg == 180:
        angle_deg = 0

    return angle_deg

def mask_frame(frame):
# mask = cv2.inRange(frame_hsv, red_hsv_lower, red_hsv_upper)
    mask = cv2.inRange(frame, blue_hsv_lower, blue_hsv_upper)

    mask_corrected = mask

    kernel = np.ones((5,5), np.uint8)
    kernel_small = np.ones((2,2), np.uint8)
    kernel_large = np.ones((20,20), np.uint8)
    # mask_corrected = cv2.erode(mask, kernel, iterations=1)
    mask_corrected = cv2.dilate(mask, kernel_small, iterations=2)   #TODO: might need to remove this in final. (thin drawn lines)
    mask_corrected = cv2.morphologyEx(mask_corrected, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask_corrected = cv2.morphologyEx(mask_corrected, cv2.MORPH_OPEN, kernel, iterations=1)
    # mask_corrected = cv2.morphologyEx(mask_corrected, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask_corrected = cv2.dilate(mask_corrected, kernel, iterations=5)
    # mask_corrected = cv2.morphologyEx(mask_corrected, cv2.MORPH_CLOSE, kernel_large, iterations=2)
    return mask_corrected

def line_detector(mask):
    edges = cv2.Canny(mask, 50,150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=20)

    if lines is not None:
        # lines = lines.reshape(-1, 4)
        print(lines)
        line_plot = frame.copy()
        print("\n\n")
        for line in lines:
            cv2.line(line_plot, (line[0][0], line[0][1]), (line[0][2], line[0][3]), (0,255,0), 5)
        # cv2.imshow("lines", make_size_reasonable(line_plot))

        # Calculate angles of each line (in radians)
        # angles = np.array([np.arctan2(y2 - y1, x2 - x1) for x1, y1, x2, y2 in lines])
        # angles = angles.reshape(-1, 1)
        # print(angles)
        # if len(angles) < 2 or True:
        #     print("Not enough angles!")
        # else:
        #     # Cluster angles into two groups
        #     kmeans = KMeans(n_clusters=2).fit(angles)
        #     labels = kmeans.labels_

        #     # Separate lines into clusters
        #     cluster0 = lines[labels == 0]
        #     cluster1 = lines[labels == 1]

        #     # Compute centers for both clusters
        #     center0 = compute_cluster_center(cluster0)
        #     center1 = compute_cluster_center(cluster1)

        #     if center0 and center1:
        #         hoop_center = ((center0[0] + center1[0])//2, (center0[1] + center1[1])//2)
        #         print("Hoop center:", hoop_center)
        #         # Draw center on image
        #         result = frame
        #         cv2.circle(result, hoop_center, 5, (0, 0, 255), -1)

        #         cv2.imshow("result", result)
        #     else:
        #         print("insufficient lines to compute center")
    else:
            print("No lines detected")

def contour_detection(mask, frame):
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    # c = max(contours, key=cv2.contourArea)
    output_contours = frame.copy()
    contourlist = []
    for c in contours:
        (x, y, w, h) = cv2.boundingRect(c)
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        ar = calculate_aspect_ratio(box)
        #TODO:  make filtering more agressive again.
        #       currently we have to lower it, because the fire extinguisher on the sample
        #       image has a tiny blue line that connects with the hoop...
        if ar > 1.8 and ar < 5:
            ang = calculate_rotation_angle(box)
            if (35 <= ang <= 55) or (125 <= ang <= 145):
                contourlist.append(c)
                cv2.drawContours(output_contours, [c], -1, (0, 255, 0), 3)
                # cv2.putText(output_contours, f"np: {len(c)}", (x, y-15), cv2.FONT_HERSHEY_SIMPLEX,
                #             2, (0, 255, 0), 5)
                cv2.drawContours(output_contours,[box],0,(0,191,255), 2)
                # cv2.putText(output_contours, f"ar: {ar:.0f}", (x, y-60), cv2.FONT_HERSHEY_SIMPLEX,
                #             2, (0, 191, 255), 5)
                # cv2.putText(output_contours, f"ang: {ang:.1f}", (x, y+30), cv2.FONT_HERSHEY_SIMPLEX,
                            # 2, (0, 50, 255), 5)

    if not contourlist:
        print("No contours found in this frame!")
        return frame
    cnts = np.concatenate(contourlist)
    x,y,w,h=cv2.boundingRect(cnts)
    cv2.rectangle(output_contours, (x-100,y-100),(x+w+100,y+h+100), (0,0,255),10)
    cX = int(x + w/2)
    cY = int(y + h/2)
    cv2.circle(output_contours, (cX, cY), 5, (0, 0, 255), 30)
    #TODO: return useful stuff from contour detection instead of drawing here
    return output_contours




def main():
    if MODE == "image":
        frame = cv2.imread('sample_data/hoop_blue.jpg')
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = mask_frame(frame_hsv)
        output_contours = contour_detection(mask, frame)
        cv2.imshow("Countours", make_size_reasonable(output_contours))

        # cv2.imshow("frame", make_size_reasonable(frame))
        # cv2.imshow("mask", make_size_reasonable(mask))
        # cv2.imshow("mask_eroded", make_size_reasonable(mask_corrected))


        while True:
            k = cv2.waitKey(0)
            if k == 27:
                break
    elif MODE == "video":
        cap = cv2.VideoCapture('sample_data/sample_vid.mp4')
        if SAVE:
            ret, frame = cap.read()
            oh = frame.shape[0]
            ow = frame.shape[1]
            output_params = {"-vcodec":"libx264", "-crf": 0, "-preset": "fast"}
            out = WriteGear(output='output.mp4', compression_mode=True, logging=False, **output_params)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("No more frames? Stream end?")
                break
            frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = mask_frame(frame_hsv)
            output_contours = contour_detection(mask, frame)
            if cv2.waitKey(1) == ord('q'):
                break
            if SAVE:
                out.write(output_contours)
            cv2.imshow("Countours", make_size_reasonable(output_contours))
            sleep(1/70) #Playback is too fast, slow it down a bit
        cap.release()
        if SAVE:
            out.close()
    else:
        print("Unknown mode!")
        exit(0)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


