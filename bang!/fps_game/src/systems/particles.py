import time
import math
import random
import numpy as np
from OpenGL.GL import *

class ShootingEffects:
    """Handles visual effects for shooting: muzzle flash, smoke, and screen shake"""
    
    def __init__(self):
        # Muzzle flash settings
        self.muzzle_flash_active = False
        self.muzzle_flash_start_time = 0
        self.muzzle_flash_duration = 0.08  # 80ms flash duration
        self.muzzle_flash_intensity = 1.0
        self.muzzle_flash_position = np.array([0.0, 0.0, 0.0])
        self.muzzle_flash_direction = np.array([0.0, 0.0, -1.0])
        
        # Smoke effect settings
        self.smoke_particles = []
        self.max_smoke_particles = 15
        self.smoke_lifetime = 2.0  # 2 seconds
        
        # Screen shake settings
        self.screen_shake_active = False
        self.screen_shake_start_time = 0
        self.screen_shake_duration = 0.25  # Longer duration for recoil
        self.screen_shake_intensity = 1.2  # Stronger intensity
        self.shake_offset = np.array([0.0, 0.0, 0.0])
        self.recoil_recovery_factor = 0.3  # How much the gun settles back down
        
        # Flash colors for different intensities
        self.flash_colors = {
            'bright': [1.0, 0.9, 0.3],    # Bright yellow-white
            'medium': [1.0, 0.6, 0.2],    # Orange-yellow
            'dim': [0.8, 0.3, 0.1]        # Orange-red
        }
    
    def trigger_shooting_effects(self, weapon_tip_position, weapon_direction):
        """Trigger all shooting effects: muzzle flash, smoke, and screen shake"""
        current_time = time.time()
        
        # Start muzzle flash
        self.muzzle_flash_active = True
        self.muzzle_flash_start_time = current_time
        self.muzzle_flash_intensity = 1.0
        
        # Start screen shake
        self.screen_shake_active = True
        self.screen_shake_start_time = current_time
        
        # Store weapon tip position and direction for rendering
        self.muzzle_flash_position = np.array(weapon_tip_position).copy()
        self.muzzle_flash_direction = np.array(weapon_direction).copy()
        
        # Create smoke particles at weapon tip
        self._create_smoke_burst(weapon_tip_position, weapon_direction)
        
        print("Shooting effects triggered: muzzle flash, smoke, and screen shake!")
    
    def update(self):
        """Update all visual effects (call every frame)"""
        current_time = time.time()
        
        # Update muzzle flash
        if self.muzzle_flash_active:
            elapsed = current_time - self.muzzle_flash_start_time
            if elapsed >= self.muzzle_flash_duration:
                self.muzzle_flash_active = False
                self.muzzle_flash_intensity = 0.0
            else:
                # Fade out flash intensity over time
                progress = elapsed / self.muzzle_flash_duration
                self.muzzle_flash_intensity = 1.0 - (progress * progress)  # Quadratic fade
        
        # Update screen shake
        if self.screen_shake_active:
            elapsed = current_time - self.screen_shake_start_time
            if elapsed >= self.screen_shake_duration:
                self.screen_shake_active = False
                self.shake_offset = np.array([0.0, 0.0, 0.0])
            else:
                # Calculate recoil pattern (upward kick followed by recovery)
                progress = elapsed / self.screen_shake_duration
                
                # Recoil phases
                if progress < 0.2:  # Initial upward kick (first 20%)
                    kick_progress = progress / 0.2
                    intensity = self.screen_shake_intensity * (1.0 - kick_progress * 0.3)  # Strong start, slight decrease
                    
                    # Strong upward recoil with slight backward movement
                    self.shake_offset = np.array([
                        random.uniform(-0.3, 0.3) * intensity * 0.01,     # Slight horizontal variation
                        intensity * 0.025 * (1.0 + kick_progress * 0.5),  # Strong upward kick
                        intensity * 0.015 * kick_progress                   # Slight backward movement
                    ])
                    
                elif progress < 0.6:  # Recovery phase (20% to 60%)
                    recovery_progress = (progress - 0.2) / 0.4
                    intensity = self.screen_shake_intensity * (0.7 - recovery_progress * 0.4)  # Gradual decrease
                    
                    # Camera settling back down with oscillation
                    oscillation = math.sin(recovery_progress * math.pi * 4) * (1.0 - recovery_progress)
                    
                    self.shake_offset = np.array([
                        random.uniform(-0.2, 0.2) * intensity * 0.008,     # Reduced horizontal shake
                        intensity * 0.015 * oscillation,                   # Oscillating vertical movement
                        intensity * 0.01 * (1.0 - recovery_progress)       # Return from backward movement
                    ])
                    
                else:  # Final settle (60% to 100%)
                    settle_progress = (progress - 0.6) / 0.4
                    intensity = self.screen_shake_intensity * 0.3 * (1.0 - settle_progress)  # Final fade
                    
                    # Very subtle final movements
                    self.shake_offset = np.array([
                        random.uniform(-0.1, 0.1) * intensity * 0.005,     # Minimal horizontal
                        intensity * 0.008 * (1.0 - settle_progress),       # Settling down
                        0.0                                                 # No backward movement
                    ])
        
        # Update smoke particles
        self._update_smoke_particles()
    
    def apply_screen_shake(self):
        """Apply screen shake transformation (call before rendering scene)"""
        if self.screen_shake_active:
            # Apply translation shake
            glTranslatef(self.shake_offset[0], self.shake_offset[1], self.shake_offset[2])
            
            # Add subtle rotational recoil for more realism
            elapsed = time.time() - self.screen_shake_start_time
            progress = elapsed / self.screen_shake_duration
            
            if progress < 0.3:  # Initial recoil rotation
                kick_intensity = (1.0 - progress / 0.3) * 0.8
                # Slight upward rotation (pitch) and random roll
                pitch_rotation = kick_intensity * 1.2  # Degrees
                roll_rotation = kick_intensity * random.uniform(-0.8, 0.8)
                
                glRotatef(pitch_rotation, 1, 0, 0)  # Pitch up
                glRotatef(roll_rotation, 0, 0, 1)   # Roll left/right
                
            elif progress < 0.7:  # Recovery rotation
                recovery_progress = (progress - 0.3) / 0.4
                settle_intensity = 0.8 * (1.0 - recovery_progress)
                oscillation = math.sin(recovery_progress * math.pi * 3) * settle_intensity
                
                glRotatef(oscillation * 0.6, 1, 0, 0)  # Settling pitch oscillation
                glRotatef(oscillation * 0.3, 0, 0, 1)  # Settling roll oscillation
    
    def render_muzzle_flash(self, weapon_tip_position=None, weapon_direction=None):
        """Render muzzle flash effect at weapon tip"""
        if not self.muzzle_flash_active:
            return
        
        # Use stored position and direction from when effect was triggered
        flash_position = self.muzzle_flash_position
        flash_direction = self.muzzle_flash_direction
        
        # Save current state
        glPushMatrix()
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for bright flash
        glDepthMask(GL_FALSE)  # Don't write to depth buffer
        
        # Position flash at weapon tip
        glTranslatef(flash_position[0], flash_position[1], flash_position[2])
        
        # Align flash with weapon direction
        self._align_with_direction(flash_direction)
        
        # Choose flash color based on intensity
        if self.muzzle_flash_intensity > 0.7:
            color = self.flash_colors['bright']
        elif self.muzzle_flash_intensity > 0.3:
            color = self.flash_colors['medium']
        else:
            color = self.flash_colors['dim']
        
        alpha = self.muzzle_flash_intensity * 0.8
        glColor4f(color[0], color[1], color[2], alpha)
        
        # Render flash as multiple overlapping shapes for realistic look
        self._render_flash_core()
        self._render_flash_spikes()
        
        # Restore state
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glPopMatrix()
    
    def render_smoke_effects(self):
        """Render all smoke particles"""
        if not self.smoke_particles:
            return
        
        glPushMatrix()
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        
        for particle in self.smoke_particles:
            self._render_smoke_particle(particle)
        
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glPopMatrix()
    
    def _create_smoke_burst(self, position, direction):
        """Create a burst of smoke particles"""
        current_time = time.time()
        
        # Create 4-6 smoke particles (much smaller burst)
        num_particles = random.randint(4, 6)
        
        for i in range(num_particles):
            # Random velocity with forward bias
            base_velocity = np.array(direction) * random.uniform(0.5, 1.2)  # Much slower
            
            # Add random spread
            spread = np.array([
                random.uniform(-0.3, 0.3),  # Much tighter spread
                random.uniform(-0.2, 0.5),  # Slight upward bias
                random.uniform(-0.3, 0.3)
            ]) * 0.4  # Much smaller spread multiplier
            
            velocity = base_velocity + spread
            
            particle = {
                'position': np.array(position) + np.random.uniform(-0.01, 0.01, 3),  # Very tight spawn area
                'velocity': velocity,
                'size': random.uniform(0.02, 0.08),  # Much smaller initial size
                'max_size': random.uniform(0.2, 0.4),  # Much smaller maximum size
                'life': 0.0,
                'max_life': random.uniform(1.0, 1.5),  # Shorter life
                'birth_time': current_time,
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-60, 60)  # Slower rotation
            }
            
            self.smoke_particles.append(particle)
        
        # Remove old particles if we have too many
        if len(self.smoke_particles) > self.max_smoke_particles:
            # Remove oldest particles
            self.smoke_particles = self.smoke_particles[-self.max_smoke_particles:]
    
    def _update_smoke_particles(self):
        """Update all smoke particles"""
        current_time = time.time()
        dt = 1.0 / 60.0  # Assume 60 FPS
        
        particles_to_remove = []
        
        for i, particle in enumerate(self.smoke_particles):
            # Update lifetime
            particle['life'] = current_time - particle['birth_time']
            
            # Remove expired particles
            if particle['life'] >= particle['max_life']:
                particles_to_remove.append(i)
                continue
            
            # Update position
            particle['position'] += particle['velocity'] * dt
            
            # Apply gravity and air resistance
            particle['velocity'][1] += 2.0 * dt  # Gravity (upward positive)
            particle['velocity'] *= 0.98  # Air resistance
            
            # Update size (grows over time)
            life_progress = particle['life'] / particle['max_life']
            particle['size'] = particle['max_size'] * (0.1 + 0.9 * life_progress)
            
            # Update rotation
            particle['rotation'] += particle['rotation_speed'] * dt
        
        # Remove expired particles (in reverse order to avoid index issues)
        for i in reversed(particles_to_remove):
            del self.smoke_particles[i]
    
    def _render_smoke_particle(self, particle):
        """Render a single smoke particle"""
        life_progress = particle['life'] / particle['max_life']
        
        # Calculate alpha (fades out over time)
        if life_progress < 0.1:
            alpha = life_progress / 0.1  # Fade in
        elif life_progress > 0.7:
            alpha = (1.0 - life_progress) / 0.3  # Fade out
        else:
            alpha = 1.0  # Full opacity
        
        alpha *= 0.6  # Overall transparency
        
        # Smoke color (gray with slight yellow tint)
        glColor4f(0.7, 0.7, 0.6, alpha)
        
        glPushMatrix()
        glTranslatef(particle['position'][0], particle['position'][1], particle['position'][2])
        glRotatef(particle['rotation'], 0, 0, 1)
        
        # Render as textured quad
        size = particle['size']
        glBegin(GL_QUADS)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)
        glEnd()
        
        glPopMatrix()
    
    def _align_with_direction(self, direction):
        """Align current transformation with given direction"""
        # Normalize direction
        direction = np.array(direction)
        if np.linalg.norm(direction) > 0:
            direction = direction / np.linalg.norm(direction)
        
        # Default direction is along negative Z
        default_dir = np.array([0, 0, -1])
        
        # Calculate rotation
        axis = np.cross(default_dir, direction)
        if np.linalg.norm(axis) > 0.001:
            axis = axis / np.linalg.norm(axis)
            angle = math.acos(max(-1, min(1, np.dot(default_dir, direction))))
            glRotatef(math.degrees(angle), axis[0], axis[1], axis[2])
        elif np.dot(default_dir, direction) < 0:
            glRotatef(180, 1, 0, 0)
    
    def _render_flash_core(self):
        """Render the core muzzle flash (bright center)"""
        # Main flash body - even smaller scale
        scale = 0.1 + self.muzzle_flash_intensity * 0.15  # Reduced further
        glPushMatrix()
        glScalef(scale, scale, scale * 1.0)  # Less depth extension
        
        glBegin(GL_QUADS)
        # Front face
        glVertex3f(-1, -1, 0.2)  # Reduced depth
        glVertex3f(1, -1, 0.2)
        glVertex3f(1, 1, 0.2)
        glVertex3f(-1, 1, 0.2)
        
        # Extending backward
        glVertex3f(-0.4, -0.4, -0.3)  # Even smaller and less depth
        glVertex3f(0.4, -0.4, -0.3)
        glVertex3f(0.4, 0.4, -0.3)
        glVertex3f(-0.4, 0.4, -0.3)
        glEnd()
        
        glPopMatrix()
    
    def _render_flash_spikes(self):
        """Render spiky edges of muzzle flash for realistic look"""
        spike_count = 5  # Even fewer spikes
        spike_length = 0.2 + self.muzzle_flash_intensity * 0.15  # Smaller spikes
        
        glBegin(GL_TRIANGLES)
        for i in range(spike_count):
            angle = (2 * math.pi * i) / spike_count
            
            # Inner point
            inner_x = 0.08 * math.cos(angle)  # Smaller inner radius
            inner_y = 0.08 * math.sin(angle)
            
            # Outer point
            outer_x = spike_length * math.cos(angle)
            outer_y = spike_length * math.sin(angle)
            
            # Next inner point
            next_angle = (2 * math.pi * (i + 1)) / spike_count
            next_inner_x = 0.08 * math.cos(next_angle)
            next_inner_y = 0.08 * math.sin(next_angle)
            
            # Triangle spike
            glVertex3f(inner_x, inner_y, 0.08)
            glVertex3f(outer_x, outer_y, 0.04)
            glVertex3f(next_inner_x, next_inner_y, 0.08)
        glEnd()
    
    def is_any_effect_active(self):
        """Check if any visual effect is currently active"""
        return (self.muzzle_flash_active or 
                self.screen_shake_active or 
                len(self.smoke_particles) > 0)
    
    def get_effects_info(self):
        """Get debug information about active effects"""
        return {
            'muzzle_flash': self.muzzle_flash_active,
            'screen_shake': self.screen_shake_active,
            'smoke_particles': len(self.smoke_particles),
            'shake_intensity': np.linalg.norm(self.shake_offset) if self.screen_shake_active else 0.0
        }