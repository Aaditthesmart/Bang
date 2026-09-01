import math

class EnemyPhysics:
    """Handles enemy physics calculations including ray intersection for shooting"""
    
    @staticmethod
    def intersects_ray(enemy, ray_start, ray_dir, max_distance):
        """Ray-cylinder intersection for shooting"""
        if not enemy.alive:
            return None
        
        # Vector from ray start to cylinder center
        oc_x = ray_start[0] - enemy.x
        oc_y = ray_start[1] - enemy.y
        oc_z = ray_start[2] - enemy.z
        
        # For cylinder intersection, we'll use a simplified approach
        # Project to 2D (ignore Y for cylinder sides initially)
        oc_2d_x = oc_x
        oc_2d_z = oc_z
        ray_2d_x = ray_dir[0]
        ray_2d_z = ray_dir[2]
        
        # Quadratic equation coefficients for 2D circle intersection
        a = ray_2d_x * ray_2d_x + ray_2d_z * ray_2d_z
        b = 2.0 * (oc_2d_x * ray_2d_x + oc_2d_z * ray_2d_z)
        c = oc_2d_x * oc_2d_x + oc_2d_z * oc_2d_z - enemy.radius * enemy.radius
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
        
        if a == 0:  # Ray is parallel to cylinder axis
            # Check if ray is within cylinder radius
            distance_from_axis = math.sqrt(oc_2d_x * oc_2d_x + oc_2d_z * oc_2d_z)
            if distance_from_axis <= enemy.radius:
                # Check Y intersection with cylinder height
                if ray_dir[1] != 0:
                    # Find t values for top and bottom of cylinder
                    t_bottom = (enemy.y - enemy.height/2 - ray_start[1]) / ray_dir[1]
                    t_top = (enemy.y + enemy.height/2 - ray_start[1]) / ray_dir[1]
                    
                    # Check which intersection is valid
                    for t in [t_bottom, t_top]:
                        if 0 <= t <= max_distance:
                            return t
            return None
        
        # Find intersection points with the infinite cylinder
        sqrt_discriminant = math.sqrt(discriminant)
        t1 = (-b - sqrt_discriminant) / (2 * a)
        t2 = (-b + sqrt_discriminant) / (2 * a)
        
        # Check both intersection points
        valid_intersections = []
        for t in [t1, t2]:
            if 0 <= t <= max_distance:
                # Check if intersection is within cylinder height
                y_at_intersection = ray_start[1] + t * ray_dir[1]
                if enemy.y - enemy.height/2 <= y_at_intersection <= enemy.y + enemy.height/2:
                    valid_intersections.append(t)
        
        # Also check intersection with top and bottom caps
        # Bottom cap
        if ray_dir[1] != 0:
            t_bottom = (enemy.y - enemy.height/2 - ray_start[1]) / ray_dir[1]
            if 0 <= t_bottom <= max_distance:
                x_at_bottom = ray_start[0] + t_bottom * ray_dir[0]
                z_at_bottom = ray_start[2] + t_bottom * ray_dir[2]
                distance_from_center = math.sqrt((x_at_bottom - enemy.x)**2 + (z_at_bottom - enemy.z)**2)
                if distance_from_center <= enemy.radius:
                    valid_intersections.append(t_bottom)
            
            # Top cap
            t_top = (enemy.y + enemy.height/2 - ray_start[1]) / ray_dir[1]
            if 0 <= t_top <= max_distance:
                x_at_top = ray_start[0] + t_top * ray_dir[0]
                z_at_top = ray_start[2] + t_top * ray_dir[2]
                distance_from_center = math.sqrt((x_at_top - enemy.x)**2 + (z_at_top - enemy.z)**2)
                if distance_from_center <= enemy.radius:
                    valid_intersections.append(t_top)
        
        # Return the closest valid intersection
        if valid_intersections:
            return min(valid_intersections)
        
        return None
    
    @staticmethod
    def check_sphere_collision(enemy, sphere_center, sphere_radius):
        """Check if enemy collides with a sphere (e.g., explosion damage)"""
        if not enemy.alive:
            return False
            
        # Calculate distance between enemy center and sphere center
        dx = enemy.x - sphere_center[0]
        dy = enemy.y - sphere_center[1]
        dz = enemy.z - sphere_center[2]
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        
        # Check if collision occurs (considering enemy as cylinder approximated as sphere)
        enemy_effective_radius = max(enemy.radius, enemy.height / 2)
        return distance <= (enemy_effective_radius + sphere_radius)
    
    @staticmethod
    def get_distance_to_point(enemy, point):
        """Calculate 3D distance from enemy center to a point"""
        dx = enemy.x - point[0]
        dy = enemy.y - point[1]
        dz = enemy.z - point[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    
    @staticmethod
    def get_2d_distance_to_point(enemy, point):
        """Calculate 2D distance from enemy center to a point (ignoring Y axis)"""
        dx = enemy.x - point[0]
        dz = enemy.z - point[2]
        return math.sqrt(dx * dx + dz * dz)
    
    @staticmethod
    def is_point_inside_cylinder(enemy, point):
        """Check if a point is inside the enemy's cylindrical bounds"""
        if not enemy.alive:
            return False
            
        # Check 2D distance from cylinder axis
        dx = point[0] - enemy.x
        dz = point[2] - enemy.z
        distance_2d = math.sqrt(dx * dx + dz * dz)
        
        if distance_2d > enemy.radius:
            return False
        
        # Check height bounds
        if point[1] < enemy.y - enemy.height/2 or point[1] > enemy.y + enemy.height/2:
            return False
            
        return True