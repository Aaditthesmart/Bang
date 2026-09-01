import cv2
import numpy as np
import math
from collections import deque
import json
import os
from src.vision.monitors import Viewer
import mediapipe as mp

class Estimate:
    MARKER_SIZE_M = 0.03    
    WIDTH = 1500
    HEIGHT = 750
    
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
   
        # Initialize all tracking variables
        self.d = 0
        self.alpha = 0
        self.d_to_cam = 1.5  # Initialize with default distance instead of 0
        self.last_valid_distance = 1.5  # Store the last valid distance measurement
        self.angle = 0  # Rotation angle for left/right gun rotation
        
        # Reload detection
        self.reloading = False
        self.reload_cooldown = 0  # Cannot reload consecutively 
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5
        )
        self.finger_names = ["thumb", "index", "middle", "ring", "pinky"]
        
        self.viewer = Viewer("Degree and Pos Visualizer")
        
        # Detect shoot (up/down recoil motion)
        self.track_coords = deque(maxlen=5)
        self.shooting = False
        self.shoot_cooldown = 0

    def get_inplane_angle(self, rvec):
        """Return marker orientation about camera Z-axis in degrees [-180, 180]."""
        R, _ = cv2.Rodrigues(rvec)
        angle_rad = math.atan2(R[1,0], R[0,0])
        angle_deg = math.degrees(angle_rad)
        return angle_deg  # [-180, 180]

    def get_distance(self, c):
        """Estimate distance (z) from marker to camera"""
        TL, TR, BR, BL = c

        # Average side length in pixels
        side_px = (np.linalg.norm(TR-TL) + np.linalg.norm(TR-BR) +
                np.linalg.norm(BR-BL) + np.linalg.norm(BL-TL)) / 4.0

        fx = self.K[0,0]  # Focal length in pixels
        # Pinhole model: size_in_pixels = (f * real_size) / Z
        Z = (fx * self.MARKER_SIZE_M) / side_px
        return Z * 1.39  # 1.39 determined experimentally
    
    def get_degree_in_game(self, rvec, tvec, frame, ok_pnp):
        """Calculate weapon position and orientation from ArUco marker"""
        point_3d = np.array([[0, 0, 0]], dtype=np.float32)  # marker center
        point_2d, _ = cv2.projectPoints(point_3d, rvec, tvec, self.K, self.dist)

        x, y = point_2d.ravel()
        cv2.circle(frame, (int(x), int(y)), 20, (0, 0, 255), 10)
        
        # Get ratio of x pos / total width, convert to a degree by doing ratio * 180
        artistic = 1.3  # This factor makes it so the gun doesn't actually move that much
        r = 0.4  # Radius
        self.d = (x / self.WIDTH * r - r / 2) * artistic
        arc_deg = x / self.WIDTH * 180 - 90
    
        self.alpha, _ = self.viewer.update(r=0.4, d=self.d, arc_deg=arc_deg, track_coords=self.track_coords)
    
    def detect_left_fist(self, frame, aruco_central_y):
        """
        Detects if the LEFT hand is making a fist.
        Also draws lines for visualization:
        - palm-center to each fingertip (green if curled, red if not)
        - fingertip-to-fingertip across the knuckles (green if compact)
        Returns True if left hand fist is detected, False otherwise.
        """
        def distance(p1, p2):
            return math.hypot(p1.x - p2.x, p1.y - p2.y)

        def to_px(pt, w, h):
            return (int(pt.x * w), int(pt.y * h))

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        if not results.multi_hand_landmarks:
            return False

        h, w = frame.shape[:2]
        for hand_lms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            if handedness.classification[0].label != "Left":
                continue

            h, w = frame.shape[:2]
            lm = hand_lms.landmark
            avg_y = int(round(np.mean([p.y * h for p in lm])))
            
            palm_center = lm[9]

            # Distances fingertip -> palm and PIP -> palm for curl ratios
            thumb_to_palm  = distance(lm[4],  palm_center);  thumb_ref  = distance(lm[3],  palm_center)
            index_to_palm  = distance(lm[8],  palm_center);  index_ref  = distance(lm[6],  palm_center)
            middle_to_palm = distance(lm[12], palm_center);  middle_ref = distance(lm[10], palm_center)
            ring_to_palm   = distance(lm[16], palm_center);  ring_ref   = distance(lm[14], palm_center)
            pinky_to_palm  = distance(lm[20], palm_center);  pinky_ref  = distance(lm[18], palm_center)

            # Curl ratios (< threshold means curled)
            curl_threshold = 1.3
            curls = [
                thumb_to_palm  / (thumb_ref  + 1e-6) < curl_threshold,
                index_to_palm  / (index_ref  + 1e-6) < curl_threshold,
                middle_to_palm / (middle_ref + 1e-6) < curl_threshold,
                ring_to_palm   / (ring_ref   + 1e-6) < curl_threshold,
                pinky_to_palm  / (pinky_ref  + 1e-6) < curl_threshold
            ]

            # Fingertip compactness
            tips = [lm[4], lm[8], lm[12], lm[16], lm[20]]
            fingertip_distances = [
                distance(lm[4], lm[8]),
                distance(lm[8], lm[12]),
                distance(lm[12], lm[16]),
                distance(lm[16], lm[20]),
            ]
            avg_fingertip_distance = sum(fingertip_distances) / len(fingertip_distances)
            compact_threshold = 0.08
            compact = avg_fingertip_distance < compact_threshold

            # --------- DRAWING LINES ----------
            # 1) Palm-center to each fingertip (green if curled, else red)
            colors = [(0,255,0) if c else (0,0,255) for c in curls]  # BGR
            palm_px = to_px(palm_center, w, h)
            for tip, color in zip(tips, colors):
                cv2.line(frame, palm_px, to_px(tip, w, h), color, 2, cv2.LINE_AA)
                cv2.circle(frame, to_px(tip, w, h), 4, color, -1, cv2.LINE_AA)

            # 2) Fingertip-to-fingertip chain (green if compact, else red)
            chain_color = (0,255,0) if compact else (0,0,255)
            for a, b in zip(tips[:-1], tips[1:]):
                cv2.line(frame, to_px(a, w, h), to_px(b, w, h), chain_color, 2, cv2.LINE_AA)

            # Optional: draw palm point
            cv2.circle(frame, palm_px, 5, (255,255,255), -1, cv2.LINE_AA)

            # Decision of reloading (fist + above)
            if sum(curls) >= 4 and compact and avg_y < aruco_central_y:
                return True

        return False

    def is_shooting(self):
        """
        VERY SENSITIVE recoil detector.
        Fires on a small, fast y 'kick' (up then down) with only mild x stability.
        Assumes self.track_coords holds the last (x, y) centers.
        """
        n = len(self.track_coords)
        if n < 4:
            return False

        pts = list(self.track_coords)[-5:]  # up to last 5
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        # --- Relaxed X stability (allow small pan) ---
        if (max(xs) - min(xs)) > 35:   # was much stricter before
            return False

        # --- Sensitivity knobs (tiny thresholds) ---
        up_step_thresh   = 3.0   # min single-frame "up" change (y decreases)
        down_step_thresh = 3.0   # min single-frame "down" change (y increases)
        amp_min          = 6.0   # overall peak-to-trough needed

        # Compute first differences
        dys = [ys[i+1] - ys[i] for i in range(len(ys)-1)]  # + = down, - = up

        # Look for an UP step followed soon by a DOWN step
        up_idxs   = [i for i, dy in enumerate(dys) if dy < -up_step_thresh]
        down_idxs = [i for i, dy in enumerate(dys) if dy >  down_step_thresh]

        if not up_idxs or not down_idxs:
            return False

        # Ensure order: an up happens before a down within the recent window
        k = min(up_idxs)
        m_candidates = [m for m in down_idxs if m > k]
        if not m_candidates:
            return False

        # Amplitude check around the up→down region
        m = min(m_candidates)
        seg = ys[k:(m+2)]  # cover points affected by dy[k]..dy[m]
        if len(seg) < 2:
            return False

        # We want the segment to have a clear local minimum (kick up) then rise back
        ymin = min(seg); ymax = max(seg)
        if (ymax - ymin) < amp_min:
            return False

        # Extra forgiving shape check: min should be before the end of the segment
        argmin = seg.index(ymin)
        if argmin == len(seg) - 1:
            return False

        return True
    
    def get_weapon_transform_data(self):
        """
        Return all weapon transform data needed by the game.
        This includes position offset, orientation, rotation angle, and distance.
        """
        return {
            'position_offset': self.d,           # Horizontal position offset
            'orientation_alpha': self.alpha,     # Orientation angle in radians
            'degree': 90.0,                      # Legacy compatibility
            'rotation_angle': self.angle,        # Left/right rotation of gun
            'distance_to_cam': self.d_to_cam,    # Distance from camera (now persistent)
            'shooting': self.shooting,           # Shooting state
            'reloading': self.reloading          # Reloading state
        }

    def get_measurements(self, frame):
        corners, ids, _ = self.detector.detectMarkers(frame)
        
        if ids is not None and len(ids) > 0:
            self.aruco.drawDetectedMarkers(frame, corners, ids)
            for c in corners:
                c = c.reshape(-1, 2).astype(np.float32)
                # rvec is rotation vector, tvec is translation vector relative to camera
                ok_pnp, rvec, tvec = cv2.solvePnP(self.objp, c, self.K, self.dist, flags=cv2.SOLVEPNP_IPPE_SQUARE)
                
                # Angles and orientation
                self.get_degree_in_game(rvec, tvec, frame, ok_pnp)
                
                # Distance to cam - only update if valid
                new_distance = self.get_distance(c)
                if new_distance > 0:
                    self.d_to_cam = new_distance
                    self.last_valid_distance = new_distance
                # If new_distance is 0 or negative, keep the current d_to_cam value
                
                # Rotation angle (left/right gun rotation)
                self.angle = self.get_inplane_angle(rvec)
                
                # Label aruco
                xs, ys = c[:,0], c[:,1]
                x1, y1, x2, y2 = map(int, [xs.min(), ys.min(), xs.max(), ys.max()])
                tx, ty = int((x1+x2)/2), max(0, y1-6)
                txt = f"{self.angle:+.1f}°"
                sz = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.putText(frame, txt, (tx - sz[0]//2, ty + sz[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.LINE_AA)
                
                central_y = int((y1 + y2) / 2)
                
                # Track coordinates for shooting detection
                self.track_coords.append((tx, central_y))
                
                # Shooting detection
                if self.shooting:
                    self.shooting = False
                if self.shoot_cooldown == 0:
                    self.shooting = self.is_shooting()
                    if self.shooting:
                        self.shoot_cooldown = 5
                
                # Reloading detection
                if self.reloading:
                    self.reloading = False
                if self.reload_cooldown == 0:
                    self.reloading = self.detect_left_fist(frame, central_y)
                    if self.reloading:
                        self.reload_cooldown = 30
        else:
            # No marker detected - keep the last valid distance instead of setting to 0
            # self.d_to_cam remains at its last valid value
            pass

        return frame

if __name__ == "__main__":
    estimator = Estimate()
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while True:
        _, frame = cap.read()
        frame = cv2.flip(frame, 1)
        frame = estimator.get_measurements(frame)
        
        # Update cooldowns
        if estimator.reload_cooldown > 0:
            estimator.reload_cooldown -= 1
        cv2.putText(frame, f'Reload cooldown {estimator.reload_cooldown}', 
                   (10, 60), cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
        
        if estimator.shoot_cooldown > 0:
            estimator.shoot_cooldown -= 1
        cv2.putText(frame, f'Shooting cooldown {estimator.shoot_cooldown}', 
                   (10, 110), cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
        
        # Display weapon transform data
        data = estimator.get_weapon_transform_data()
        cv2.putText(frame, f"Distance: {data['distance_to_cam']:.2f}m", 
                   (10, 160), cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Shooting: {data['shooting']}", 
                   (10, 210), cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Reloading: {data['reloading']}", 
                   (10, 260), cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
        
        cv2.imshow("Cam Feed", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()