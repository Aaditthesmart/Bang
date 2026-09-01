import pygame
from pygame.locals import *
from OpenGL.GL import *
import random
import cv2
import threading
import time

# Import our modules
from src.core.camera import Camera  # Now fixed position camera
from src.entities.enemy.enemy import Enemy
from src.rendering.environment import draw_skybox, draw_ground, draw_weapon_model, draw_cursor_target
from src.rendering.ui import (
    draw_crosshair, draw_health_bar, draw_ammo_display,
    draw_score, draw_title, draw_bottom_banner
)
from src.weapons.weapon import shoot  # Updated to use cursor tracking
from src.weapons.weapon_system import WeaponSystem
from src.systems.particles import ShootingEffects  # New visual effects system
from src.core.render import Render
from src.entities.player.health import HealthSystem
from src.systems.collision import CollisionSystem
from src.weapons.cursor_weapon import QuaternionWeapon  # New cursor tracking weapon
from src.vision.estimate import Estimate  # ArUco marker detection
from src.audio.sound_system import initialize_sound_system, cleanup_sound_system  # Sound system

class Game:
    def __init__(self):
        pygame.init()
        
        # Set up display
        self.display = (800, 600)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("3D Shooting Game - Full ArUco Control")
        
        # Initialize OpenGL
        Render.init_opengl()
        
        # Initialize sound system
        self.sound_system = initialize_sound_system()
        
        # Initialize shooting effects system
        self.shooting_effects = ShootingEffects()
        
        # ArUco marker detection system
        self.estimator = Estimate()
        self.aruco_thread = None
        self.aruco_running = False
        
        # Store full ArUco control data
        self.aruco_data = {
            'position_offset': 0.0,    # Horizontal position offset (d value)
            'orientation_alpha': 0.0,  # Orientation angle in radians (alpha)
            'degree': 90.0,           # Original degree value for compatibility
            'rotation_angle': 0.0,    # Left/right rotation from estimate.angle
            'distance_to_cam': 1.5,   # Distance from camera (default 1.5m)
            'shooting': False,        # Shooting detection from camera
            'reloading': False        # Reload detection from hand gesture
        }
        self.aruco_lock = threading.Lock()
        
        # Start ArUco detection in separate thread
        self.start_aruco_detection()
        
        # Game objects
        self.camera = Camera()  # Fixed position camera
        self.quaternion_weapon = QuaternionWeapon(self.camera.get_position())
        self.enemies = self.create_enemies()
        self.health_system = HealthSystem(max_health=100)
        self.weapon_system = WeaponSystem(max_ammo=7, reload_time=2.0)
        self.player_radius = 0.5  # Player collision radius
        
        # Track shooting state to prevent multiple shots from one detection
        self.last_shoot_state = False
        # Store score
        self.score = 0
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.print_instructions()
    
    def start_aruco_detection(self):
        """Start ArUco marker detection in a separate thread"""
        self.aruco_running = True
        self.aruco_thread = threading.Thread(target=self.aruco_detection_loop, daemon=True)
        self.aruco_thread.start()
        print("ArUco detection started...")
    
    def aruco_detection_loop(self):
        """ArUco detection loop running in separate thread"""
        cap = None
        try:
            # Test if estimator is properly initialized
            if not hasattr(self.estimator, 'K') or not hasattr(self.estimator, 'dist'):
                print("Error: ArUco estimator not properly initialized")
                return
                
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Warning: Could not open camera for ArUco detection")
                return
                
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            # Minimize camera buffer to always get the most recent frame
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            print("ArUco camera initialized successfully")
            print("Camera matrix shape:", self.estimator.K.shape)
            print("Distortion coefficients shape:", self.estimator.dist.shape)
            
            while self.aruco_running:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame from camera")
                    continue
                
                try:
                    frame = cv2.flip(frame, 1)
                    frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
                    
                    # Process frame for ArUco markers
                    frame = self.estimator.get_measurements(frame)
                    
                    # Update cooldowns for shooting and reloading
                    if self.estimator.shoot_cooldown > 0:
                        self.estimator.shoot_cooldown -= 1
                    if self.estimator.reload_cooldown > 0:
                        self.estimator.reload_cooldown -= 1
                    
                    # Collect all ArUco data including shooting/reloading states
                    with self.aruco_lock:
                        # Get geometry data
                        geometry_data = {
                            'position_offset': self.estimator.d,
                            'orientation_alpha': self.estimator.alpha,
                            'degree': 90.0,  # Can be calculated from position if needed
                            'rotation_angle': self.estimator.angle if hasattr(self.estimator, 'angle') else 0.0,
                            'distance_to_cam': self.estimator.d_to_cam if self.estimator.d_to_cam > 0 else 1.5,
                            'shooting': self.estimator.shooting,
                            'reloading': self.estimator.reloading
                        }
                        self.aruco_data = geometry_data
                    
                    # Show ArUco detection window with debug info (Removed to prevent latency)
                    # cv2.imshow in a background thread on Windows causes massive UI blocking and latency.
                    # We will rely entirely on the Pygame window for output.
                        
                except Exception as frame_error:
                    print(f"Error processing frame: {frame_error}")
                    continue
                
                # Removed artificial sleep, cap.read() blocks naturally to camera framerate
                # time.sleep(0.016)
                
        except Exception as e:
            print(f"ArUco detection error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            print("ArUco detection stopped")
    
    def stop_aruco_detection(self):
        """Stop ArUco detection thread"""
        self.aruco_running = False
        if self.aruco_thread and self.aruco_thread.is_alive():
            self.aruco_thread.join(timeout=1.0)
    
    def create_enemies(self):
        """Create initial enemy cylinders in front of the camera"""
        enemies = []
        for i in range(4):
            enemy = self.spawn_single_enemy()
            enemies.append(enemy)
            print(f"Enemy {i+1} spawned with {enemy.max_health} HP")
        
        return enemies

    def spawn_single_enemy(self):
        distance = random.uniform(15, 25)
        spread = 10.0  # How wide the spawn area is
        
        x = random.uniform(-spread, spread)  # Left to right spread
        z = -distance + random.uniform(-5, 5)  # In front, with some depth variation
        y = 1.5  # Half the height so they sit on the ground
        
        # Vary the enemy sizes slightly
        height = random.uniform(2.5, 3.5)
        radius = random.uniform(0.6, 1.0)
        
        return Enemy(x, y, z, height, radius)
    
    def print_instructions(self):
        print("="*60)
        print("FULL ARUCO CONTROL MODE")
        print("="*60)
        print("All weapon control through ArUco marker and camera:")
        print()
        print("AIMING:")
        print("- Move ArUco marker left/right: Weapon follows horizontally")
        print("- Rotate ArUco marker: Gun rotates left/right")
        print("- Move marker closer/further: Gun moves forward/backward in game")
        print()
        print("SHOOTING:")
        print("- Quick upward 'recoil' motion with marker to shoot")
        print("- System detects the characteristic up-then-down motion")
        print()
        print("RELOADING:")
        print("- Make a FIST with LEFT hand ABOVE the ArUco marker")
        print("- System will detect the gesture and reload automatically")
        print()
        print("Manual Controls (backup/calibration):")
        print("Left Click - Manual shoot")
        print("R - Manual reload")
        print("S - Toggle sound on/off")
        print("- / + - Decrease / Increase volume")
        print("ESC - Exit")
        print("Q - Close ArUco detection window")
        print()
        print("Calibration:")
        print("1-6 - Adjust barrel tip position")
        print("7/8 - Adjust position sensitivity")
        print()
        print(f"Survive! Destroy all {len(self.enemies)} AI enemies!")
        print("Watch out - they're coming for you!")
        print("Health: 100/100 - Don't let enemies touch you!")
        print(f"Ammo: {self.weapon_system.max_ammo} rounds per magazine")
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Manual reload (backup option)
                    if self.weapon_system.force_reload(self.quaternion_weapon.quaternion):
                        print("Manual reload started!")
                    else:
                        print("Cannot reload now (already full or already reloading)")
                elif event.key == pygame.K_q:
                    # Close ArUco window (No longer used)
                    pass
                elif event.key == pygame.K_s:
                    # Toggle sound on/off
                    sound_enabled = self.sound_system.toggle_sound()
                    print(f"Sound system {'enabled' if sound_enabled else 'disabled'}")
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    # Decrease volume
                    current_volume = self.sound_system.volume
                    new_volume = max(0.0, current_volume - 0.1)
                    self.sound_system.set_volume(new_volume)
                    print(f"Volume: {int(new_volume * 100)}%")
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                    # Increase volume
                    current_volume = self.sound_system.volume
                    new_volume = min(1.0, current_volume + 0.1)
                    self.sound_system.set_volume(new_volume)
                    print(f"Volume: {int(new_volume * 100)}%")
                # Calibration controls
                elif event.key == pygame.K_1:
                    current_offset = self.quaternion_weapon.barrel_tip_offset
                    self.quaternion_weapon.calibrate_barrel_tip_offset(
                        current_offset[0], current_offset[1], current_offset[2] - 0.1)
                elif event.key == pygame.K_2:
                    current_offset = self.quaternion_weapon.barrel_tip_offset
                    self.quaternion_weapon.calibrate_barrel_tip_offset(
                        current_offset[0], current_offset[1], current_offset[2] + 0.1)
                elif event.key == pygame.K_3:
                    current_offset = self.quaternion_weapon.barrel_tip_offset
                    self.quaternion_weapon.calibrate_barrel_tip_offset(
                        current_offset[0], current_offset[1] + 0.1, current_offset[2])
                elif event.key == pygame.K_4:
                    current_offset = self.quaternion_weapon.barrel_tip_offset
                    self.quaternion_weapon.calibrate_barrel_tip_offset(
                        current_offset[0], current_offset[1] - 0.1, current_offset[2])
                elif event.key == pygame.K_5:
                    current_offset = self.quaternion_weapon.barrel_tip_offset
                    self.quaternion_weapon.calibrate_barrel_tip_offset(
                        current_offset[0] + 0.1, current_offset[1], current_offset[2])
                elif event.key == pygame.K_6:
                    current_offset = self.quaternion_weapon.barrel_tip_offset
                    self.quaternion_weapon.calibrate_barrel_tip_offset(
                        current_offset[0] - 0.1, current_offset[1], current_offset[2])
                elif event.key == pygame.K_7:
                    current_sensitivity = self.quaternion_weapon.position_sensitivity
                    new_sensitivity = max(0.5, current_sensitivity - 0.5)
                    self.quaternion_weapon.calibrate_position_sensitivity(new_sensitivity)
                elif event.key == pygame.K_8:
                    current_sensitivity = self.quaternion_weapon.position_sensitivity
                    new_sensitivity = min(20.0, current_sensitivity + 0.5)
                    self.quaternion_weapon.calibrate_position_sensitivity(new_sensitivity)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button (backup shooting)
                    shoot_result = shoot(self.camera, self.enemies, self.weapon_system, 
                                       self.quaternion_weapon, self.shooting_effects)
                    if not shoot_result:
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
        
        # Update shooting effects (muzzle flash, smoke, screen shake)
        self.shooting_effects.update()
        
        # Get current ArUco data thread-safely
        with self.aruco_lock:
            current_aruco_data = self.aruco_data.copy()
        
        # Update weapon position and orientation with full ArUco data
        if not self.weapon_system.is_reloading:
            self.quaternion_weapon.update_full_aruco_data(current_aruco_data)
            self.quaternion_weapon.calculate_weapon_orientation()
        
        # Handle ArUco-based shooting (edge detection to prevent multiple shots)
        if current_aruco_data['shooting'] and not self.last_shoot_state:
            # Transition from not shooting to shooting - fire!
            shoot_result = shoot(self.camera, self.enemies, self.weapon_system, 
                               self.quaternion_weapon, self.shooting_effects)
            if shoot_result:
                print("ArUco SHOOT detected! Bang!")
            else:
                if self.weapon_system.is_reloading:
                    print("Cannot shoot - reloading!")
                elif self.weapon_system.current_ammo <= 0:
                    print("No ammo! Make a fist with left hand to reload!")
        self.last_shoot_state = current_aruco_data['shooting']
        
        # Handle ArUco-based reloading (edge detection)
        if current_aruco_data['reloading'] and not self.last_reload_state:
            # Transition to reloading - start reload
            if self.weapon_system.force_reload(self.quaternion_weapon.quaternion):
                print("ArUco RELOAD detected! Left fist gesture recognized!")
            else:
                if self.weapon_system.is_reloading:
                    print("Already reloading...")
                elif self.weapon_system.current_ammo == self.weapon_system.max_ammo:
                    print("Magazine already full!")
        self.last_reload_state = current_aruco_data['reloading']
        
        # Get player position for collision detection
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
            if self.health_system.take_damage():
                print("Enemy collision! Defend yourself!")
        
        # Calculate killed enemies and update score
        old_count = len(self.enemies)
        
        # Check if we should give hit points (if enemy health changed, could be complex, 
        # so we just give big points for kills. Wait, let's also give points for killing).
        
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        killed = old_count - len(self.enemies)
        if killed > 0:
            self.score += killed * 100
            print(f"Killed {killed} enemies! Score is now {self.score}")
            for _ in range(killed):
                self.enemies.append(self.spawn_single_enemy())
        
        # Check win condition - game never ends from winning now
        if not self.health_system.is_alive:
            print(f"Game Over! You were overwhelmed by enemies. Final Score: {self.score}")
            self.running = False
    
    def render(self):
        """Render the game"""
        # Clear screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Apply screen shake BEFORE camera transformation
        self.shooting_effects.apply_screen_shake()
        
        # Apply camera transformation (fixed position)
        self.camera.apply()
        
        # Draw environment
        draw_skybox()
        draw_ground()
        
        # Draw cursor target for visualization
        draw_cursor_target(self.quaternion_weapon)
        
        # Draw weapon with current transform
        draw_weapon_model(self.quaternion_weapon, self.weapon_system)
        
        # Render muzzle flash
        self.shooting_effects.render_muzzle_flash()
        
        # Render smoke effects
        self.shooting_effects.render_smoke_effects()
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw()
        
        # Draw UI
        draw_health_bar(self.health_system.get_health_percentage())
        draw_score(self.score)
        draw_title()
        draw_bottom_banner()
        draw_ammo_display(self.weapon_system)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        try:
            print("Starting FULL ArUco control system...")
            print("Use marker movements for aiming, recoil motion for shooting, left fist for reloading!")
            
            while self.running:
                self.handle_events()
                self.update()
                self.render()
                self.clock.tick(60)
        finally:
            # Clean up
            print("Stopping ArUco detection...")
            self.stop_aruco_detection()
            cleanup_sound_system()
            print("Game cleanup complete.")
        
        pygame.quit()

def main():
    print("3D Shooting Game - Full ArUco Control System")
    print("="*60)
    game = Game()
    game.run()

if __name__ == "__main__":
    main()