import math

class CollisionSystem:
    @staticmethod
    def check_player_enemy_collision(player_pos, player_radius, enemy):
        """Check if player is colliding with an enemy (cylinder collision)"""
        if not enemy.alive:
            return False
        
        # Calculate 2D distance (ignore Y for cylinder collision)
        dx = player_pos[0] - enemy.x
        dz = player_pos[2] - enemy.z
        distance_2d = math.sqrt(dx * dx + dz * dz)
        
        # Check if player is within the enemy's radius
        collision_distance = player_radius + enemy.radius
        
        if distance_2d <= collision_distance:
            # Check if player is within the enemy's height range
            player_y = player_pos[1]
            enemy_bottom = enemy.y - enemy.height / 2
            enemy_top = enemy.y + enemy.height / 2
            
            # Player collision box (assume player is about 1.8 units tall)
            player_bottom = player_y - 0.9
            player_top = player_y + 0.9
            
            # Check Y overlap
            if player_bottom <= enemy_top and player_top >= enemy_bottom:
                return True
        
        return False
    
    @staticmethod
    def check_multiple_collisions(player_pos, player_radius, enemies):
        """Check collisions with all enemies and return list of colliding enemies"""
        colliding_enemies = []
        
        for enemy in enemies:
            if CollisionSystem.check_player_enemy_collision(player_pos, player_radius, enemy):
                colliding_enemies.append(enemy)
        
        return colliding_enemies
    
    @staticmethod
    def push_player_away(player_pos, enemy, push_strength=0.1):
        """Calculate push vector to move player away from enemy"""
        dx = player_pos[0] - enemy.x
        dz = player_pos[2] - enemy.z
        distance = math.sqrt(dx * dx + dz * dz)
        
        if distance > 0:
            # Normalize and apply push
            push_x = (dx / distance) * push_strength
            push_z = (dz / distance) * push_strength
            return push_x, push_z
        
        return 0, 0