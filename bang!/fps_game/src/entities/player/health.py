import time

class HealthSystem:
    def __init__(self, max_health=100):
        self.max_health = max_health
        self.current_health = max_health
        self.last_damage_time = 0
        self.damage_cooldown = 1.0  # 1 second between damage instances
        self.damage_per_hit = 20
        self.is_alive = True
        
    def take_damage(self, damage=None):
        """Take damage if cooldown has passed"""
        current_time = time.time()
        
        # Check if enough time has passed since last damage
        if current_time - self.last_damage_time < self.damage_cooldown:
            return False
        
        if damage is None:
            damage = self.damage_per_hit
            
        self.current_health -= damage
        self.last_damage_time = current_time
        
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            print("GAME OVER! You have been defeated!")
        else:
            print(f"Taking damage! Health: {self.current_health}/{self.max_health}")
            
        return True
    
    def heal(self, amount):
        """Heal the player"""
        self.current_health = min(self.max_health, self.current_health + amount)
    
    def get_health_percentage(self):
        """Get health as a percentage for UI display"""
        return self.current_health / self.max_health
    
    def reset(self):
        """Reset health to full"""
        self.current_health = self.max_health
        self.is_alive = True
        self.last_damage_time = 0