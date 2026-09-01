import math
from OpenGL.GL import *
from src.rendering.model_loader import render_pistol

def draw_skybox():
    """Draw a rich deep-blue gradient sky with mountain silhouettes."""
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)

    # --- Sky gradient: deep navy at top → bright cerulean at horizon ---
    glBegin(GL_QUADS)
    # Ceiling
    glColor3f(0.08, 0.18, 0.45)
    glVertex3f(-200, 80, -200)
    glVertex3f( 200, 80, -200)
    glVertex3f( 200, 80,  200)
    glVertex3f(-200, 80,  200)

    # 4 sky walls
    for i in range(4):
        a1 = i * math.pi / 2
        a2 = a1 + math.pi / 2
        x1, z1 = 200 * math.cos(a1), 200 * math.sin(a1)
        x2, z2 = 200 * math.cos(a2), 200 * math.sin(a2)

        glColor3f(0.08, 0.18, 0.45)   # navy top
        glVertex3f(x1, 80, z1)
        glVertex3f(x2, 80, z2)
        glColor3f(0.30, 0.60, 0.90)   # cerulean horizon
        glVertex3f(x2,  0, z2)
        glVertex3f(x1,  0, z1)
    glEnd()

    # --- Mountain silhouettes (drawn as dark blue filled shapes) ---
    glColor3f(0.10, 0.22, 0.48)
    _draw_mountain_range()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glDepthMask(GL_TRUE)


def _draw_mountain_range():
    """Draw stylised low-poly mountain silhouettes around the horizon."""
    mountains = [
        # (center_x, center_z, peak_height, half_width)
        (-80, -90,  22, 30),
        (-30, -95,  28, 35),
        ( 20, -90,  20, 25),
        ( 70, -92,  26, 32),
        (110, -88,  18, 28),
        (-110,-85,  24, 30),
    ]
    glBegin(GL_TRIANGLES)
    for cx, cz, ph, hw in mountains:
        # left base  →  peak  →  right base
        glVertex3f(cx - hw, 0,       cz)
        glVertex3f(cx,       ph,     cz)
        glVertex3f(cx + hw,  0,      cz)
        # second overlapping mountain for depth
        glVertex3f(cx - hw*0.6, 0,   cz - 5)
        glVertex3f(cx + hw*0.3, ph*0.8, cz - 5)
        glVertex3f(cx + hw,     0,   cz - 5)
    glEnd()


def draw_ground():
    """Draw a dark navy tactical floor with a perspective grid."""
    glDisable(GL_LIGHTING)

    # --- Solid dark navy base ---
    glColor3f(0.08, 0.14, 0.28)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-100, 0, -100)
    glVertex3f( 100, 0, -100)
    glVertex3f( 100, 0,  100)
    glVertex3f(-100, 0,  100)
    glEnd()

    # --- Bright teal/blue grid lines ---
    glLineWidth(1.0)
    glColor3f(0.10, 0.35, 0.65)
    glBegin(GL_LINES)
    step = 5
    for i in range(-100, 101, step):
        glVertex3f(i, 0.02, -100)
        glVertex3f(i, 0.02,  100)
        glVertex3f(-100, 0.02, i)
        glVertex3f( 100, 0.02, i)
    glEnd()
    glLineWidth(1.0)

    glEnable(GL_LIGHTING)

def draw_weapon_model(quaternion_weapon, weapon_system=None):
    """Draw the pistol model using quaternion-based positioning with reload transitions"""
    
    # Get the appropriate weapon quaternion (cursor-following or reload transition)
    if weapon_system:
        weapon_quaternion = weapon_system.get_weapon_orientation_quaternion(quaternion_weapon)
    else:
        weapon_quaternion = quaternion_weapon.quaternion
    
    # Temporarily override the quaternion_weapon's quaternion for rendering
    original_quaternion = quaternion_weapon.quaternion.copy()
    quaternion_weapon.quaternion = weapon_quaternion
    
    # Apply weapon transformation (this pushes matrix)
    if quaternion_weapon.apply_weapon_transform():
        
        # Reduced scale for smaller weapon size
        weapon_scale = 50.0  # Reduced from 100.0
        
        # Render the pistol model at origin (transformation already applied)
        # Weapon stays steady during reload - no spinning
        render_pistol(
            position=(0, 0, 0),  # Centered at origin since transform is already applied
            rotation=(-90, 0, 90),  # Fixed rotation - no spinning
            scale=weapon_scale
        )
        
        # Pop the matrix
        glPopMatrix()
    
    # Restore original quaternion
    quaternion_weapon.quaternion = original_quaternion
    
    # Render reload animation arm if weapon system is provided
    if weapon_system:
        # Get weapon world position for arm animation
        weapon_world_pos = [
            quaternion_weapon.camera_pos[0] + quaternion_weapon.weapon_offset[0],
            quaternion_weapon.camera_pos[1] + quaternion_weapon.weapon_offset[1],
            quaternion_weapon.camera_pos[2] + quaternion_weapon.weapon_offset[2]
        ]
        weapon_system.render_reload_animation(weapon_world_pos)

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