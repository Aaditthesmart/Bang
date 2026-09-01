import math
from OpenGL.GL import *
from model_loader import render_pistol

def draw_skybox():
    # Disable depth testing for skybox
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)  # Disable lighting for skybox
    glDepthMask(GL_FALSE)
    
    # Sky gradient
    glBegin(GL_QUADS)
    
    # Top (lighter blue)
    glColor3f(0.5, 0.7, 1.0)
    glVertex3f(-100, 50, -100)
    glVertex3f(100, 50, -100)
    glVertex3f(100, 50, 100)
    glVertex3f(-100, 50, 100)
    
    # Sides with gradient
    for i in range(4):
        angle = i * math.pi / 2
        x1, z1 = 100 * math.cos(angle), 100 * math.sin(angle)
        x2, z2 = 100 * math.cos(angle + math.pi/2), 100 * math.sin(angle + math.pi/2)
        
        # Top of side (sky blue)
        glColor3f(0.5, 0.7, 1.0)
        glVertex3f(x1, 50, z1)
        glVertex3f(x2, 50, z2)
        
        # Bottom of side (horizon blue)
        glColor3f(0.7, 0.8, 1.0)
        glVertex3f(x2, 0, z2)
        glVertex3f(x1, 0, z1)
    
    glEnd()
    
    # Re-enable depth testing and lighting
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glDepthMask(GL_TRUE)

def draw_ground():
    # Set material properties for the ground
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.5, 0.5, 0.5, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 10.0)
    
    # Draw large platform
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-50, 0, -50)
    glVertex3f(50, 0, -50)
    glVertex3f(50, 0, 50)
    glVertex3f(-50, 0, 50)
    glEnd()
    
    # Add some grid lines for depth perception
    glDisable(GL_LIGHTING)  # Disable lighting for grid lines
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-50, 51, 5):
        glVertex3f(i, 0.01, -50)
        glVertex3f(i, 0.01, 50)
        glVertex3f(-50, 0.01, i)
        glVertex3f(50, 0.01, i)
    glEnd()
    glEnable(GL_LIGHTING)  # Re-enable lighting

def draw_weapon_model(quaternion_weapon):
    """Draw the pistol model using quaternion-based positioning"""
    # Apply weapon transformation (this pushes matrix)
    if quaternion_weapon.apply_weapon_transform():
        
        # Much smaller scale for reasonable weapon size
        weapon_scale = 100.0
        
        # Render the pistol model at origin (transformation already applied)
        # Adjusted rotation to fix sideways orientation
        render_pistol(
            position=(0, 0, 0),
            rotation=(-90, 0, 90),  # Fixed orientation: pitch -90, yaw 0, roll 90
            scale=weapon_scale
        )
        
        # Pop the matrix
        glPopMatrix()

def draw_cursor_target(quaternion_weapon):
    """Draw a small sphere at the cursor target position for visualization"""
    cursor_pos = quaternion_weapon.get_cursor_world_position()
    
    glPushMatrix()
    glTranslatef(cursor_pos[0], cursor_pos[1], cursor_pos[2])
    
    # Set bright material for visibility
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 0.0, 0.0)  # Bright red
    
    # Draw a simple sphere using triangle strips
    import math
    
    segments = 8
    rings = 6
    radius = 0.1
    
    for i in range(rings):
        ring_angle1 = math.pi * i / rings
        ring_angle2 = math.pi * (i + 1) / rings
        
        glBegin(GL_TRIANGLE_STRIP)
        for j in range(segments + 1):
            segment_angle = 2 * math.pi * j / segments
            
            x1 = radius * math.sin(ring_angle1) * math.cos(segment_angle)
            y1 = radius * math.cos(ring_angle1)
            z1 = radius * math.sin(ring_angle1) * math.sin(segment_angle)
            
            x2 = radius * math.sin(ring_angle2) * math.cos(segment_angle)
            y2 = radius * math.cos(ring_angle2)
            z2 = radius * math.sin(ring_angle2) * math.sin(segment_angle)
            
            glVertex3f(x1, y1, z1)
            glVertex3f(x2, y2, z2)
        glEnd()
    
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_pistol_on_ground():
    """Draw a pistol model on the ground as a demo/pickup item - REMOVED"""
    # Function removed to clean up the scene
    pass