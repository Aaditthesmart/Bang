import math
import numpy as np
import matplotlib.pyplot as plt
import threading

class GeometryViewer:
    """
    Interactive window to visualize:
      - Circle centered at (0,0) with radius r
      - Arc starting at top (0,r) spanning arc_deg (deg)
      - Point P = (d, 0) on the diameter
      - Chord from P to arc end E
      - Angle alpha at P (to the +x diameter)
    """
    def __init__(self, title="Circle Geometry"):
        self.title = title
        self.is_main_thread = threading.current_thread() is threading.main_thread()
        
        # Only initialize matplotlib if we're on the main thread
        if self.is_main_thread:
            try:
                plt.ion()
                self.fig, self.ax = plt.subplots(figsize=(6,6))
                self.fig.canvas.manager.set_window_title(title)
                self.ax.set_aspect('equal', 'box')
                self.ax.grid(True, linestyle='--', alpha=0.3)
                self.circle_artist = None
                self.arc_line, = self.ax.plot([], [], lw=2, color='tab:cyan')
                self.chord_line, = self.ax.plot([], [], lw=3, color='tab:red')
                self.P_scatter = self.ax.scatter([], [], s=60, color='tab:red', zorder=3, label='P(d,0)')
                self.E_scatter = self.ax.scatter([], [], s=60, color='tab:cyan', zorder=3, label='E (arc end)')
                self.angle_arc, = self.ax.plot([], [], lw=2, color='tab:green')
                self.text_handle = self.ax.text(0.02, 0.98, "", transform=self.ax.transAxes,
                                                ha='left', va='top', fontsize=10)
                self.ax.legend(loc='upper right')
                self.matplotlib_available = True
                print(f"GeometryViewer: Matplotlib GUI initialized on main thread")
            except Exception as e:
                print(f"GeometryViewer: Failed to initialize matplotlib GUI: {e}")
                self.matplotlib_available = False
        else:
            self.matplotlib_available = False
            print(f"GeometryViewer: Running on background thread - GUI disabled, calculations only")

    @staticmethod
    def _end_angle_from_arc_deg(arc_deg):
        # arc_deg is the arc measured from the TOP (0,r).
        # Convert to standard angle theta (deg) from +x axis CCW:
        # TOP is 90°, moving CW decreases angle -> theta = 90 - arc_deg
        return 90.0 - arc_deg

    def calculate_geometry(self, r, d, arc_deg):
        """Calculate geometry values without updating display - thread-safe"""
        # Compute arc end E
        theta_deg = self._end_angle_from_arc_deg(arc_deg)
        theta = math.radians(theta_deg)
        Ex, Ey = r*math.cos(theta), r*math.sin(theta)

        # Point P on diameter
        Px, Py = d, 0.0

        # Angle alpha at P relative to +x axis
        alpha = math.atan2(Ey - Py, Ex - Px)          # radians
        alpha_deg = math.degrees(alpha)
        
        return alpha, (Ex, Ey), alpha_deg

    def update(self, r, d, arc_deg):
        """Update geometry calculations and optionally display if on main thread"""
        # Always calculate the geometry (this is thread-safe)
        alpha, end_point, alpha_deg = self.calculate_geometry(r, d, arc_deg)
        Ex, Ey = end_point
        Px, Py = d, 0.0
        
        # Only update display if matplotlib is available and we're on main thread
        if self.matplotlib_available and self.is_main_thread:
            try:
                self._update_display(r, d, arc_deg, alpha, alpha_deg, Ex, Ey, Px, Py)
            except Exception as e:
                print(f"GeometryViewer: Display update failed: {e}")
                # If display fails, disable it for future calls
                self.matplotlib_available = False
        
        return alpha, (Ex, Ey)
    
    def _update_display(self, r, d, arc_deg, alpha, alpha_deg, Ex, Ey, Px, Py):
        """Update the matplotlib display - only call from main thread"""
        theta_deg = self._end_angle_from_arc_deg(arc_deg)
        theta = math.radians(theta_deg)
        
        # ----- draw circle -----
        if self.circle_artist is not None:
            self.circle_artist.remove()
        self.circle_artist = plt.Circle((0,0), r, fill=False, lw=2, color='k')
        self.ax.add_artist(self.circle_artist)

        # Axes lines
        self.ax.axhline(0, color='0.7', lw=1)
        self.ax.axvline(0, color='0.7', lw=1)

        # ----- draw arc from TOP to E -----
        theta_top = math.radians(90.0)
        thetas = np.linspace(theta_top, theta, 150)
        self.arc_line.set_data(r*np.cos(thetas), r*np.sin(thetas))

        # ----- chord P -> E -----
        self.chord_line.set_data([Px, Ex], [Py, Ey])

        # ----- scatter points -----
        self.P_scatter.set_offsets(np.array([[Px, Py]]))
        self.E_scatter.set_offsets(np.array([[Ex, Ey]]))

        # ----- small angle marker at P -----
        # draw an arc from 0 to alpha around P
        rad = 0.2 * r
        phis = np.linspace(0.0, alpha, 64)
        ang_x = Px + rad*np.cos(phis)
        ang_y = Py + rad*np.sin(phis)
        self.angle_arc.set_data(ang_x, ang_y)

        # ----- annotate -----
        self.text_handle.set_text(
            f"r = {r:.3f}\n"
            f"d = {d:.3f}\n"
            f"arc_deg (from top) = {arc_deg:.1f}°\n"
            f"E = ({Ex:.3f}, {Ey:.3f})\n"
            f"alpha = {alpha_deg:+.2f}°"
        )

        # ----- view limits -----
        m = r * 1.25
        self.ax.set_xlim(-m, m)
        self.ax.set_ylim(-m, m)

        # Use draw_idle instead of draw for better performance and thread safety
        self.fig.canvas.draw_idle()
        
        # Remove the plt.pause call that was causing threading issues
        # plt.pause(0.001)  # This was the problematic line
    
    def close(self):
        """Close the matplotlib window if it exists"""
        if self.matplotlib_available and hasattr(self, 'fig'):
            try:
                plt.close(self.fig)
                print("GeometryViewer: Matplotlib window closed")
            except Exception as e:
                print(f"GeometryViewer: Error closing matplotlib window: {e}")