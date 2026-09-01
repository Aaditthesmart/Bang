import time
import math
import numpy as np
from OpenGL.GL import *
from src.audio.sound_system import play_reload_sound

class ReloadAnimation:
    """Handles the reload animation using inverse kinematics with two-segment arm"""
    
    def __init__(self, duration=2.0):
        self.duration = duration
        self.is_active = False
        self.start_time = 0
        
        # Store original weapon orientation for smooth transition back
        self.original_quaternion = None
        self.target_quaternion = None  # Forward-facing quaternion during reload
        
        # Smooth gun transition settings
        self.gun_transition_start = None  # Gun position at start of reload
        self.gun_transition_target = None  # Target gun position during reload
        self.gun_smooth_factor = 0.08  # How smooth the gun movement is (lower = smoother)
        
        # Sound effect timing
        self.sound_played = False  # Track if reload sound has been played
        
        # Arm segment lengths - increased for better reach
        self.upper_arm_length = 1.5  # Shoulder to elbow (increased)
        self.forearm_length = 1.4    # Elbow to wrist (increased)
        self.total_reach = self.upper_arm_length + self.forearm_length
        
        # Shoulder position (bottom left, out of view) - lowered significantly
        self.shoulder_offset = np.array([-2.2, -1.5, -0.3])  # Much lower starting position
        
        # Customizable target offsets for fine-tuning reload positions
        self.reload_target_offsets = {
            'approach': np.array([0.15, 0.2, 0]),      # Where arm approaches gun from
            'contact': np.array([-0.1, 0.15, 0]),     # Exact reload contact point on gun
            'pull_back': np.array([-0.35, 0.15, 0]),  # How far to pull slide back
            'release': np.array([0.1, 0.15, 0]),      # Where slide snaps forward to
            'retract_to': np.array([-2.2, -0.8, -1.2]) # Final retract position
        }
        
        # Start position offset (relative to weapon)
        self.start_position_offset = np.array([-1.8, -0.8, -0.8])  # Lower start position
        
        # Animation phases and their durations
        self.phase_durations = {
            'transition_to_center': 0.15,   # 15% - Gun moves to center position
            'reach_in': 0.20,              # 20% - Arm reaches toward gun
            'contact': 0.10,               # 10% - Hand makes contact with slide
            'pull_back': 0.15,             # 15% - Pull slide back (SOUND PLAYS HERE)
            'release': 0.10,               # 10% - Release slide forward
            'retract': 0.15,               # 15% - Arm retracts
            'transition_to_cursor': 0.15    # 15% - Gun returns to cursor position
        }
        
        # Calculate cumulative phase times
        self.phase_times = {}
        cumulative = 0
        for phase, duration in self.phase_durations.items():
            self.phase_times[phase] = {
                'start': cumulative,
                'end': cumulative + duration
            }
            cumulative += duration
    
    def start_animation(self, current_quaternion):
        """Start the reload animation with current weapon quaternion"""
        self.is_active = True
        self.start_time = time.time()
        self.sound_played = False  # Reset sound flag
        
        # Store current quaternion for smooth transition back
        self.original_quaternion = current_quaternion.copy()
        
        # Create forward-facing target quaternion (no rotation from default)
        self.target_quaternion = np.array([1.0, 0.0, 0.0, 0.0])  # Identity quaternion
        
        # Set up smooth gun transition
        self.gun_transition_start = current_quaternion.copy()
        self.gun_transition_target = self.target_quaternion.copy()
    
    def update(self):
        """Update animation state and handle sound timing"""
        if not self.is_active:
            return
            
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.is_active = False
            self.sound_played = False  # Reset for next reload
            return
        
        # Check if we should play the reload sound during pull_back phase
        current_phase = self.get_current_phase()
        if current_phase == 'pull_back' and not self.sound_played:
            # Play sound at the start of pull_back phase
            phase_progress = self.get_phase_progress('pull_back')
            if phase_progress >= 0.1:  # Play sound 10% into the pull_back phase
                play_reload_sound()
                self.sound_played = True
                print("Reload sound triggered during slide pull!")
    
    def get_progress(self):
        """Get overall animation progress (0.0 to 1.0)"""
        if not self.is_active:
            return 1.0
            
        elapsed = time.time() - self.start_time
        return min(elapsed / self.duration, 1.0)
    
    def get_current_phase(self):
        """Get the current animation phase"""
        if not self.is_active:
            return None
            
        progress = self.get_progress()
        
        for phase, times in self.phase_times.items():
            if times['start'] <= progress <= times['end']:
                return phase
                
        return 'transition_to_cursor'  # Fallback to last phase
    
    def get_phase_progress(self, phase):
        """Get progress within a specific phase (0.0 to 1.0)"""
        overall_progress = self.get_progress()
        phase_info = self.phase_times[phase]
        
        if overall_progress < phase_info['start']:
            return 0.0
        elif overall_progress > phase_info['end']:
            return 1.0
        else:
            phase_duration = phase_info['end'] - phase_info['start']
            phase_elapsed = overall_progress - phase_info['start']
            return phase_elapsed / phase_duration if phase_duration > 0 else 1.0
    
    def get_weapon_transition_quaternion(self, current_quaternion):
        """Get interpolated quaternion for smooth weapon transition during reload"""
        if not self.is_active:
            return current_quaternion
            
        overall_progress = self.get_progress()
        
        # During transition_to_center phase - smooth transition to center
        if overall_progress <= self.phase_times['transition_to_center']['end']:
            phase_progress = self.get_phase_progress('transition_to_center')
            eased_progress = self._ease_in_out_cubic(phase_progress)
            return self._slerp_quaternions(self.original_quaternion, self.target_quaternion, eased_progress)
        
        # During main animation phases (gun stays in center with slight movement)
        elif overall_progress <= self.phase_times['retract']['end']:
            # Add subtle gun movement during arm animation for realism
            current_phase = self.get_current_phase()
            phase_progress = self.get_phase_progress(current_phase)
            
            # Small movements during different phases
            movement_offset = np.array([0.0, 0.0, 0.0, 0.0])  # Base quaternion offset
            
            if current_phase == 'contact':
                # Slight forward tilt when hand contacts
                tilt_amount = phase_progress * 0.05
                movement_offset = self._create_rotation_quaternion([1, 0, 0], tilt_amount)
            elif current_phase == 'pull_back':
                # Slight backward tilt when pulling slide
                tilt_amount = phase_progress * 0.08
                movement_offset = self._create_rotation_quaternion([1, 0, 0], -tilt_amount)
            elif current_phase == 'release':
                # Slight forward snap when releasing
                snap_amount = (1.0 - phase_progress) * 0.06
                movement_offset = self._create_rotation_quaternion([1, 0, 0], snap_amount)
            
            # Combine target quaternion with movement
            return self._combine_quaternions(self.target_quaternion, movement_offset)
        
        # During transition_to_cursor phase - smooth transition back to original
        else:
            phase_progress = self.get_phase_progress('transition_to_cursor')
            eased_progress = self._ease_in_out_cubic(phase_progress)
            return self._slerp_quaternions(self.target_quaternion, self.original_quaternion, eased_progress)
    
    def get_target_hand_position(self, weapon_position):
        """Get target position for hand based on current animation phase - uses actual gun position"""
        current_phase = self.get_current_phase()
        if not current_phase:
            return None
        
        # Use the actual weapon position as the reload target
        # This ensures the arm reaches exactly where the gun is
        gun_reload_pos = np.array([
            weapon_position[0] - 0.0,  # Slightly behind gun (slide area)
            weapon_position[1] + 0.4, # Slightly above gun center
            weapon_position[2] + 0.1        # Exact same depth as gun
        ])
        
        if current_phase == 'reach_in':
            # Move from start position toward gun
            progress = self.get_phase_progress('reach_in')
            eased_progress = self._ease_in_out_cubic(progress)
            
            # Start position further left and lower
            start_pos = np.array([
                weapon_position[0] - 1.8, 
                weapon_position[1] - 0.3, 
                weapon_position[2] - 0.8
            ])
            # Approach position near the gun
            target_pos = gun_reload_pos + np.array([0.15, 0, 0])
            
            return start_pos + (target_pos - start_pos) * eased_progress
            
        elif current_phase == 'contact':
            # Move to exact contact with gun slide
            progress = self.get_phase_progress('contact')
            eased_progress = self._ease_in_out_cubic(progress)
            
            approach_pos = gun_reload_pos + np.array([0.15, 0, 0])
            contact_pos = gun_reload_pos  # Exact gun position
            
            return approach_pos + (contact_pos - approach_pos) * eased_progress
            
        elif current_phase == 'pull_back':
            # Pull slide backward from gun position
            progress = self.get_phase_progress('pull_back')
            eased_progress = self._ease_in_out_cubic(progress)
            
            contact_pos = gun_reload_pos
            pulled_pos = gun_reload_pos + np.array([-0.25, 0, 0])  # Pull back from gun
            
            return contact_pos + (pulled_pos - contact_pos) * eased_progress
            
        elif current_phase == 'release':
            # Release slide forward relative to gun position
            progress = self.get_phase_progress('release')
            eased_progress = self._ease_out_bounce(progress)  # Bouncy release
            
            pulled_pos = gun_reload_pos + np.array([-0.25, 0, 0])
            released_pos = gun_reload_pos + np.array([0.1, 0, 0])  # Forward from gun
            
            return pulled_pos + (released_pos - pulled_pos) * eased_progress
            
        elif current_phase == 'retract':
            # Retract hand away from gun position
            progress = self.get_phase_progress('retract')
            eased_progress = self._ease_in_out_cubic(progress)
            
            released_pos = gun_reload_pos + np.array([0.1, 0, 0])
            retract_pos = np.array([
                weapon_position[0] - 2.2, 
                weapon_position[1] - 0.5, 
                weapon_position[2] - 1.2
            ])
            
            return released_pos + (retract_pos - released_pos) * eased_progress
            
        return None
    
    def solve_ik(self, shoulder_pos, target_pos):
        """Solve inverse kinematics for two-segment arm"""
        # Vector from shoulder to target
        to_target = target_pos - shoulder_pos
        distance = np.linalg.norm(to_target)
        
        # Check if target is reachable
        if distance > self.total_reach:
            # Target too far, extend arm fully toward target
            direction = to_target / distance
            elbow_pos = shoulder_pos + direction * self.upper_arm_length
            wrist_pos = shoulder_pos + direction * self.total_reach
            return elbow_pos, wrist_pos, True  # Fully extended
            
        elif distance < abs(self.upper_arm_length - self.forearm_length):
            # Target too close, fold arm
            direction = to_target / max(distance, 0.001)  # Avoid division by zero
            elbow_pos = shoulder_pos + direction * self.upper_arm_length
            wrist_pos = target_pos
            return elbow_pos, wrist_pos, True  # Folded
        
        # Normal IK solution using law of cosines
        # Calculate elbow angle
        cos_elbow = (self.upper_arm_length**2 + self.forearm_length**2 - distance**2) / (2 * self.upper_arm_length * self.forearm_length)
        cos_elbow = max(-1.0, min(1.0, cos_elbow))  # Clamp to valid range
        elbow_angle = math.acos(cos_elbow)
        
        # Calculate shoulder angle
        cos_shoulder = (self.upper_arm_length**2 + distance**2 - self.forearm_length**2) / (2 * self.upper_arm_length * distance)
        cos_shoulder = max(-1.0, min(1.0, cos_shoulder))
        shoulder_angle = math.acos(cos_shoulder)
        
        # Direction from shoulder to target
        direction = to_target / distance
        
        # For natural arm movement, bend elbow upward
        # Create perpendicular vector for elbow offset
        up_vector = np.array([0, 1, 0])
        side_vector = np.cross(direction, up_vector)
        if np.linalg.norm(side_vector) < 0.1:  # Direction is vertical
            side_vector = np.array([1, 0, 0])
        else:
            side_vector = side_vector / np.linalg.norm(side_vector)
        
        elbow_offset = np.cross(side_vector, direction)
        elbow_offset = elbow_offset / np.linalg.norm(elbow_offset)
        
        # Calculate elbow position
        base_elbow = shoulder_pos + direction * self.upper_arm_length * math.cos(shoulder_angle)
        elbow_height = self.upper_arm_length * math.sin(shoulder_angle)
        elbow_pos = base_elbow + elbow_offset * elbow_height
        
        return elbow_pos, target_pos, False  # Normal solution
    
    def get_arm_segments(self, weapon_position):
        """Get arm segment positions using inverse kinematics"""
        if not self.is_active:
            return None
            
        current_phase = self.get_current_phase()
        if current_phase in ['transition_to_center', 'transition_to_cursor']:
            return None
        
        # Get shoulder position in world space
        shoulder_pos = np.array(weapon_position) + self.shoulder_offset
        
        # Get target hand position
        target_pos = self.get_target_hand_position(weapon_position)
        if target_pos is None:
            return None
        
        # Solve IK
        elbow_pos, wrist_pos, is_limit = self.solve_ik(shoulder_pos, target_pos)
        
        return {
            'shoulder_pos': shoulder_pos,
            'elbow_pos': elbow_pos,
            'wrist_pos': wrist_pos,
            'upper_arm_length': self.upper_arm_length,
            'forearm_length': self.forearm_length,
            'is_at_limit': is_limit,
            'phase': current_phase
        }
    
    def render_arm(self, weapon_position):
        """Render the two-segment arm using thick square prisms only"""
        if not self.is_active:
            return
            
        arm_data = self.get_arm_segments(weapon_position)
        if not arm_data:
            return
        
        shoulder_pos = arm_data['shoulder_pos']
        elbow_pos = arm_data['elbow_pos']
        wrist_pos = arm_data['wrist_pos']
        
        # Set arm material (beige/skin color)
        glDisable(GL_COLOR_MATERIAL)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.8, 0.7, 0.6, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.9, 0.8, 0.7, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 16.0)
        
        # Render upper arm as thick square prism (shoulder to elbow)
        # Increased size: was 0.12 width, 0.08 height - now much thicker and square
        self._render_square_segment(shoulder_pos, elbow_pos, 0.25)
        
        # Render forearm as thick square prism (elbow to wrist)
        # Increased size: was 0.10 width, 0.06 height - now thicker and square
        self._render_square_segment(elbow_pos, wrist_pos, 0.15)
        
        glEnable(GL_COLOR_MATERIAL)
    
    def _render_square_segment(self, start_pos, end_pos, size):
        """Render an arm segment as a thick square prism between two points"""
        direction = end_pos - start_pos
        length = np.linalg.norm(direction)
        if length < 0.001:
            return
        
        direction = direction / length
        
        # Calculate center position
        center_pos = start_pos + direction * (length / 2)
        
        # Create rotation matrix to align with direction
        # Default direction is along Z-axis
        default_dir = np.array([0, 0, 1])
        
        # Calculate rotation axis and angle
        axis = np.cross(default_dir, direction)
        
        glPushMatrix()
        glTranslatef(center_pos[0], center_pos[1], center_pos[2])
        
        if np.linalg.norm(axis) > 0.001:
            axis = axis / np.linalg.norm(axis)
            angle = math.acos(max(-1, min(1, np.dot(default_dir, direction))))
            glRotatef(math.degrees(angle), axis[0], axis[1], axis[2])
        elif np.dot(default_dir, direction) < 0:
            # 180-degree rotation case
            glRotatef(180, 1, 0, 0)
        
        # Draw thick square prism - all dimensions are equal for perfect square cross-section
        half_size = size / 2
        half_length = length / 2
        
        glBegin(GL_QUADS)
        
        # Front face (positive Z)
        glNormal3f(0, 0, 1)
        glVertex3f(-half_size, -half_size, half_length)
        glVertex3f(half_size, -half_size, half_length)
        glVertex3f(half_size, half_size, half_length)
        glVertex3f(-half_size, half_size, half_length)
        
        # Back face (negative Z)
        glNormal3f(0, 0, -1)
        glVertex3f(-half_size, -half_size, -half_length)
        glVertex3f(-half_size, half_size, -half_length)
        glVertex3f(half_size, half_size, -half_length)
        glVertex3f(half_size, -half_size, -half_length)
        
        # Top face (positive Y)
        glNormal3f(0, 1, 0)
        glVertex3f(-half_size, half_size, -half_length)
        glVertex3f(-half_size, half_size, half_length)
        glVertex3f(half_size, half_size, half_length)
        glVertex3f(half_size, half_size, -half_length)
        
        # Bottom face (negative Y)
        glNormal3f(0, -1, 0)
        glVertex3f(-half_size, -half_size, -half_length)
        glVertex3f(half_size, -half_size, -half_length)
        glVertex3f(half_size, -half_size, half_length)
        glVertex3f(-half_size, -half_size, half_length)
        
        # Right face (positive X)
        glNormal3f(1, 0, 0)
        glVertex3f(half_size, -half_size, -half_length)
        glVertex3f(half_size, half_size, -half_length)
        glVertex3f(half_size, half_size, half_length)
        glVertex3f(half_size, -half_size, half_length)
        
        # Left face (negative X)
        glNormal3f(-1, 0, 0)
        glVertex3f(-half_size, -half_size, -half_length)
        glVertex3f(-half_size, -half_size, half_length)
        glVertex3f(-half_size, half_size, half_length)
        glVertex3f(-half_size, half_size, -half_length)
        
        glEnd()
        
        glPopMatrix()
    
    def _ease_in_out(self, t):
        """Smooth easing function for natural movement"""
        return t * t * (3.0 - 2.0 * t)
    
    def _ease_in_out_cubic(self, t):
        """Smoother cubic easing for gun transitions"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def _ease_out_bounce(self, t):
        """Bouncy easing for slide release"""
        if t < 1/2.75:
            return 7.5625 * t * t
        elif t < 2/2.75:
            return 7.5625 * (t - 1.5/2.75) * t + 0.75
        elif t < 2.5/2.75:
            return 7.5625 * (t - 2.25/2.75) * t + 0.9375
        else:
            return 7.5625 * (t - 2.625/2.75) * t + 0.984375
    
    def _create_rotation_quaternion(self, axis, angle):
        """Create a quaternion from axis and angle"""
        axis = np.array(axis, dtype=float)
        axis = axis / np.linalg.norm(axis)  # Normalize
        
        half_angle = angle / 2.0
        sin_half = math.sin(half_angle)
        cos_half = math.cos(half_angle)
        
        return np.array([
            cos_half,
            axis[0] * sin_half,
            axis[1] * sin_half,
            axis[2] * sin_half
        ])
    
    def _combine_quaternions(self, q1, q2):
        """Multiply two quaternions to combine rotations"""
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        return np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        ])
    
    def _slerp_quaternions(self, q1, q2, t):
        """Spherical linear interpolation between two quaternions"""
        # Normalize quaternions
        q1 = q1 / np.linalg.norm(q1)
        q2 = q2 / np.linalg.norm(q2)
        
        # Calculate dot product
        dot = np.dot(q1, q2)
        
        # If dot product is negative, slerp won't take the shorter path
        if dot < 0.0:
            q2 = -q2
            dot = -dot
        
        # If quaternions are very close, use linear interpolation
        if dot > 0.9995:
            result = q1 + t * (q2 - q1)
            return result / np.linalg.norm(result)
        
        # Calculate angle between quaternions
        theta_0 = math.acos(abs(dot))
        theta = theta_0 * t
        
        # Calculate orthogonal quaternion
        q2_orth = q2 - q1 * dot
        q2_orth = q2_orth / np.linalg.norm(q2_orth)
        
        # Perform slerp
        return q1 * math.cos(theta) + q2_orth * math.sin(theta)