from src.entities.enemy.enemy_base import EnemyBase
from src.entities.enemy.enemy_ai import EnemyAI
from src.entities.enemy.enemy_rendering import EnemyRenderer
from src.entities.enemy.enemy_physics import EnemyPhysics

class Enemy(EnemyBase):
    """Main Enemy class that combines all enemy functionality"""
    
    def __init__(self, x, y, z, height=3.0, radius=0.8):
        super().__init__(x, y, z, height, radius)
    
    def update(self, player_pos):
        """Update enemy AI - move towards player"""
        EnemyAI.update_movement(self, player_pos)
    
    def draw(self):
        """Draw enemy as a cylinder with health bar above"""
        EnemyRenderer.draw_enemy(self)
    
    def intersects_ray(self, ray_start, ray_dir, max_distance):
        """Ray-cylinder intersection for shooting"""
        return EnemyPhysics.intersects_ray(self, ray_start, ray_dir, max_distance)
    
    # Convenience methods for physics calculations
    def get_distance_to_point(self, point):
        """Calculate 3D distance from enemy center to a point"""
        return EnemyPhysics.get_distance_to_point(self, point)
    
    def get_2d_distance_to_point(self, point):
        """Calculate 2D distance from enemy center to a point (ignoring Y axis)"""
        return EnemyPhysics.get_2d_distance_to_point(self, point)
    
    def check_sphere_collision(self, sphere_center, sphere_radius):
        """Check if enemy collides with a sphere"""
        return EnemyPhysics.check_sphere_collision(self, sphere_center, sphere_radius)
    
    def is_point_inside(self, point):
        """Check if a point is inside the enemy's cylindrical bounds"""
        return EnemyPhysics.is_point_inside_cylinder(self, point)