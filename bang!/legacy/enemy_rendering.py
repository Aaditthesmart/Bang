import math
from OpenGL.GL import *

class EnemyRenderer:
    """Handles enemy visual rendering including geometry and health bars"""
    
    @staticmethod
    def draw_enemy(enemy):
        """Draw enemy as a cylinder with health bar above"""
        if not enemy.alive:
            return
            
        glPushMatrix()
        glTranslatef(enemy.x, enemy.y, enemy.z)
        
        # Set material properties for the enemy (red color, darker when damaged)
        health_factor = enemy.get_health_percentage()
        red_intensity = 0.9
        green_intensity = 0.3 * health_factor  # Green fades as health decreases
        blue_intensity = 0.3 * health_factor   # Blue fades as health decreases
        
        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.8, 0.2, 0.2, 1.0])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [red_intensity, green_intensity, blue_intensity, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.1, 0.1, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 30.0)
        
        # Draw the cylinder geometry
        EnemyRenderer._draw_cylinder(enemy.radius, enemy.height)
        
        glPopMatrix()
        
        # Draw health bar above the enemy
        EnemyRenderer.draw_health_bar(enemy)
    
    @staticmethod
    def _draw_cylinder(radius, height, segments=12):
        """Draw a cylinder with the given radius and height"""
        half_height = height / 2.0
        
        # Draw cylinder sides
        glBegin(GL_QUADS)
        for i in range(segments):
            angle1 = 2 * math.pi * i / segments
            angle2 = 2 * math.pi * (i + 1) / segments
            
            x1 = radius * math.cos(angle1)
            z1 = radius * math.sin(angle1)
            x2 = radius * math.cos(angle2)
            z2 = radius * math.sin(angle2)
            
            # Normal for side face
            nx = math.cos((angle1 + angle2) / 2)
            nz = math.sin((angle1 + angle2) / 2)
            glNormal3f(nx, 0, nz)
            
            # Bottom vertices
            glVertex3f(x1, -half_height, z1)
            glVertex3f(x2, -half_height, z2)
            # Top vertices  
            glVertex3f(x2, half_height, z2)
            glVertex3f(x1, half_height, z1)
        glEnd()
        
        # Draw top cap
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, 1, 0)
        glVertex3f(0, half_height, 0)  # Center
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            glVertex3f(x, half_height, z)
        glEnd()
        
        # Draw bottom cap
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, -1, 0)
        glVertex3f(0, -half_height, 0)  # Center
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            glVertex3f(x, -half_height, -z)  # Reverse winding for bottom
        glEnd()
    
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