import math
import numpy as np
import pygame
from OpenGL.GL import *

class QuaternionWeapon:
    """Weapon system that tracks cursor position using quaternions"""
    
    def __init__(self, camera_pos=(0, 2, 5)):
        self.camera_pos = camera_pos
        self.weapon_offset = np.array([0.3, -0.4, -0.8])  # Offset from camera
        self.cursor_world_pos = np.array([0, 0, -10])  # Default target position
        
        # Quaternion for weapon rotation (identity quaternion = no rotation)
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # [w, x, y, z]
        
        # Screen dimensions for cursor calculations
        self.screen_width = 800
        self.screen_height = 600
        
        # FOV and aspect ratio should match the OpenGL projection
        self.fov = 60.0  # Degrees
        self.aspect_ratio = self.screen_width / self.screen_height
        
    def update_cursor_position(self, mouse_pos):
        """Convert mouse screen coordinates to 3D world coordinates using proper perspective projection"""
        # Get mouse position relative to screen center
        screen_center_x = self.screen_width / 2
        screen_center_y = self.screen_height / 2
        
        # Convert to normalized device coordinates (-1 to 1)
        ndc_x = (mouse_pos[0] - screen_center_x) / screen_center_x
        ndc_y = -(mouse_pos[1] - screen_center_y) / screen_center_y  # Flip Y
        
        # Convert FOV to radians and calculate tangent
        fov_rad = math.radians(self.fov / 2.0)
        tan_fov = math.tan(fov_rad)
        
        # Calculate world coordinates using proper perspective projection
        target_distance = 20.0
        camera_pos = np.array(self.camera_pos)
        
        # Calculate the world coordinates based on perspective projection
        world_x = camera_pos[0] + (ndc_x * tan_fov * self.aspect_ratio * target_distance)
        world_y = camera_pos[1] + (ndc_y * tan_fov * target_distance)
        world_z = camera_pos[2] - target_distance  # Forward direction (negative Z)
        
        self.cursor_world_pos = np.array([world_x, world_y, world_z])
    
    def calculate_weapon_orientation(self):
        """Calculate weapon orientation to point at cursor using quaternions"""
        # Get weapon world position
        weapon_pos = np.array(self.camera_pos) + self.weapon_offset
        
        # Calculate direction from weapon to cursor
        direction = self.cursor_world_pos - weapon_pos
        direction = direction / np.linalg.norm(direction)  # Normalize
        
        # Calculate quaternion to rotate weapon toward target
        # Default weapon forward direction is (0, 0, -1)
        forward = np.array([0.0, 0.0, -1.0])
        
        # Calculate rotation axis and angle
        cross_product = np.cross(forward, direction)
        dot_product = np.dot(forward, direction)
        
        # Handle edge cases
        if np.allclose(cross_product, 0):
            if dot_product > 0:
                # Same direction
                self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])
            else:
                # Opposite direction
                self.quaternion = np.array([0.0, 1.0, 0.0, 0.0])
        else:
            # Calculate quaternion from axis and angle
            axis = cross_product / np.linalg.norm(cross_product)
            angle = math.acos(max(-1.0, min(1.0, dot_product)))
            
            half_angle = angle / 2.0
            sin_half = math.sin(half_angle)
            cos_half = math.cos(half_angle)
            
            self.quaternion = np.array([
                cos_half,
                axis[0] * sin_half,
                axis[1] * sin_half,
                axis[2] * sin_half
            ])
    
    def quaternion_to_matrix(self, q):
        """Convert quaternion to rotation matrix"""
        w, x, y, z = q
        
        # Rotation matrix from quaternion
        matrix = np.array([
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z,     2*x*z + 2*w*y,     0],
            [2*x*y + 2*w*z,     1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x,     0],
            [2*x*z - 2*w*y,     2*y*z + 2*w*x,     1 - 2*x*x - 2*y*y, 0],
            [0,                 0,                 0,                 1]
        ])
        
        return matrix
    
    def get_weapon_tip_position(self):
        """Get the position of the weapon tip in world coordinates"""
        weapon_pos = np.array(self.camera_pos) + self.weapon_offset
        
        # Apply rotation to get tip offset (weapon extends forward)
        tip_offset = np.array([0.0, 0.0, -0.4])  # Tip is 0.4 units forward from weapon center
        
        # Rotate tip offset by weapon quaternion
        rotation_matrix = self.quaternion_to_matrix(self.quaternion)
        rotated_offset = (rotation_matrix[:3, :3] @ tip_offset)
        
        return weapon_pos + rotated_offset
    
    def get_firing_direction(self):
        """Get the direction from weapon tip to cursor"""
        tip_pos = self.get_weapon_tip_position()
        direction = self.cursor_world_pos - tip_pos
        return direction / np.linalg.norm(direction)  # Normalize
    
    def apply_weapon_transform(self):
        """Apply the weapon transformation for rendering"""
        glPushMatrix()
        
        # Position weapon relative to camera
        weapon_world_pos = np.array(self.camera_pos) + self.weapon_offset
        glTranslatef(weapon_world_pos[0], weapon_world_pos[1], weapon_world_pos[2])
        
        # Apply quaternion rotation
        rotation_matrix = self.quaternion_to_matrix(self.quaternion)
        
        # Convert to OpenGL format (column major) and apply
        gl_matrix = rotation_matrix.flatten(order='F')  # Column major order
        glMultMatrixf(gl_matrix.astype(np.float32))
        
        return True  # Matrix is pushed, caller should pop
    
    def update(self):
        """Update weapon orientation based on current cursor position"""
        # Get current mouse position
        mouse_pos = pygame.mouse.get_pos()
        self.update_cursor_position(mouse_pos)
        self.calculate_weapon_orientation()
        
    def get_cursor_world_position(self):
        """Get the current cursor world position for debugging"""
        return self.cursor_world_pos