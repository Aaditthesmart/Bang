from OpenGL.GL import *

def draw_crosshair():
    """Crosshair removed - weapon now aims at cursor position"""
    pass

def draw_health_bar(health_percentage):
    """Draw health bar in top-left corner"""
    # Save current matrices
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth testing and lighting for UI
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Health bar dimensions and position
    bar_width = 0.3
    bar_height = 0.04
    bar_x = -0.9  # Left side of screen
    bar_y = 0.85  # Top of screen
    
    # Draw health bar background (dark red)
    glColor3f(0.3, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_width, bar_y)
    glVertex2f(bar_x + bar_width, bar_y + bar_height)
    glVertex2f(bar_x, bar_y + bar_height)
    glEnd()
    
    # Draw current health (green to red based on health)
    if health_percentage > 0.6:
        glColor3f(0.2, 0.8, 0.2)  # Green
    elif health_percentage > 0.3:
        glColor3f(0.8, 0.8, 0.2)  # Yellow
    else:
        glColor3f(0.8, 0.2, 0.2)  # Red
    
    current_width = bar_width * health_percentage
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + current_width, bar_y)
    glVertex2f(bar_x + current_width, bar_y + bar_height)
    glVertex2f(bar_x, bar_y + bar_height)
    glEnd()
    
    # Draw health bar border (white)
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_width, bar_y)
    glVertex2f(bar_x + bar_width, bar_y + bar_height)
    glVertex2f(bar_x, bar_y + bar_height)
    glEnd()
    glLineWidth(1.0)
    
    # Draw "HEALTH" text (simplified using lines)
    glColor3f(1.0, 1.0, 1.0)
    text_y = bar_y + bar_height + 0.03
    glLineWidth(1.5)
    
    # Simple "HP" text using basic lines
    glBegin(GL_LINES)
    # H
    glVertex2f(bar_x, text_y)
    glVertex2f(bar_x, text_y + 0.03)
    glVertex2f(bar_x, text_y + 0.015)
    glVertex2f(bar_x + 0.015, text_y + 0.015)
    glVertex2f(bar_x + 0.015, text_y)
    glVertex2f(bar_x + 0.015, text_y + 0.03)
    
    # P
    glVertex2f(bar_x + 0.025, text_y)
    glVertex2f(bar_x + 0.025, text_y + 0.03)
    glVertex2f(bar_x + 0.025, text_y + 0.03)
    glVertex2f(bar_x + 0.04, text_y + 0.03)
    glVertex2f(bar_x + 0.04, text_y + 0.03)
    glVertex2f(bar_x + 0.04, text_y + 0.015)
    glVertex2f(bar_x + 0.04, text_y + 0.015)
    glVertex2f(bar_x + 0.025, text_y + 0.015)
    glEnd()
    
    glLineWidth(1.0)
    
    # Restore settings
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    # Restore matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_ammo_display(weapon_system):
    """Draw ammo counter and reload indicator in bottom-right corner"""
    # Save current matrices
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth testing and lighting for UI
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    current_ammo, max_ammo = weapon_system.get_ammo_info()
    
    # Ammo display position (bottom-right corner)
    bullet_size = 0.025
    bullet_spacing = 0.04
    total_width = max_ammo * bullet_spacing - (bullet_spacing - bullet_size)
    
    # Position in bottom-right corner with some margin
    margin = 0.05
    ammo_x = 1.0 - total_width - margin  # Right side with margin
    ammo_y = -0.95 + margin  # Bottom with margin
    
    start_x = ammo_x
    
    for i in range(max_ammo):
        bullet_x = start_x + i * bullet_spacing
        
        # Choose color based on ammo status
        if weapon_system.is_reloading:
            # Flashing yellow during reload
            import time
            flash = int(time.time() * 8) % 2  # Flash 4 times per second
            if flash:
                glColor3f(1.0, 1.0, 0.3)  # Yellow flash
            else:
                glColor3f(0.3, 0.3, 0.1)  # Dark yellow
        elif i < current_ammo:
            glColor3f(0.9, 0.9, 0.2)  # Bright yellow (loaded)
        else:
            glColor3f(0.3, 0.3, 0.3)  # Gray (empty)
        
        # Draw bullet as small rectangle
        glBegin(GL_QUADS)
        glVertex2f(bullet_x, ammo_y)
        glVertex2f(bullet_x + bullet_size, ammo_y)
        glVertex2f(bullet_x + bullet_size, ammo_y + bullet_size * 2)
        glVertex2f(bullet_x, ammo_y + bullet_size * 2)
        glEnd()
        
        # Draw bullet border
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(bullet_x, ammo_y)
        glVertex2f(bullet_x + bullet_size, ammo_y)
        glVertex2f(bullet_x + bullet_size, ammo_y + bullet_size * 2)
        glVertex2f(bullet_x, ammo_y + bullet_size * 2)
        glEnd()
    
    # Draw reload progress bar if reloading
    if weapon_system.is_reloading:
        progress = weapon_system.get_reload_progress()
        
        # Reload bar position (above bullets)
        reload_bar_y = ammo_y + bullet_size * 2 + 0.02
        reload_bar_width = total_width
        reload_bar_height = 0.02
        
        # Draw reload bar background
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex2f(start_x, reload_bar_y)
        glVertex2f(start_x + reload_bar_width, reload_bar_y)
        glVertex2f(start_x + reload_bar_width, reload_bar_y + reload_bar_height)
        glVertex2f(start_x, reload_bar_y + reload_bar_height)
        glEnd()
        
        # Draw reload progress
        glColor3f(0.2, 0.8, 0.2)  # Green progress
        progress_width = reload_bar_width * progress
        glBegin(GL_QUADS)
        glVertex2f(start_x, reload_bar_y)
        glVertex2f(start_x + progress_width, reload_bar_y)
        glVertex2f(start_x + progress_width, reload_bar_y + reload_bar_height)
        glVertex2f(start_x, reload_bar_y + reload_bar_height)
        glEnd()
        
        # Draw reload bar border
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(start_x, reload_bar_y)
        glVertex2f(start_x + reload_bar_width, reload_bar_y)
        glVertex2f(start_x + reload_bar_width, reload_bar_y + reload_bar_height)
        glVertex2f(start_x, reload_bar_y + reload_bar_height)
        glEnd()
        
        # Draw "RELOADING..." text (above reload bar)
        glColor3f(1.0, 1.0, 0.3)
        text_y = reload_bar_y + reload_bar_height + 0.02
        _draw_simple_text("RELOADING", start_x + reload_bar_width/2 - 0.08, text_y)
    
    # Draw ammo text (above bullets when not reloading, or above reload text when reloading)
    glColor3f(1.0, 1.0, 1.0)
    if weapon_system.is_reloading:
        text_y = ammo_y + bullet_size * 2 + 0.08  # Above reload elements
    else:
        text_y = ammo_y + bullet_size * 2 + 0.02  # Above bullets
    
    _draw_simple_text("AMMO", start_x + total_width/2 - 0.04, text_y)
    
    # Restore settings
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    # Restore matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def _draw_simple_text(text, x, y):
    """Draw simple text using basic line segments"""
    glLineWidth(1.5)
    char_width = 0.015
    char_spacing = 0.02
    
    for i, char in enumerate(text):
        char_x = x + i * char_spacing
        _draw_char(char, char_x, y, char_width)
    
    glLineWidth(1.0)

def _draw_char(char, x, y, size):
    """Draw a simple character using line segments"""
    glBegin(GL_LINES)
    
    if char == 'A':
        # A
        glVertex2f(x, y)
        glVertex2f(x + size/2, y + size)
        glVertex2f(x + size/2, y + size)
        glVertex2f(x + size, y)
        glVertex2f(x + size/4, y + size/2)
        glVertex2f(x + 3*size/4, y + size/2)
    elif char == 'M':
        # M
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + size/2, y + size/2)
        glVertex2f(x + size/2, y + size/2)
        glVertex2f(x + size, y + size)
        glVertex2f(x + size, y + size)
        glVertex2f(x + size, y)
    elif char == 'O':
        # O (simplified as rectangle)
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + size, y + size)
        glVertex2f(x + size, y + size)
        glVertex2f(x + size, y)
        glVertex2f(x + size, y)
        glVertex2f(x, y)
    elif char == 'R':
        # R
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + size, y + size)
        glVertex2f(x + size, y + size)
        glVertex2f(x + size, y + size/2)
        glVertex2f(x + size, y + size/2)
        glVertex2f(x, y + size/2)
        glVertex2f(x, y + size/2)
        glVertex2f(x + size, y)
    elif char == 'E':
        # E
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + size, y + size)
        glVertex2f(x, y + size/2)
        glVertex2f(x + 3*size/4, y + size/2)
        glVertex2f(x, y)
        glVertex2f(x + size, y)
    elif char == 'L':
        # L
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y)
        glVertex2f(x + size, y)
    elif char == 'D':
        # D (simplified)
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + 3*size/4, y + size)
        glVertex2f(x + 3*size/4, y + size)
        glVertex2f(x + size, y + 3*size/4)
        glVertex2f(x + size, y + 3*size/4)
        glVertex2f(x + size, y + size/4)
        glVertex2f(x + size, y + size/4)
        glVertex2f(x + 3*size/4, y)
        glVertex2f(x + 3*size/4, y)
        glVertex2f(x, y)
    elif char == 'I':
        # I
        glVertex2f(x, y)
        glVertex2f(x + size, y)
        glVertex2f(x + size/2, y)
        glVertex2f(x + size/2, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + size, y + size)
    elif char == 'N':
        # N
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + size, y)
        glVertex2f(x + size, y)
        glVertex2f(x + size, y + size)
    elif char == 'G':
        # G (simplified)
        glVertex2f(x, y)
        glVertex2f(x, y + size)
        glVertex2f(x, y + size)
        glVertex2f(x + size, y + size)
        glVertex2f(x + size, y + size/2)
        glVertex2f(x + size/2, y + size/2)
        glVertex2f(x + size/2, y + size/2)
        glVertex2f(x + size, y)
        glVertex2f(x + size, y)
        glVertex2f(x, y)
    
    glEnd()

def draw_cursor_indicator():
    """Draw a small indicator showing cursor position - optional function"""
    pass