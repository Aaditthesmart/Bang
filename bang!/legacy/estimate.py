import cv2
import numpy as np
import math
from collections import deque
import json
import os

class Estimate:
    MARKER_SIZE_M = 0.03
    WIDTH = 1280
    HEIGHT = 720
    
    def __init__(self):
        # Initialize distortion coefficients first
        self.dist = np.array([0, 0, 0, 0, 0], dtype=np.float64)
        
        # Camera intrinsics 
        try:
            calib_path = os.path.join(os.getcwd(), "calib.json")  # Fixed path join
            with open(calib_path, "r") as f:
                self.data = json.load(f)
            self.K = np.array([[self.data["fx"], 0, self.data["cx"]],
                        [0, self.data["fy"], self.data["cy"]],
                        [0,  0,  1]], dtype=np.float64)
            print("Loaded camera calibration from calib.json")
        except FileNotFoundError:
            print("Warning: calib.json not found, using default camera matrix")
            # Default camera matrix for 1280x720
            self.K = np.array([[800.0, 0, 640.0],
                        [0, 800.0, 360.0],
                        [0,  0,  1]], dtype=np.float64)
        except Exception as e:
            print(f"Error loading calibration: {e}, using default camera matrix")
            self.K = np.array([[800.0, 0, 640.0],
                        [0, 800.0, 360.0],
                        [0,  0,  1]], dtype=np.float64)
        
        self.aruco = cv2.aruco
        dic = self.aruco.getPredefinedDictionary(self.aruco.DICT_4X4_50)
        params = self.aruco.DetectorParameters()
        self.detector = self.aruco.ArucoDetector(dic, params)
        
        half = self.MARKER_SIZE_M / 2.0
        self.objp = np.array([
            [-half,  half, 0.0],  # TL
            [ half,  half, 0.0],  # TR
            [ half, -half, 0.0],  # BR
            [-half, -half, 0.0],  # BL
        ], dtype=np.float32)
        
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self.in_game_deg = 90.0  # Default to center position

    def draw_semi_gauge(
        self,
        frame,
        center=(180, 500),        # (x,y) pixels
        radius=120,               # dial radius in px
        value_deg=0.0,            # current value in degrees
        min_deg=-90.0,            # dial range min (left end)
        max_deg= 90.0,            # dial range max (right end)
        color_arc=(100, 100, 100),
        color_tick=(100, 100, 100),
        color_needle=(0, 0, 255),
    ):
        """
        Draw a 180° gauge (semi-circle) with ticks and a needle pointing at value_deg.
        Angle mapping: min_deg -> left end, max_deg -> right end, 0 centered.
        """
        x0, y0 = center
        h, w = frame.shape[:2]
        if not (0 <= x0 < w and 0 <= y0 < h):
            return frame

        # Clamp and norm
        val = float(np.clip(value_deg, min_deg, max_deg))
        # Map value to angle on screen: left = 180°, right = 0°, top = 90°
        # We'll render arc from 180° to 0° (OpenCV uses degrees, 0° = +x axis, counter-clockwise positive)
        def val_to_screen_deg(v):
            t = (v - min_deg) / (max_deg - min_deg) 
            return 180.0 * (1.0 - t)

        thickness_arc = 10
        cv2.ellipse(frame, (x0, y0), (radius, radius),
                    angle=0, startAngle=180, endAngle=0,
                    color=color_arc, thickness=thickness_arc, lineType=cv2.LINE_AA)

        major_ticks = 5
        minor_per_major = 4
        for i in range(major_ticks + 1):
            scr_deg = 180.0 - (180.0 * i / major_ticks)
            ang = np.deg2rad(scr_deg)
            r1 = radius - 2
            r2 = radius - 16
            x1 = int(x0 + r1 * np.cos(ang))
            y1 = int(y0 - r1 * np.sin(ang))
            x2 = int(x0 + r2 * np.cos(ang))
            y2 = int(y0 - r2 * np.sin(ang))
            cv2.line(frame, (x1, y1), (x2, y2), color_tick, 2, cv2.LINE_AA)

            # Minor ticks between majors
            if i < major_ticks:
                for m in range(1, minor_per_major):
                    frac = (i + m / minor_per_major) / major_ticks
                    scr_deg_m = 180.0 - 180.0 * frac
                    angm = np.deg2rad(scr_deg_m)
                    rm1 = radius - 2
                    rm2 = radius - 10
                    xm1 = int(x0 + rm1 * np.cos(angm))
                    ym1 = int(y0 - rm1 * np.sin(angm))
                    xm2 = int(x0 + rm2 * np.cos(angm))
                    ym2 = int(y0 - rm2 * np.sin(angm))
                    cv2.line(frame, (xm1, ym1), (xm2, ym2), color_tick, 1, cv2.LINE_AA)

        # Needle
        scr_deg_val = val_to_screen_deg(val)
        angv = np.deg2rad(scr_deg_val)
        r_need = radius - 20
        xn = int(x0 + r_need * np.cos(angv))
        yn = int(y0 - r_need * np.sin(angv))
        cv2.line(frame, (x0, y0), (xn, yn), color_needle, 3, cv2.LINE_AA)
        cv2.circle(frame, (x0, y0), 5, color_needle, -1, cv2.LINE_AA)

    def get_inplane_angle(self, rvec):
        """Return marker orientation about camera Z-axis in degrees [-180, 180]."""
        R, _ = cv2.Rodrigues(rvec)
        angle_rad = math.atan2(R[1,0], R[0,0])
        angle_deg = math.degrees(angle_rad)
        return angle_deg # [-180, 180]

    # Estimate distance (z) from marker to cam
    def get_distance(self, c):
        TL, TR, BR, BL = c

        # Average side length in pixels
        side_px = (np.linalg.norm(TR-TL) + np.linalg.norm(TR-BR) +
                np.linalg.norm(BR-BL) + np.linalg.norm(BL-TL)) / 4.0

        fx = self.K[0,0]  # Focal length in pixels
        # Pinhole model: size_in_pixels = (f * real_size) / Z
        Z = (fx * self.MARKER_SIZE_M) / side_px
        return Z * 1.39 # 1.39 determined experimentally
    
    def get_degree_in_game(self, rvec, tvec, frame):
        point_3d = np.array([[0, 0, 0]], dtype=np.float32)  # marker center
        point_2d, _ = cv2.projectPoints(point_3d, rvec, tvec, self.K, self.dist)

        x, y = point_2d.ravel()
        cv2.circle(frame, (int(x), int(y)), 20, (0, 0, 255), 10)
        
        # Get ratio of x pos / total width, convert to a degree by doing ratio * 180
        # Clamp x position to screen bounds to avoid invalid degrees
        x_clamped = max(0, min(self.WIDTH, x))
        self.in_game_deg = (x_clamped / self.WIDTH) * 180
        
        # Convert to range for gauge display (-90 to +90)
        gauge_deg = self.in_game_deg - 90
        self.draw_semi_gauge(frame, value_deg=gauge_deg)
        
    def get_measurements(self, frame):
        corners, ids, _ = self.detector.detectMarkers(frame)

        if ids is not None and len(ids) > 0:
            self.aruco.drawDetectedMarkers(frame, corners, ids)

            for c in corners:
                c = c.reshape(-1, 2).astype(np.float32)
                # rvec is rotation vector (stores rotation of aruco relative to cam), tvec is translation vector relative to camera
                ok_pnp, rvec, tvec = cv2.solvePnP(self.objp, c, self.K, self.dist, flags=cv2.SOLVEPNP_IPPE_SQUARE)
                if ok_pnp:  # Only process if pose estimation was successful
                    self.get_degree_in_game(rvec, tvec, frame)
        else:
            # No markers detected, maintain current position and draw gauge
            gauge_deg = self.in_game_deg - 90
            self.draw_semi_gauge(frame, value_deg=gauge_deg)
                
        return frame

if __name__ == "__main__":
    estimator = Estimate()
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    kernel = np.ones((5,5), np.uint8)
    
    while True:
        _, frame = cap.read()
        frame = cv2.flip(frame, 1)
        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
        frame = estimator.get_measurements(frame)

        cv2.imshow("Cam Feed", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()