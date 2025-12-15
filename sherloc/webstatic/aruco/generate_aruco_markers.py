import cv2

# Use the simplest and most stable dictionary
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

for marker_id in [0, 1, 2, 3]:
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, 200)
    cv2.imwrite(f"aruco_{marker_id}.png", marker_img)

print("Generated markers: aruco_0.png, aruco_1.png, aruco_2.png, aruco_3.png")
