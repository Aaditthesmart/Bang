import time
from src.animations.reload import ReloadAnimation

class WeaponSystem:
    """Handles weapon mechanics including ammo, reloading, and shooting"""
    
    def __init__(self, max_ammo=7, reload_time=2.0):
        self.max_ammo = max_ammo
        self.current_ammo = max_ammo
        self.reload_time = reload_time
        self.is_reloading = False
        self.reload_start_time = 0
        self.last_shot_time = 0
        self.fire_rate = 0.2  # Minimum time between shots (200ms)
        
        # Initialize reload animation
        self.reload_animation = ReloadAnimation(duration=reload_time)
        
    def can_shoot(self):
        """Check if weapon can shoot (has ammo, not reloading, fire rate respected)"""
        current_time = time.time()
        return (not self.is_reloading and 
                self.current_ammo > 0 and 
                current_time - self.last_shot_time >= self.fire_rate)
    
    def shoot(self):
        """Attempt to shoot - returns True if successful"""
        if not self.can_shoot():
            return False
            
        self.current_ammo -= 1
        self.last_shot_time = time.time()
        
        # Auto-reload when ammo reaches 0
        if self.current_ammo <= 0:
            self.start_reload()
            
        return True
    
    def start_reload(self, current_quaternion=None):
        """Start the reload process with weapon transition - NO sound here"""
        if self.is_reloading or self.current_ammo == self.max_ammo:
            return False
            
        self.is_reloading = True
        self.reload_start_time = time.time()
        
        # NO SOUND CALL HERE - sound will be triggered during pull_back phase
        
        # Start the reload animation with current weapon quaternion
        if current_quaternion is not None:
            self.reload_animation.start_animation(current_quaternion)
        else:
            # Fallback to identity quaternion if none provided
            import numpy as np
            self.reload_animation.start_animation(np.array([1.0, 0.0, 0.0, 0.0]))
        
        print(f"Reloading... ({self.reload_time:.1f}s) - Sound will play during slide pull!")
        return True
    
    def update(self):
        """Update weapon state (call every frame)"""
        # Update reload animation (this handles sound timing internally)
        self.reload_animation.update()
        
        if self.is_reloading:
            current_time = time.time()
            if current_time - self.reload_start_time >= self.reload_time:
                # Reload complete
                self.current_ammo = self.max_ammo
                self.is_reloading = False
                print(f"Reload complete! Ammo: {self.current_ammo}/{self.max_ammo}")
    
    def get_reload_progress(self):
        """Get reload progress as percentage (0.0 to 1.0)"""
        if not self.is_reloading:
            return 1.0
            
        current_time = time.time()
        elapsed = current_time - self.reload_start_time
        return min(elapsed / self.reload_time, 1.0)
    
    def get_ammo_info(self):
        """Get ammo information as tuple (current, max)"""
        return self.current_ammo, self.max_ammo
    
    def force_reload(self, current_quaternion=None):
        """Force reload (manual reload with R key)"""
        return self.start_reload(current_quaternion)
    
    def get_weapon_orientation_quaternion(self, quaternion_weapon):
        """Get the appropriate weapon quaternion (either cursor-following or reload transition)"""
        if self.is_reloading:
            return self.reload_animation.get_weapon_transition_quaternion(quaternion_weapon.quaternion)
        else:
            return quaternion_weapon.quaternion
    
    def render_reload_animation(self, weapon_position):
        """Render the reload animation arm"""
        self.reload_animation.render_arm(weapon_position)