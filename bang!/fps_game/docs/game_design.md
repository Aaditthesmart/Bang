# Game Design Document

## Overview

A 3D shooting game where the player must survive waves of AI enemies.

## Core Mechanics

### Aiming System
- Cursor-based aiming using quaternion rotation
- Weapon follows mouse cursor position
- Bullets originate from weapon tip and travel to cursor position

### Weapon System
- Magazine-based ammo system (7 rounds)
- Manual and automatic reloading
- Fire rate limiting
- Visual ammo display

### Enemy AI
- Enemies move toward player
- Randomized health (30-80 HP)
- Speed increases when close to player
- Individual health bars

### Health System
- Player starts with 100 HP
- Damage cooldown prevents spam damage
- Game over when health reaches 0

## Future Features

- Multiple enemy types
- Different weapons
- Power-ups and upgrades
- Sound effects and music
- Particle effects
- Multiple levels/waves
