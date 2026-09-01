# save_marker.py
import cv2
import numpy as np

aruco = cv2.aruco
dic = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)

marker_id = 0
px_size   = 600  # image size to save (pixels)
img = aruco.generateImageMarker(dic, marker_id, px_size)

# add a white border (“quiet zone”)
pad = 40
canvas = 255*np.ones((px_size+2*pad, px_size+2*pad), np.uint8)
canvas[pad:-pad, pad:-pad] = img

cv2.imwrite("aruco_4x4_50_id0.png", cv2.flip(canvas, 1))
print("Saved aruco_4x4_50_id0.png")
