import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

class Viewer:
    """
    Window with:
      (Top)  Circle geometry (your original visual)
      (Bottom) Live plot of last 5 Y pixel coords from a deque of (x,y)
    """
    def __init__(self, title="Circle Geometry", img_width=1280, img_height=720):
        self.img_width = img_width
        self.img_height = img_height

        plt.ion()
        self.fig = plt.figure(figsize=(7, 8))
        self.fig.canvas.manager.set_window_title(title)

        gs = GridSpec(2, 1, height_ratios=[3, 1], hspace=0.35, figure=self.fig)

        # --- Top axes: geometry ---
        self.ax = self.fig.add_subplot(gs[0, 0])
        self.ax.set_aspect('equal', 'box')
        self.ax.grid(True, linestyle='--', alpha=0.3)

        self.circle_artist = None
        self.arc_line,   = self.ax.plot([], [], lw=2, color='tab:cyan')
        self.chord_line, = self.ax.plot([], [], lw=3, color='tab:red')
        self.P_scatter = self.ax.scatter([], [], s=60, color='tab:red',  zorder=3, label='P(d,0)')
        self.E_scatter = self.ax.scatter([], [], s=60, color='tab:cyan', zorder=3, label='E (arc end)')
        self.angle_arc, = self.ax.plot([], [], lw=2, color='tab:green')
        self.text_handle = self.ax.text(0.02, 0.98, "", transform=self.ax.transAxes,
                                        ha='left', va='top', fontsize=10)
        self.ax.legend(loc='upper right')

        # --- Bottom axes: Y tracking (last 5 samples) ---
        self.ax_y = self.fig.add_subplot(gs[1, 0])
        self.ax_y.set_title("Last 5 Y pixel coords (image space)")
        self.ax_y.set_xlabel("sample (0 = oldest, 4 = newest)")
        self.ax_y.set_ylabel("y (pixels)")
        self.ax_y.set_xlim(-0.2, 4.2)
        self.ax_y.set_ylim(0, self.img_height)
        self.ax_y.grid(True, linestyle='--', alpha=0.4)
        self.ax_y.invert_yaxis()  # smaller y (up on screen) appears higher on the plot
        (self.y_line,) = self.ax_y.plot([], [], marker="o")
        (self.y_last,) = self.ax_y.plot([], [], marker="o", lw=0, ms=8)  # highlight newest
        self._y_indices = np.arange(5)

        self.show = True # set True to make update() call pause()

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
        ys = np.array(ys, dtype=float)
        return ys

    def _update_y_trend(self, track_coords):
        ys = self._pad_last5_y(track_coords)
        self.y_line.set_data(self._y_indices, ys)

        # highlight newest non-NaN point
        finite = np.isfinite(ys)
        if np.any(finite):
            newest_idx = np.max(np.where(finite)[0])
            self.y_last.set_data([newest_idx], [ys[newest_idx]])
        else:
            self.y_last.set_data([], [])

    def update(self, r, d, arc_deg, track_coords=None):
        # --- compute geometry ---
        theta_deg = self._end_angle_from_arc_deg(arc_deg)
        theta = math.radians(theta_deg)
        Ex, Ey = r*math.cos(theta), r*math.sin(theta)
        Px, Py = d, 0.0
        alpha = math.atan2(Ey - Py, Ex - Px)
        alpha_deg = math.degrees(alpha)

        # ----- draw circle -----
        if self.circle_artist is not None:
            self.circle_artist.remove()
        self.circle_artist = plt.Circle((0,0), r, fill=False, lw=2, color='k')
        self.ax.add_artist(self.circle_artist)

        # axes lines
        self.ax.axhline(0, color='0.7', lw=1)
        self.ax.axvline(0, color='0.7', lw=1)

        # arc from TOP to E
        theta_top = math.radians(90.0)
        thetas = np.linspace(theta_top, theta, 150)
        self.arc_line.set_data(r*np.cos(thetas), r*np.sin(thetas))

        # chord P->E
        self.chord_line.set_data([Px, Ex], [Py, Ey])

        # points
        self.P_scatter.set_offsets(np.array([[Px, Py]]))
        self.E_scatter.set_offsets(np.array([[Ex, Ey]]))

        # small angle marker at P
        rad = 0.2 * r
        phis = np.linspace(0.0, alpha, 64)
        ang_x = Px + rad*np.cos(phis)
        ang_y = Py + rad*np.sin(phis)
        self.angle_arc.set_data(ang_x, ang_y)

        # annotation
        self.text_handle.set_text(
            f"r = {r:.3f}\n"
            f"d = {d:.3f}\n"
            f"arc_deg (from top) = {arc_deg:.1f}°\n"
            f"E = ({Ex:.3f}, {Ey:.3f})\n"
            f"alpha = {alpha_deg:+.2f}°"
        )

        # view limits
        m = r * 1.25
        self.ax.set_xlim(-m, m)
        self.ax.set_ylim(-m, m)

        # --- update Y trend if provided ---
        if track_coords is not None:
            self._update_y_trend(track_coords)

        # redraw
        self.fig.canvas.draw_idle()
        if self.show:
            plt.pause(0.001)

        return alpha, (Ex, Ey)
