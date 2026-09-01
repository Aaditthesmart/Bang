# Game Controls

## Mouse Controls
- **Mouse Movement**: Aim weapon
- **Left Click**: Fire weapon
- **Mouse Cursor**: Determines bullet trajectory

## Keyboard Controls
- **R**: Manual reload weapon
- **ESC**: Exit game

## Gameplay Tips

1. **Aiming**: The weapon automatically tracks your mouse cursor
2. **Ammo Management**: Watch your ammo counter and reload strategically
3. **Enemy Behavior**: Enemies move faster when they get close
4. **Health**: Avoid enemy contact to preserve health
5. **Positioning**: Use cursor aiming to engage enemies at range

## Technical Notes

- The game uses quaternion-based rotation for smooth weapon tracking
- Bullets travel from the weapon tip to the cursor's world position
- Collision detection uses ray-cylinder intersection for accurate hits
