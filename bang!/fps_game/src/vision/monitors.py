import math
import numpy as np

class Viewer:
    """
    Headless (no-plot) geometry helper.

    - update(r, d, arc_deg, track_coords=None) computes:
        * E = (Ex, Ey) on the circle of radius r given arc from TOP
        * alpha = angle at P(d,0) toward E   (returned in radians)
      Returns: (alpha, (Ex, Ey))

    - If track_coords is provided (iterable of (x,y)),
      stores the last 5 y-values (image-space) in self.last5_y
      and the newest valid index in self.last5_y_newest_idx.
    """

    def __init__(self, title="Circle Geometry", img_width=1280, img_height=720):
        self.img_width = img_width
        self.img_height = img_height

        # Y-tracking buffers (no plotting)
        self._y_indices = np.arange(5)
        self.last5_y = np.array([np.nan]*5, dtype=float)
        self.last5_y_newest_idx = None  # 0..4 or None if no data

    @staticmethod
    def _end_angle_from_arc_deg(arc_deg):
        # arc measured from TOP (0,r); convert to standard angle from +x axis CCW
        return 90.0 - arc_deg

    @staticmethod
    def _pad_last5_y(track_coords):
        """Extract last 5 y's, pad front with NaNs to length 5."""
        buf = list(track_coords)[-5:]
        ys = [p[1] for p in buf]
        pad = 5 - len(ys)
        if pad > 0:
            ys = [np.nan]*pad + ys
        return np.asarray(ys, dtype=float)

    def _update_y_trend(self, track_coords):
        ys = self._pad_last5_y(track_coords)
        self.last5_y = ys

        finite = np.isfinite(ys)
        if np.any(finite):
            self.last5_y_newest_idx = int(np.max(np.where(finite)[0]))
        else:
            self.last5_y_newest_idx = None

    def update(self, r, d, arc_deg, track_coords=None):
        # --- compute geometry only (no plots) ---
        theta_deg = self._end_angle_from_arc_deg(arc_deg)
        theta = math.radians(theta_deg)

        Ex, Ey = r*math.cos(theta), r*math.sin(theta)
        Px, Py = d, 0.0

        alpha = math.atan2(Ey - Py, Ex - Px)  # radians

        # Optional: update y-trend buffers (no plots)
        if track_coords is not None:
            self._update_y_trend(track_coords)

        # Return same outputs you used before
        return alpha, (Ex, Ey)
