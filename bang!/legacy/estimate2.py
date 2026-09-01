import cv2
import numpy as np
import math
from collections import deque
import json
import os
from src.vision.geometry_viewer import GeometryViewer

class Estimate:
    MARKER_SIZE_M = 0.03
    WIDTH = 1280
    HEIGHT = 720
    
    def __init__(self):
        self.dist = np.array([0, 0, 0, 0, 0], dtype=np.float64)
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
        self.d, self.alpha = 0, 0
        
        self.viewer = GeometryViewer("Degree and Pos Visualizer")

    def draw_semi_gauge(
        self,
        frame,
        center=(180, 500),      # circle center in pixels
        radius_px=120,          # circle radius in pixels (for drawing)
        r_world=0.4,            # your circle radius r (same units as d)
        d_world=0.0,            # your d (can be +/-)
        arc_deg=0.0,            # arc angle in DEGREES from the TOP of circle; cw positive if you used x/WIDTH*180 - 90
        alpha_rad=0.0,          # the angle at P to the diameter (in RADIANS)
        color_circle=(100,100,100),
        color_arc=(80,180,255),
        color_line=(0,0,255),
        color_angle=(0,255,0)
    ):
        """
        Draw: semi-circle, the arc from top to arc_deg, point P at (d,0),
        the chord from P to the arc end E, and the small angle alpha at P.

        Geometry:
        - Circle center at 'center' (pixels), radius 'radius_px' (pixels).
        - World r_world, d_world only used to place P along the diameter:
            P_x = center_x + (d/r)*radius_px, P_y = center_y.
        - Arc starts at the TOP of the circle; arc_deg ∈ [-90, +90] like your mapping.
        """
        import numpy as np
        import cv2
        x0, y0 = center

        # --- helper: map arc_deg in [-90..+90] to screen angle in [180..0]
        # (OpenCV ellipse: 0° = +x axis, CCW positive; top is 90°)
        t = (arc_deg - (-90.0)) / (180.0)      # normalize -90..+90 to 0..1
        scr_end_deg = 180.0 * (1.0 - t)        # 180..0
        scr_end_deg = float(np.clip(scr_end_deg, 0.0, 180.0))

        # --- circle outline (semi only)
        cv2.ellipse(frame, (x0, y0), (radius_px, radius_px),
                    angle=0, startAngle=180, endAngle=0,
                    color=color_circle, thickness=2, lineType=cv2.LINE_AA)

        # --- draw the arc from top (180→90) continuing to scr_end_deg
        # Split in two segments to handle left/right halves cleanly
        if scr_end_deg <= 90:
            # left half (180→90) then (90→scr_end_deg)
            cv2.ellipse(frame, (x0, y0), (radius_px, radius_px),
                        0, 180, 90, color_arc, 4, cv2.LINE_AA)
            cv2.ellipse(frame, (x0, y0), (radius_px, radius_px),
                        0, 90, scr_end_deg, color_arc, 4, cv2.LINE_AA)
        else:
            # arc goes only within left half
            cv2.ellipse(frame, (x0, y0), (radius_px, radius_px),
                        0, 180, scr_end_deg, color_arc, 4, cv2.LINE_AA)

        # --- compute arc end point E in pixels from screen angle
        ang = np.deg2rad(scr_end_deg)
        Ex = int(round(x0 + radius_px * np.cos(ang)))
        Ey = int(round(y0 - radius_px * np.sin(ang)))  # y down

        # --- compute P=(d,0) mapped to pixels along the diameter
        # scale d/r by radius_px
        Px = int(round(x0 + (d_world / (r_world if r_world != 0 else 1e-6)) * radius_px))
        Py = y0

        # --- draw chord P->E
        cv2.line(frame, (Px, Py), (Ex, Ey), color_line, 3, cv2.LINE_AA)
        cv2.circle(frame, (Px, Py), 5, color_line, -1, cv2.LINE_AA)
        cv2.circle(frame, (Ex, Ey), 5, color_line, -1, cv2.LINE_AA)

        # --- draw small angle alpha at P, measured from the diameter (x-axis) toward chord
        # alpha_rad is in standard math coords; image y is down → use y0 - sin()
        small_r = max(8, int(0.12 * radius_px))
        # determine direction sign from alpha
        steps = 24
        phis = np.linspace(0, alpha_rad, steps)  # 0 is along +x; positive alpha is CCW (up)
        arc_pts = np.stack([
            Px + small_r * np.cos(phis),
            Py - small_r * np.sin(phis)  # y down
        ], axis=1).astype(np.int32)
        if len(arc_pts) >= 2:
            cv2.polylines(frame, [arc_pts], isClosed=False, color=color_angle, thickness=2, lineType=cv2.LINE_AA)
        cv2.circle(frame, (Px, Py), 3, color_angle, -1, cv2.LINE_AA)

        return frame


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
    
    def get_degree_in_game(self, rvec, tvec, frame, ok_pnp):
        point_3d = np.array([[0, 0, 0]], dtype=np.float32)  # marker center
        point_2d, _ = cv2.projectPoints(point_3d, rvec, tvec, self.K, self.dist)

        x, y = point_2d.ravel()
        cv2.circle(frame, (int(x), int(y)), 20, (0, 0, 255), 10)
        
        # Get ratio of x pos / total width, convert to a degree by doing ratio * 180
        artistic = 0.80 # This factor makes it so the gun doesn't actually move that much, for better artisitc value
        r = 0.4 # Radius
        self.d = (x / self.WIDTH * r - r / 2) * artistic
        arc_deg = x / self.WIDTH * 180 - 90
      
        self.alpha, _ = self.viewer.update(r=0.4, d=self.d, arc_deg=arc_deg)

    def get_measurements(self, frame):
        corners, ids, _ = self.detector.detectMarkers(frame)
        
        if ids is not None and len(ids) > 0:
            self.aruco.drawDetectedMarkers(frame, corners, ids)
            for c in corners:
                c = c.reshape(-1, 2).astype(np.float32)
                # rvec is rotation vector (stores rotation of aruco relative to cam), tvec is translation vector relative to camera
                ok_pnp, rvec, tvec = cv2.solvePnP(self.objp, c, self.K, self.dist, flags=cv2.SOLVEPNP_IPPE_SQUARE)
                self.get_degree_in_game(rvec, tvec, frame, ok_pnp)
                
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
