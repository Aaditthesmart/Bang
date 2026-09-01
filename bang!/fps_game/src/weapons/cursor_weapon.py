import math
import numpy as np
import pygame
from OpenGL.GL import *

class QuaternionWeapon:
    """Weapon system that tracks ArUco marker position and orientation using geometry calculations"""
    
    def __init__(self, camera_pos=(0, 2, 5)):
        self.camera_pos = camera_pos
        
        # Base weapon offset from camera (will be modified by ArUco position)
        self.base_weapon_offset = np.array([0, -0.4, -2.0])  # Base offset from camera
        self.weapon_offset = self.base_weapon_offset.copy()  # Current actual offset
        
        self.cursor_world_pos = np.array([0, 0, -10])  # Default target position
        
        # Quaternion for weapon rotation (identity quaternion = no rotation)
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # [w, x, y, z]
        
        # Separate yaw and roll quaternions
        self.yaw_quaternion = np.array([1.0, 0.0, 0.0, 0.0])    # Rotation around Y-axis
        self.roll_quaternion = np.array([1.0, 0.0, 0.0, 0.0])   # Rotation around Z-axis
        
        # Separate yaw and roll angles (in radians)
        self.yaw_angle = 0.0    # Left/right rotation
        self.roll_angle = 0.0   # Roll rotation around forward axis
        
        # ArUco geometry data
        self.geometry_data = {
            'position_offset': 0.0,    # Horizontal position offset (d value)
            'orientation_alpha': 0.0,  # Orientation angle in radians (alpha) - primarily yaw
            'degree': 90.0,           # Original degree value for compatibility
            'rotation_angle': 0.0,    # Additional rotation angle - now contributes to roll
            'distance_to_cam': 1.5,   # Distance from camera (default 1.5m)
            'roll_offset': 0.0        # Roll offset (replaces pitch_offset)
        }
        
        # Default distance for when ArUco marker not visible
        self.default_distance_to_cam = 1.5
        
        # Target distance for aiming
        self.target_distance = 20.0
        
        # Weapon model specific offsets (based on your pistol GLB model)
        self.barrel_tip_offset = np.array([0.0, 0.2, -1.0])  # Tip is forward from weapon center
        
        # Position sensitivity multiplier
        self.position_sensitivity = 5.0  # How much the weapon position changes with ArUco movement
        
        # Distance-to-camera sensitivity (how much forward/back movement)
        self.distance_sensitivity = 0.3  # Multiplier for distance-based Z offset
        
        # Rotation sensitivity for left/right gun rotation
        self.rotation_sensitivity = 1.0
        
        # Roll sensitivity (replaces pitch sensitivity)
        self.roll_sensitivity = 1.0
        
        # Debug flag
        self._debug_counter = 0
        
    def update_full_aruco_data(self, full_data):
        """Update weapon using complete ArUco detection data including rotation and distance"""
        # Update all geometry data
        self.geometry_data.update(full_data)
        
        # Get values with defaults
        position_offset = full_data.get('position_offset', 0.0)
        orientation_alpha = full_data.get('orientation_alpha', 0.0)
        rotation_angle = full_data.get('rotation_angle', 0.0)
        distance_to_cam = full_data.get('distance_to_cam', self.default_distance_to_cam)
        roll_offset = full_data.get('roll_offset', 0.0)  # Get roll if provided
        
        # If distance is 0 (marker not visible), use default
        if distance_to_cam <= 0.01:
            distance_to_cam = self.default_distance_to_cam
        
        # Calculate weapon offset based on ArUco data
        self.weapon_offset = self.base_weapon_offset.copy()
        
        # Apply horizontal position offset (left-right movement based on d value)
        self.weapon_offset[0] += position_offset * self.position_sensitivity
        
        # Apply distance-based Z offset (forward-back movement)
        distance_offset = (distance_to_cam - self.default_distance_to_cam) * self.distance_sensitivity
        self.weapon_offset[2] += (distance_offset * 10) + 3
        
        # Calculate separate yaw and roll angles
        # Yaw: horizontal rotation (left-right aiming)
        self.yaw_angle = orientation_alpha
        
        # Roll: rotation around the forward axis (weapon twist)
        # Combine rotation_angle and roll_offset for roll control
        self.roll_angle = -(math.radians(rotation_angle) + roll_offset) * self.roll_sensitivity
        
        # Calculate target position using yaw only (no pitch, weapon aims horizontally)
        weapon_world_pos = np.array(self.camera_pos) + self.weapon_offset
        
        # Apply yaw to calculate horizontal target position
        target_x = weapon_world_pos[0] + (math.cos(self.yaw_angle) * self.target_distance)
        target_y = weapon_world_pos[1]  # Same height as weapon
        target_z = weapon_world_pos[2] - (math.sin(self.yaw_angle) * self.target_distance)
        
        self.cursor_world_pos = np.array([target_x, target_y, target_z])
        
        # Debug output
        self._debug_counter += 1
        if self._debug_counter % 30 == 0:  # Print every 0.5 seconds at 60 FPS
            print(f"Yaw: {math.degrees(self.yaw_angle):.1f}°, Roll: {math.degrees(self.roll_angle):.1f}°")
            print(f"Distance: {distance_to_cam:.2f}m, Pos offset: {position_offset:.3f}")
            print(f"Target: ({target_x:.1f}, {target_y:.1f}, {target_z:.1f})")
    
    def update_aruco_geometry(self, geometry_data):
        """Update weapon using geometry calculations from ArUco detection"""
        self.update_full_aruco_data(geometry_data)
    
    def update_aruco_position(self, degree):
        """Legacy method for backward compatibility - converts degree to geometry data"""
        degree = max(0.0, min(180.0, degree))
        horizontal_angle_deg = (degree - 90.0)
        horizontal_angle_rad = math.radians(horizontal_angle_deg)
        
        geometry_data = {
            'position_offset': horizontal_angle_rad * 0.1,
            'orientation_alpha': horizontal_angle_rad,
            'degree': degree,
            'rotation_angle': 0.0,
            'distance_to_cam': self.default_distance_to_cam,
            'roll_offset': 0.0
        }
        
        self.update_full_aruco_data(geometry_data)
    
    def calculate_weapon_orientation(self):
        """Calculate weapon orientation using separate yaw and roll quaternions"""
        weapon_pos = np.array(self.camera_pos) + self.weapon_offset
        
        direction = self.cursor_world_pos - weapon_pos
        direction_norm = np.linalg.norm(direction)
        
        if direction_norm < 0.001:
            self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])
            self.yaw_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
            self.roll_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
            return
            
        direction = direction / direction_norm
        
        # Calculate yaw (rotation around Y-axis)
        # Project direction onto XZ plane
        xz_direction = np.array([direction[0], 0, direction[2]])
        xz_norm = np.linalg.norm(xz_direction)
        
        if xz_norm > 0.001:
            xz_direction = xz_direction / xz_norm
            # Calculate yaw angle from forward vector [0, 0, -1]
            yaw = math.atan2(-xz_direction[0], -xz_direction[2])
            
            # Create yaw quaternion (rotation around Y-axis)
            half_yaw = yaw / 2.0
            self.yaw_quaternion = np.array([
                math.cos(half_yaw),
                0.0,
                math.sin(half_yaw),
                0.0
            ])
        else:
            self.yaw_quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        
        # Create roll quaternion (rotation around Z-axis)
        # Roll rotates the weapon around its forward-facing axis
        half_roll = self.roll_angle / 2.0
        self.roll_quaternion = np.array([
            math.cos(half_roll),
            0.0,
            0.0,
            math.sin(half_roll)
        ])
        
        # Combine quaternions: first yaw, then roll
        # Order matters! We apply yaw first, then roll around the new forward axis
        self.quaternion = self.multiply_quaternions(self.yaw_quaternion, self.roll_quaternion)
        
        # Normalize final quaternion
        quat_norm = np.linalg.norm(self.quaternion)
        if quat_norm > 0:
            self.quaternion = self.quaternion / quat_norm
    
    def multiply_quaternions(self, q1, q2):
        """Multiply two quaternions q1 * q2"""
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        return np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        ])
    
    def quaternion_to_matrix(self, q):
        """Convert quaternion to rotation matrix"""
        w, x, y, z = q
        
        norm = math.sqrt(w*w + x*x + y*y + z*z)
        if norm > 0:
            w, x, y, z = w/norm, x/norm, y/norm, z/norm
        
        matrix = np.array([
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z,     2*x*z + 2*w*y,     0],
            [2*x*y + 2*w*z,     1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x,     0],
            [2*x*z - 2*w*y,     2*y*z + 2*w*x,     1 - 2*x*x - 2*y*y, 0],
            [0,                 0,                 0,                 1]
        ])
        
        return matrix
    
    def get_weapon_tip_position(self):
        """Get the position of the weapon tip (barrel end) in world coordinates"""
        weapon_pos = np.array(self.camera_pos) + self.weapon_offset
        
        rotation_matrix = self.quaternion_to_matrix(self.quaternion)
        rotated_tip_offset = (rotation_matrix[:3, :3] @ self.barrel_tip_offset)
        
        tip_position = weapon_pos + rotated_tip_offset
        
        if hasattr(self, '_debug_tip_counter'):
            self._debug_tip_counter += 1
        else:
            self._debug_tip_counter = 0
            
        if self._debug_tip_counter % 60 == 0:
            print(f"Weapon tip position: ({tip_position[0]:.2f}, {tip_position[1]:.2f}, {tip_position[2]:.2f})")
            print(f"Yaw: {math.degrees(self.yaw_angle):.1f}°, Roll: {math.degrees(self.roll_angle):.1f}°")
        
        return tip_position
    
    def get_firing_direction(self):
        """Get the direction from weapon tip to ArUco target"""
        tip_pos = self.get_weapon_tip_position()
        direction = self.cursor_world_pos - tip_pos
        norm = np.linalg.norm(direction)
        if norm > 0:
            return direction / norm
        else:
            return np.array([0, 0, -1])
    
    def apply_weapon_transform(self):
        """Apply the weapon transformation for rendering"""
        glPushMatrix()
        
        weapon_world_pos = np.array(self.camera_pos) + self.weapon_offset
        glTranslatef(weapon_world_pos[0], weapon_world_pos[1], weapon_world_pos[2])
        
        rotation_matrix = self.quaternion_to_matrix(self.quaternion)
        gl_matrix = rotation_matrix.flatten(order='F')
        glMultMatrixf(gl_matrix.astype(np.float32))
        
        return True
    
    def update_with_aruco(self, degree):
        """Legacy update method for backward compatibility"""
        self.update_aruco_position(degree)
        self.calculate_weapon_orientation()
        
    def update_with_aruco_geometry(self, geometry_data):
        """Update method using geometry calculations"""
        self.update_full_aruco_data(geometry_data)
        self.calculate_weapon_orientation()
    
    def update(self):
        """Update weapon orientation - can be called without parameters for compatibility"""
        self.calculate_weapon_orientation()
        
    def get_cursor_world_position(self):
        """Get the current target world position for debugging"""
        return self.cursor_world_pos
    
    def get_aruco_degree(self):
        """Get the current ArUco degree for debugging"""
        return self.geometry_data.get('degree', 90.0)
    
    def get_geometry_data(self):
        """Get current geometry data for debugging"""
        return self.geometry_data.copy()
    
    def get_yaw_roll_angles(self):
        """Get current yaw and roll angles in degrees"""
        return {
            'yaw': math.degrees(self.yaw_angle),
            'roll': math.degrees(self.roll_angle)
        }
    
    def set_yaw_angle(self, yaw_degrees):
        """Manually set yaw angle (in degrees)"""
        self.yaw_angle = 1.5 * math.radians(yaw_degrees)
        print(f"Yaw angle set to: {yaw_degrees:.1f}°")
    
    def set_roll_angle(self, roll_degrees):
        """Manually set roll angle (in degrees)"""
        self.roll_angle = math.radians(roll_degrees)
        print(f"Roll angle set to: {roll_degrees:.1f}°")
    
    def calibrate_barrel_tip_offset(self, x_offset, y_offset, z_offset):
        """Allow runtime calibration of barrel tip position"""
        self.barrel_tip_offset = np.array([x_offset, y_offset, z_offset])
        print(f"Barrel tip offset updated to: ({x_offset:.2f}, {y_offset:.2f}, {z_offset:.2f})")
        
    def calibrate_position_sensitivity(self, sensitivity):
        """Allow runtime calibration of position sensitivity"""
        self.position_sensitivity = max(0.1, sensitivity)
        print(f"Position sensitivity updated to: {self.position_sensitivity:.2f}")
    
    def calibrate_distance_sensitivity(self, sensitivity):
        """Allow runtime calibration of distance sensitivity"""
        self.distance_sensitivity = max(0.01, sensitivity)
        print(f"Distance sensitivity updated to: {self.distance_sensitivity:.2f}")
    
    def calibrate_roll_sensitivity(self, sensitivity):
        """Allow runtime calibration of roll sensitivity"""
        self.roll_sensitivity = max(0.1, sensitivity)
        print(f"Roll sensitivity updated to: {self.roll_sensitivity:.2f}")
        
    def set_weapon_forward_direction(self, forward_vector):
        """Allow setting the weapon's forward direction for different models"""
        self.weapon_forward = np.array(forward_vector) / np.linalg.norm(forward_vector)
        print(f"Weapon forward direction set to: {self.weapon_forward}")