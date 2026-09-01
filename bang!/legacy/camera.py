import math
from OpenGL.GL import *
from OpenGL.GLU import *

class Camera:
    def __init__(self):
        # Fixed camera position
        self.x = 0.0
        self.y = 2.0
        self.z = 5.0
        
        # Camera always looks straight ahead (no movement)
        self.yaw = 0.0
        self.pitch = 0.0
        
        # Remove movement capabilities
        self.speed = 0.0
        self.sensitivity = 0.0
        
    def update(self, keys, mouse_rel):
        # No movement or rotation - camera stays fixed
        pass
        
    def apply(self):
        # Fixed camera looking straight ahead
        glLoadIdentity()
        gluLookAt(self.x, self.y, self.z,
                  self.x, self.y, self.z - 1.0,  # Look straight forward (negative Z)
                  0.0, 1.0, 0.0)
    
    def get_forward_vector(self):
        # Always pointing straight forward
        return 0.0, 0.0, -1.0
    
    def get_position(self):
        """Get camera position for weapon positioning"""
        return (self.x, self.y, self.z)