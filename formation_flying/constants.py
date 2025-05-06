import numpy as np


cam_type = "webcam"
calibration_base_dir = "calibration_data/" + cam_type +"/"
image_base_dir = "calibration_images/" + cam_type + "/"
calibration_base_dir = "calibration_data/" + cam_type + "/"
calibration_data = calibration_base_dir + "calibration_data.npz"
image_type = ".jpg"
train_image_loc = image_base_dir + "training"
test_image_loc = image_base_dir + "unused/"
test_image = test_image_loc + "unused0.jpg"

#To be changed depending on size of marker
# Side length of the ArUco marker in meters 
marker_size = 0.13

# Define the 3D model points of the marker corners
obj_points = np.array([
    [-marker_size / 2, -marker_size / 2, 0],
    [marker_size / 2, -marker_size / 2, 0],
    [marker_size / 2, marker_size / 2, 0],
    [-marker_size / 2, marker_size / 2, 0]], dtype=np.float32)
