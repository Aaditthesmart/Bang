def shoot(camera, enemies, weapon_system, quaternion_weapon=None):
    """Handle shooting mechanics using cursor tracking - bullet comes from gun tip and goes to cursor"""
    
    # Check if weapon can shoot
    if not weapon_system.shoot():
        return False
    
    if quaternion_weapon is None:
        # Fallback to original behavior if no quaternion weapon provided
        start_pos = [camera.x, camera.y, camera.z]
        direction = camera.get_forward_vector()
    else:
        # Use weapon tip position and cursor direction
        start_pos = quaternion_weapon.get_weapon_tip_position()
        direction = quaternion_weapon.get_firing_direction()
    
    max_distance = 100.0
    
    # Check for enemy intersections and find the closest one
    closest_enemy = None
    closest_distance = float('inf')
    
    for enemy in enemies:
        if not enemy.alive:
            continue
            
        distance = enemy.intersects_ray(start_pos, direction, max_distance)
        if distance is not None and distance < closest_distance:
            closest_distance = distance
            closest_enemy = enemy
    
    # Damage the closest hit enemy
    if closest_enemy is not None:
        damage = 25  # Standard damage per shot
        was_killed = closest_enemy.take_damage(damage)
        
        if was_killed:
            alive_count = sum(1 for enemy in enemies if enemy.alive)
            print(f"Enemy destroyed! {alive_count} enemies remaining.")
        else:
            health_remaining = closest_enemy.current_health
            print(f"Enemy hit! Health: {health_remaining}/{closest_enemy.max_health}")
    else:
        # Show where the bullet would land for debugging
        if quaternion_weapon:
            cursor_pos = quaternion_weapon.get_cursor_world_position()
            print(f"Shot fired toward cursor at: ({cursor_pos[0]:.1f}, {cursor_pos[1]:.1f}, {cursor_pos[2]:.1f})")
    
    return True