import pygame
from pygame.locals import *
from OpenGL.GL import *
import random

# Import our modules
from camera import Camera  # Now fixed position camera
from enemy import Enemy
from environment import draw_skybox, draw_ground, draw_weapon_model, draw_cursor_target
from ui import draw_crosshair, draw_health_bar, draw_ammo_display  # Crosshair is now empty
from weapon import shoot  # Updated to use cursor tracking
from weapon_system import WeaponSystem
from render import Render
from health import HealthSystem
from collision import CollisionSystem
from cursor_weapon import QuaternionWeapon  # New cursor tracking weapon

class Game:
    def __init__(self):
        pygame.init()
        
        # Set up display
        self.display = (800, 600)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Shooting Game - Cursor Aiming")
        
        # Keep cursor visible since we're tracking it
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)  # Don't grab mouse - we need to track cursor position
        
        # Initialize OpenGL
        Render.init_opengl()
        
        # Game objects
        self.camera = Camera()  # Fixed position camera
        self.quaternion_weapon = QuaternionWeapon(self.camera.get_position())
        self.enemies = self.create_enemies()
        self.health_system = HealthSystem(max_health=100)
        self.weapon_system = WeaponSystem(max_ammo=7, reload_time=2.0)
        self.player_radius = 0.5  # Player collision radius
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.print_instructions()
    
    def create_enemies(self):
        """Create initial enemy cylinders in front of the camera"""
        enemies = []
        for i in range(8):
            # Spawn enemies only in front of camera (negative Z direction)
            # Camera is at (0, 2, 5) looking toward negative Z
            distance = random.uniform(15, 25)
            spread = 10.0  # How wide the spawn area is
            
            x = random.uniform(-spread, spread)  # Left to right spread
            z = -distance + random.uniform(-5, 5)  # In front, with some depth variation
            y = 1.5  # Half the height so they sit on the ground
            
            # Vary the enemy sizes slightly
            height = random.uniform(2.5, 3.5)
            radius = random.uniform(0.6, 1.0)
            
            enemy = Enemy(x, y, z, height, radius)
            enemies.append(enemy)
            print(f"Enemy {i+1} spawned with {enemy.max_health} HP")
        
        return enemies
    
    def print_instructions(self):
        print("Controls:")
        print("Mouse - Aim weapon (cursor tracking)")
        print("Left Click - Shoot")
        print("R - Reload weapon (manual)")
        print("ESC - Exit")
        print(f"Survive! Destroy all {len(self.enemies)} AI enemies!")
        print("Watch out - they're coming for you!")
        print("Health: 100/100 - Don't let enemies touch you!")
        print(f"Ammo: {self.weapon_system.max_ammo} rounds per magazine")
        print("The weapon now follows your cursor and shoots from the gun tip!")
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Manual reload
                    if self.weapon_system.force_reload():
                        print("Manual reload started!")
                    else:
                        print("Cannot reload now (already full or already reloading)")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Use cursor tracking weapon for shooting
                    shoot_result = shoot(self.camera, self.enemies, self.weapon_system, self.quaternion_weapon)
                    if not shoot_result:
                        # Shooting failed - could be reloading, no ammo, or fire rate
                        if self.weapon_system.is_reloading:
                            print("Cannot shoot - reloading!")
                        elif self.weapon_system.current_ammo <= 0:
                            print("No ammo!")
                        else:
                            print("Weapon cooling down...")
    
    def update(self, mouse_rel=None):
        """Update game state"""
        # Stop updating if player is dead
        if not self.health_system.is_alive:
            return
        
        # Update weapon system
        self.weapon_system.update()
        
        # Update quaternion weapon to track cursor
        self.quaternion_weapon.update()
            
        # Get player position for collision detection (camera position since camera is fixed)
        player_pos = [self.camera.x, self.camera.y, self.camera.z]
        
        # Update AI enemies
        for enemy in self.enemies:
            enemy.update(player_pos)
        
        # Check for collisions with enemies
        colliding_enemies = CollisionSystem.check_multiple_collisions(
            player_pos, self.player_radius, self.enemies
        )
        
        # Handle collisions
        if colliding_enemies:
            # Take damage from collision
            if self.health_system.take_damage():
                print("Enemy collision! Cannot move to avoid damage - defend yourself!")
        
        # Remove dead enemies from the list
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        
        # Check win condition
        if len(self.enemies) == 0 and self.health_system.is_alive:
            print("Victory! All enemies defeated!")
            print(f"Final Health: {self.health_system.current_health}/{self.health_system.max_health}")
            self.running = False
        elif not self.health_system.is_alive:
            self.running = False
    
    def render(self):
        """Render the game"""
        # Clear screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Apply camera transformation (fixed position)
        self.camera.apply()
        
        # Draw environment
        draw_skybox()
        draw_ground()
        
        # Draw cursor target for visualization (optional - can be removed)
        draw_cursor_target(self.quaternion_weapon)
        
        # Draw weapon using cursor tracking
        draw_weapon_model(self.quaternion_weapon)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw()
        
        # Draw UI (crosshair is now removed)
        draw_crosshair()  # This is now empty
        draw_health_bar(self.health_system.get_health_percentage())
        draw_ammo_display(self.weapon_system)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        
        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()