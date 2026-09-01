import time

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
    
    def start_reload(self):
        """Start the reload process"""
        if self.is_reloading or self.current_ammo == self.max_ammo:
            return False
            
        self.is_reloading = True
        self.reload_start_time = time.time()
        print(f"Reloading... ({self.reload_time:.1f}s)")
        return True
    
    def update(self):
        """Update weapon state (call every frame)"""
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
    
    def force_reload(self):
        """Force reload (manual reload with R key)"""
        return self.start_reload()