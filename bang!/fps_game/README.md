# 3D Shooting Game

A 3D shooting game built with Python, Pygame, and OpenGL.

## Features

- Cursor-based aiming system using quaternions
- 3D enemy AI with health systems
- Weapon system with ammo management and reloading
- Collision detection and physics
- 3D model loading (GLB/GLTF format)

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

```bash
python main.py
```

## Controls

- **Mouse**: Aim weapon (cursor tracking)
- **Left Click**: Shoot
- **R**: Manual reload
- **ESC**: Exit game

## Project Structure

```
shooting_game/
├── main.py                 # Game entry point
├── config/                 # Configuration files
├── assets/                 # Game assets (models, textures, sounds)
├── src/                    # Source code
│   ├── core/              # Core game systems
│   ├── entities/          # Game entities (player, enemies)
│   ├── weapons/           # Weapon systems
│   ├── systems/           # Game systems (physics, collision)
│   ├── rendering/         # Rendering systems
│   └── utils/             # Utility functions
├── tests/                 # Test files
└── docs/                  # Documentation
```

## Development

- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation for major changes

## License

This project is for educational purposes.
