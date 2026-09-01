import math
import random

class EnemyBase:
    """Base enemy class containing core properties and basic functionality"""
    
    def __init__(self, x, y, z, height=3.0, radius=0.8):
        self.x = x
        self.y = y
        self.z = z
        self.height = height
        self.radius = radius
        self.speed = 0.02  # Movement speed towards player
        self.alive = True
        
        # Health system for individual enemies
        self.max_health = random.randint(30, 80)  # Randomized health between 30-80
        self.current_health = self.max_health
        
    def take_damage(self, damage=25):
        """Enemy takes damage and returns True if killed"""
        if not self.alive:
            return False
            
        self.current_health -= damage
        
        if self.current_health <= 0:
            self.current_health = 0
            self.alive = False
            return True
        
        return False
    
    def get_health_percentage(self):
        """Get health as percentage for health bar display"""
        return self.current_health / self.max_health if self.max_health > 0 else 0
    
    def destroy(self):
        """Mark enemy as destroyed (kept for compatibility)"""
        self.alive = False
        
    def get_position(self):
        """Get enemy position as tuple"""
        return (self.x, self.y, self.z)
        
    def set_position(self, x, y, z):
        """Set enemy position"""
        self.x = x
        self.y = y
        self.z = z