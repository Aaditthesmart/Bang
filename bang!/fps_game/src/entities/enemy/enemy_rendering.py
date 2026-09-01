import math
from OpenGL.GL import *

class EnemyRenderer:
    """Handles enemy visual rendering including geometry and health bars"""
    
    @staticmethod
    def draw_enemy(enemy):
        """Draw enemy as a target board on a stand, with health bar above"""
        if not enemy.alive:
            return
            
        glPushMatrix()
        glTranslatef(enemy.x, enemy.y, enemy.z)
        
        # Draw the stand first (below the target centre)
        EnemyRenderer._draw_stand(enemy.radius, enemy.y)
        
        # Draw the target face
        EnemyRenderer._draw_target_board(enemy.radius)
        
        glPopMatrix()
        
        # Draw health bar above the enemy
        EnemyRenderer.draw_health_bar(enemy)
    
    @staticmethod
    def _draw_stand(radius, world_y):
        """Draw a simple pole and base feet below the target."""
        glDisable(GL_LIGHTING)
        glColor3f(0.15, 0.15, 0.18)   # dark charcoal

        pole_h = world_y + radius        # extend down to ground
        pw = radius * 0.10               # pole half-width

        # Vertical pole (quad strip front-facing)
        glBegin(GL_QUADS)
        glVertex3f(-pw, -radius, 0.0)
        glVertex3f( pw, -radius, 0.0)
        glVertex3f( pw, -radius - pole_h, 0.0)
        glVertex3f(-pw, -radius - pole_h, 0.0)
        glEnd()

        # Left foot
        fw = radius * 0.55
        glBegin(GL_QUADS)
        glVertex3f(-fw, -radius - pole_h, -fw)
        glVertex3f(-pw, -radius - pole_h, -fw)
        glVertex3f(-pw, -radius - pole_h + pw, -fw)
        glVertex3f(-fw, -radius - pole_h + pw, -fw)
        glEnd()

        # Right foot
        glBegin(GL_QUADS)
        glVertex3f(pw,  -radius - pole_h, -fw)
        glVertex3f(fw,  -radius - pole_h, -fw)
        glVertex3f(fw,  -radius - pole_h + pw, -fw)
        glVertex3f(pw,  -radius - pole_h + pw, -fw)
        glEnd()

        glEnable(GL_LIGHTING)

    @staticmethod
    def _draw_target_board(radius, segments=32):
        """Draw a classic archery target board"""
        # Disable lighting for the target board to make colors pop
        glDisable(GL_LIGHTING)
        
        # Ring colors from outside to inside
        colors = [
            (1.0, 1.0, 1.0),   # White
            (0.1, 0.1, 0.1),   # Black
            (0.2, 0.6, 1.0),   # Light Blue
            (1.0, 0.2, 0.2),   # Red
            (1.0, 0.9, 0.2)    # Yellow
        ]
        
        # Draw from outside to inside, slightly offsetting Z to prevent Z-fighting
        for i, color in enumerate(colors):
            ring_radius = radius * (1.0 - (i * 0.2))
            z_offset = i * 0.01  # Bring inner rings slightly forward
            
            glColor3f(*color)
            
            # Front face
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, 0, z_offset)  # Center
            for j in range(segments + 1):
                angle = 2 * math.pi * j / segments
                x = ring_radius * math.cos(angle)
                y = ring_radius * math.sin(angle)
                glVertex3f(x, y, z_offset)
            glEnd()
            
            # Back face
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, 0, -z_offset - 0.05)  # Back Center
            for j in range(segments + 1):
                angle = 2 * math.pi * j / segments
                x = ring_radius * math.cos(angle)
                y = ring_radius * math.sin(angle)
                glVertex3f(x, y, -z_offset - 0.05)
            glEnd()
            
        glEnable(GL_LIGHTING)
    
    @staticmethod
    def draw_health_bar(enemy):
        """Draw a 3D health bar above the enemy's head"""
        if not enemy.alive:
            return
        
        # Disable lighting for health bar to make it clearly visible
        glDisable(GL_LIGHTING)
        
        # Position health bar above enemy
        bar_height_offset = enemy.height / 2 + 0.5
        bar_width = 1.2
        bar_thickness = 0.1
        bar_depth = 0.05
        
        glPushMatrix()
        glTranslatef(enemy.x, enemy.y + bar_height_offset, enemy.z)
        
        health_percentage = enemy.get_health_percentage()
        
        # Draw health bar background (dark red)
        EnemyRenderer._draw_health_bar_background(bar_width, bar_thickness, bar_depth)
        
        # Draw current health portion
        if health_percentage > 0:
            EnemyRenderer._draw_health_bar_foreground(bar_width, bar_thickness, bar_depth, health_percentage)
        
        # Draw health bar border
        EnemyRenderer._draw_health_bar_border(bar_width, bar_thickness, bar_depth)
        
        glPopMatrix()
        
        # Re-enable lighting
        glEnable(GL_LIGHTING)
    
    @staticmethod
    def _draw_health_bar_background(bar_width, bar_thickness, bar_depth):
        """Draw the background of the health bar"""
        glColor3f(0.3, 0.1, 0.1)
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(-bar_width/2, -bar_thickness/2, bar_depth/2)
        glVertex3f(bar_width/2, -bar_thickness/2, bar_depth/2)
        glVertex3f(bar_width/2, bar_thickness/2, bar_depth/2)
        glVertex3f(-bar_width/2, bar_thickness/2, bar_depth/2)
        
        # Back face
        glVertex3f(-bar_width/2, -bar_thickness/2, -bar_depth/2)
        glVertex3f(-bar_width/2, bar_thickness/2, -bar_depth/2)
        glVertex3f(bar_width/2, bar_thickness/2, -bar_depth/2)
        glVertex3f(bar_width/2, -bar_thickness/2, -bar_depth/2)
        
        # Top face
        glVertex3f(-bar_width/2, bar_thickness/2, -bar_depth/2)
        glVertex3f(-bar_width/2, bar_thickness/2, bar_depth/2)
        glVertex3f(bar_width/2, bar_thickness/2, bar_depth/2)
        glVertex3f(bar_width/2, bar_thickness/2, -bar_depth/2)
        
        # Bottom face
        glVertex3f(-bar_width/2, -bar_thickness/2, -bar_depth/2)
        glVertex3f(bar_width/2, -bar_thickness/2, -bar_depth/2)
        glVertex3f(bar_width/2, -bar_thickness/2, bar_depth/2)
        glVertex3f(-bar_width/2, -bar_thickness/2, bar_depth/2)
        glEnd()
    
    @staticmethod
    def _draw_health_bar_foreground(bar_width, bar_thickness, bar_depth, health_percentage):
        """Draw the current health portion of the health bar"""
        # Set color based on health percentage
        if health_percentage > 0.6:
            glColor3f(0.2, 0.8, 0.2)  # Green
        elif health_percentage > 0.3:
            glColor3f(0.8, 0.8, 0.2)  # Yellow
        else:
            glColor3f(0.8, 0.2, 0.2)  # Red
        
        current_width = bar_width * health_percentage
        glBegin(GL_QUADS)
        # Front face (health portion)
        glVertex3f(-bar_width/2, -bar_thickness/2, bar_depth/2 + 0.001)
        glVertex3f(-bar_width/2 + current_width, -bar_thickness/2, bar_depth/2 + 0.001)
        glVertex3f(-bar_width/2 + current_width, bar_thickness/2, bar_depth/2 + 0.001)
        glVertex3f(-bar_width/2, bar_thickness/2, bar_depth/2 + 0.001)
        
        # Back face (health portion)
        glVertex3f(-bar_width/2, -bar_thickness/2, -bar_depth/2 - 0.001)
        glVertex3f(-bar_width/2, bar_thickness/2, -bar_depth/2 - 0.001)
        glVertex3f(-bar_width/2 + current_width, bar_thickness/2, -bar_depth/2 - 0.001)
        glVertex3f(-bar_width/2 + current_width, -bar_thickness/2, -bar_depth/2 - 0.001)
        
        # Top face (health portion)
        glVertex3f(-bar_width/2, bar_thickness/2, -bar_depth/2 - 0.001)
        glVertex3f(-bar_width/2, bar_thickness/2, bar_depth/2 + 0.001)
        glVertex3f(-bar_width/2 + current_width, bar_thickness/2, bar_depth/2 + 0.001)
        glVertex3f(-bar_width/2 + current_width, bar_thickness/2, -bar_depth/2 - 0.001)
        
        # Bottom face (health portion)
        glVertex3f(-bar_width/2, -bar_thickness/2, -bar_depth/2 - 0.001)
        glVertex3f(-bar_width/2 + current_width, -bar_thickness/2, -bar_depth/2 - 0.001)
        glVertex3f(-bar_width/2 + current_width, -bar_thickness/2, bar_depth/2 + 0.001)
        glVertex3f(-bar_width/2, -bar_thickness/2, bar_depth/2 + 0.001)
        glEnd()
    
    @staticmethod
    def _draw_health_bar_border(bar_width, bar_thickness, bar_depth):
        """Draw the border of the health bar"""
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(1.5)
        
        # Front border
        glBegin(GL_LINE_LOOP)
        glVertex3f(-bar_width/2, -bar_thickness/2, bar_depth/2 + 0.002)
        glVertex3f(bar_width/2, -bar_thickness/2, bar_depth/2 + 0.002)
        glVertex3f(bar_width/2, bar_thickness/2, bar_depth/2 + 0.002)
        glVertex3f(-bar_width/2, bar_thickness/2, bar_depth/2 + 0.002)
        glEnd()
        
        # Back border
        glBegin(GL_LINE_LOOP)
        glVertex3f(-bar_width/2, -bar_thickness/2, -bar_depth/2 - 0.002)
        glVertex3f(-bar_width/2, bar_thickness/2, -bar_depth/2 - 0.002)
        glVertex3f(bar_width/2, bar_thickness/2, -bar_depth/2 - 0.002)
        glVertex3f(bar_width/2, -bar_thickness/2, -bar_depth/2 - 0.002)
        glEnd()
        
        glLineWidth(1.0)