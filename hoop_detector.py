import cv2
import imutils
import numpy as np

from enum import Enum
from time import sleep
from sklearn.cluster import KMeans
from vidgear.gears import WriteGear #Used this one instead of OpenCV's write function
                                    #Because the latter didn't work for me.
from scipy.spatial.distance import cdist

red_hsv_lower = np.array([0, 50, 50])
red_hsv_upper = np.array([10, 255, 255])
blue_hsv_lower = np.array([100, 40, 30])
blue_hsv_upper = np.array([125, 255, 150])

# TODO: --> args?
MODE = "video"
SAVE = False #Very heavy and slow process! Disable when running with Drone!
DRAW = True

#TODO: currently this is set in main, which we won't have access to when using it as a lib.
frame_dimensions = (0,0)

class PredictionCertainty(Enum):
    CERTAIN = 1,                # 4 hoop segments: prediction can be relied on
    RELIABLE = 2,               # 3 hoop segments: enough to estimate center of hoop
    DIRECTION_ESTIMATE = 3,     # 2 hoop segments: enough to estimate direction
    DIRECTION_GUESS = 4,        # 1 hoop segments: we guess one of two possible directions
    NOISY_PREDICTION = 5,       # >4 hoop segments: we potentially have detected an incorrect segment
    NONE = 6


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

def contour_detection(mask, frame):
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    # c = max(contours, key=cv2.contourArea)
    output_contours = frame.copy()
    contourlist = []
    anglelist = []
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
                anglelist.append(ang)
                cv2.drawContours(output_contours, [c], -1, (0, 255, 0), 3)
                # cv2.putText(output_contours, f"np: {len(c)}", (x, y-15), cv2.FONT_HERSHEY_SIMPLEX,
                #             2, (0, 255, 0), 5)
                cv2.drawContours(output_contours,[box],0,(0,191,255), 2)
                # cv2.putText(output_contours, f"ar: {ar:.0f}", (x, y-60), cv2.FONT_HERSHEY_SIMPLEX,
                #             2, (0, 191, 255), 5)
                # cv2.putText(output_contours, f"ang: {ang:.1f}", (x, y+30), cv2.FONT_HERSHEY_SIMPLEX,
                #             2, (0, 50, 255), 5)

    if not contourlist:
        return frame, None, None
    cnts = np.concatenate(contourlist)
    x,y,w,h=cv2.boundingRect(cnts)
    # cv2.rectangle(output_contours, (x-100,y-100),(x+w+100,y+h+100), (0,0,255),10)
    # cX = int(x + w/2)
    # cY = int(y + h/2)
    # cv2.circle(output_contours, (cX, cY), 15, (0, 0, 255), -1)

    rectlist = []
    for c in contourlist:
        rect = cv2.boundingRect(c)
        rectlist.append(rect)

    return output_contours, rectlist, anglelist

def filter_outliers(rectlist, anglelist):
    points = np.array([[rect[0]+rect[2]/2, rect[1]+rect[3]/2] for rect in rectlist])
    distances = cdist(points, points)
    sum_distances = distances.sum(axis=1)
    inlier_indices = np.argsort(sum_distances)[:4]

    inliers = points[inlier_indices]
    outliers = np.delete(points, inlier_indices, axis=0)
    inliers_rects = np.array(rectlist)[inlier_indices].tolist()
    outliers_rects = np.delete(np.array(rectlist), inlier_indices, axis=0).tolist()
    angle_inliers = np.array(anglelist)[inlier_indices].tolist()
    angle_outliers = np.delete(np.array(anglelist), inlier_indices, axis=0).tolist()
    #NOTE:  inliers/outliers are CENTERS of the rectts,
    #       while inliers_rects/outliers_rects are (x,y,w,h) tuples.
    return inliers, outliers, inliers_rects, outliers_rects, angle_inliers, angle_outliers
    #TODO: Make a decision on what to return.
    #      Eventually we will probably only want the inlier_rects

def get_bb_of_rects(rects):
    min_x = min([r[0] for r in rects])
    min_y = min([r[1] for r in rects])
    max_x = int(max([r[0]+r[2] for r in rects]))
    max_y = int(max([r[1]+r[3] for r in rects]))

    return min_x, min_y, max_x-min_x, max_y-min_y

def process_frame(frame):
    #TODO: the arrow drawing functions in this function can easily be refactored so we only
    #       need to call it once.
    rects_to_draw = []     #(point, dims, color, line_width)
    circles_to_draw = []   #(point, size, color, line_width)
    arrows_to_draw = []    #(point1, point2, color, line_width)

    certainty = None
    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = mask_frame(frame_hsv)
    output_contours, rectlist, anglelist = contour_detection(mask, frame)
    if rectlist:
        inliers, outliers, inliers_rects, outliers_rects, angle_inliers, angle_outliers \
            = filter_outliers(rectlist, anglelist)
        x,y,w,h = get_bb_of_rects(inliers_rects)
        if len(inliers) > 2:
            if len(inliers) <= 4:
                certainty = PredictionCertainty.CERTAIN
            elif len(inliers) > 4:
                certainty = PredictionCertainty.NOISY_PREDICTION
            else:
                certainty = PredictionCertainty.RELIABLE
            rects_to_draw.append(((x-50,y-50),(x+w+50,y+h+50),(0,255,0),8))
            cX = int(x + w/2)
            cY = int(y + h/2)
            circles_to_draw.append(((cX,cY), 10, (0, 255, 0), -1))
        elif len(inliers) == 2:
            certainty = PredictionCertainty.DIRECTION_ESTIMATE
            if abs(inliers[1][0] - inliers[0][0]) > abs(inliers[1][1] - inliers[0][1]):
                # The segments are on a horizontal line
                if inliers[0][0] < inliers[1][0]:
                    seg_l = inliers[0]
                    seg_r = inliers[1]
                    #seg_l_rect = inliers_rects[0]
                    #seg_r_rect = inliers_rects[1]
                    seg_l_angle = angle_inliers[0]
                    seg_r_angle = angle_inliers[1]
                else:
                    seg_l = inliers[1]
                    seg_r = inliers[0]
                    #seg_l_rect = inliers_rects[1]
                    #seg_r_rect = inliers_rects[0]
                    seg_l_angle = angle_inliers[1]
                    seg_r_angle = angle_inliers[0]
                #TODO: should we check if the angles are more or less what we expect here?
                #       I don't think so, right? We already filtered them?
                if seg_l_angle < seg_r_angle:
                    # shape = \  / --> We are too low
                    cX = int(x + w/2)
                    cY = int(y + h/2)
                    #TODO: make arrowlength dependent on frame dimensions
                    arrows_to_draw.append(((cX, cY), (cX, cY-100), (255,50,255), 10))
                else:
                    # shape = /  \ --> We are too high
                    cX = int(x + w/2)
                    cY = int(y + h/2)
                    arrows_to_draw.append(((cX, cY), (cX, cY+100), (255,50,255), 10))
            else:
                # The segments are on a vertical line
                if inliers[0][1] < inliers[1][1]:
                    seg_t = inliers[0]
                    seg_b = inliers[1]
                    #seg_t_rect = inliers_rects[0]
                    #seg_b_rect = inliers_rects[1]
                    seg_t_angle = angle_inliers[0]
                    seg_b_angle = angle_inliers[1]
                else:
                    seg_t = inliers[1]
                    seg_b = inliers[0]
                    #seg_t_rect = inliers_rects[1]
                    #seg_b_rect = inliers_rects[0]
                    seg_t_angle = angle_inliers[1]
                    seg_b_angle = angle_inliers[0]
                if seg_t_angle < seg_b_angle:
                    # shape = \  --> We are too far right
                    #         /
                    cX = int(x + w/2)
                    cY = int(y + h/2)
                    arrows_to_draw.append(((cX, cY), (cX-200, cY), (255,50,255), 10))
                else:
                    # shape = /  --> We are too far left
                    #         \
                    cX = int(x + w/2)
                    cY = int(y + h/2)
                    arrows_to_draw.append(((cX, cY), (cX+200, cY), (255,50,255), 10))

        elif len(inliers) == 1:
            #TODO: There's one import drawback of the current implementation!
            #       If the camera POV centerpoint is OUTSIDE of the hoop,
            #       AND it can only see a single segment, it will recommend steering the drone
            #       away from the hoop!!!
            #       Either we need to improve this algorithm (is that even possible?)
            #       Or be intelligent enough about this in the steering of the drone.
            certainty = PredictionCertainty.DIRECTION_GUESS
            cX = int(inliers[0][0])
            cY = int(inliers[0][1])
            if abs(angle_inliers[0]-45) < abs(angle_inliers[0]-135):
                #TODO: For now I only take x-axis into account.
                #       I think for 99% of the cases this will be enough.
                #       Ideally though, we would use some Pythagoras shit or smt.
                # Either TOP-RIGHT or BOTTOM-LEFT
                if inliers[0][0] > frame_dimensions[0]/2:
                    # segment is in right-most part of the screen
                    # --> down-left
                    arrows_to_draw.append(((cX, cY), (cX-200, cY+200), (255,50,255), 10))
                else:
                    # segment is in left-most part of the screen
                    # --> up-right
                    arrows_to_draw.append(((cX, cY), (cX+200, cY-200), (255,50,255), 10))
            else:
                # Either BOTTOM-RIGHT or TOP-LEFT
                # --> Steer down-right or up-left
                if inliers[0][0] > frame_dimensions[0]/2:
                    # segment is in right-most part of the screen
                    # --> up-left
                    arrows_to_draw.append(((cX, cY), (cX-200, cY-200), (255,50,255), 10))
                else:
                    # segment is in left-most part of the screen
                    # --> down-right
                    arrows_to_draw.append(((cX, cY), (cX+200, cY+200), (255,50,255), 10))
        else:
            certainty = PredictionCertainty.NONE
        #TODO: return both the prediction and the certainty of the prediction

        #TODO: Ideally we also calculate the pseudo distance from the hoop
        #       by checking the segment sizes.
        #       Larger size = closer to hoop --> less agressive controlling of drone
    if DRAW:
        for rect_to_draw in rects_to_draw:
            cv2.rectangle(output_contours, *rect_to_draw)
        for circle_to_draw in circles_to_draw:
            cv2.circle(output_contours, *circle_to_draw)
        for arrow_to_draw in arrows_to_draw:
            cv2.arrowedLine(output_contours, *arrow_to_draw)


    return output_contours

# TODO: I'm not a big fan of this. Need a more reliable way of doing things.
def set_frame_dimensions(dimensions):
    global frame_dimensions
    frame_dimensions = dimensions

def main():
    global frame_dimensions
    if MODE == "image":
        frame = cv2.imread('sample_data/hoop_blue.jpg')
        frame_dimensions = frame.shape
        output = process_frame(frame)
        cv2.imshow("Countours", make_size_reasonable(output))
        while True:
            k = cv2.waitKey(0)
            if k == 27:
                break
    elif MODE == "video":
        cap = cv2.VideoCapture('sample_data/sample_vid.mp4')
        ret, frame = cap.read()
        frame_dimensions = frame.shape
        if SAVE:
            output_params = {"-vcodec":"libx264", "-crf": 0, "-preset": "fast"}
            out = WriteGear(output='output.mp4', compression_mode=True, logging=False, **output_params)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("No more frames? Stream end?")
                break
            output = process_frame(frame)
            if cv2.waitKey(1) == ord('q'):
                break
            if SAVE:
                out.write(output)
            cv2.imshow("Countours", make_size_reasonable(output))
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


