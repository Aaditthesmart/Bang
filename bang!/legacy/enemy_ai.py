import math

class EnemyAI:
    """Handles enemy AI behavior and movement logic"""
    
    @staticmethod
    def update_movement(enemy, player_pos):
        """Update enemy AI - move towards player"""
        if not enemy.alive:
            return
            
        # Calculate direction to player
        dx = player_pos[0] - enemy.x
        dz = player_pos[2] - enemy.z
        
        # Calculate distance to player
        distance = math.sqrt(dx * dx + dz * dz)
        
        # Move towards player (more aggressive when close)
        if distance > 0.8:  # Reduced minimum distance for more aggressive behavior
            # Normalize direction vector
            dx /= distance
            dz /= distance
            
            # Increase speed when close to player for more intense combat
            current_speed = enemy.speed
            if distance < 5.0:
                current_speed *= 1.5  # 50% speed boost when close
            
            # Move towards player
            enemy.x += dx * current_speed
            enemy.z += dz * current_speed
        
        # Keep enemy on ground level
        enemy.y = max(enemy.height/2, enemy.y)
    
    @staticmethod
    def calculate_direction_to_player(enemy, player_pos):
        """Calculate normalized direction vector from enemy to player"""
        dx = player_pos[0] - enemy.x
        dz = player_pos[2] - enemy.z
        distance = math.sqrt(dx * dx + dz * dz)
        
        if distance > 0:
            return dx / distance, dz / distance, distance
        return 0, 0, 0
    
    @staticmethod
    def should_move_toward_player(enemy, player_pos, min_distance=0.8):
        """Determine if enemy should move toward player based on distance"""
        dx = player_pos[0] - enemy.x
        dz = player_pos[2] - enemy.z
        distance = math.sqrt(dx * dx + dz * dz)
        return distance > min_distance
    
    @staticmethod
    def get_speed_multiplier(enemy, player_pos, close_distance=5.0, speed_boost=1.5):
        """Get speed multiplier based on distance to player"""
        dx = player_pos[0] - enemy.x
        dz = player_pos[2] - enemy.z
        distance = math.sqrt(dx * dx + dz * dz)
        
        if distance < close_distance:
            return speed_boost
        return 1.0