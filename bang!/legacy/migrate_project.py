#!/usr/bin/env python3
"""
Migration script to reorganize the 3D shooting game project structure.
This script will:
1. Create the new directory structure
2. Move files to their new locations
3. Update import statements throughout the codebase
4. Create necessary __init__.py files
5. Create configuration and requirements files
"""

import os
import shutil
import re
from pathlib import Path

class ProjectMigrator:
    def __init__(self, source_dir=".", target_dir="shooting_game"):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        
        # Define the new directory structure
        self.directories = [
            "config",
            "assets/models",
            "assets/textures", 
            "assets/sounds",
            "src/core",
            "src/entities/enemy",
            "src/entities/player",
            "src/weapons",
            "src/systems/physics",
            "src/rendering",
            "src/utils",
            "tests/unit_tests",
            "docs"
        ]
        
        # Define file mappings: source_file -> destination_path
        self.file_mappings = {
            # Main entry point
            "game.py": "main.py",
            
            # Core systems
            "camera.py": "src/core/camera.py",
            "render.py": "src/core/render.py",
            
            # Enemy system
            "enemy.py": "src/entities/enemy/enemy.py",
            "enemy_ai.py": "src/entities/enemy/enemy_ai.py",
            "enemy_base.py": "src/entities/enemy/enemy_base.py",
            "enemy_physics.py": "src/entities/enemy/enemy_physics.py",
            "enemy_rendering.py": "src/entities/enemy/enemy_rendering.py",
            
            # Player systems
            "health.py": "src/entities/player/health.py",
            
            # Weapon systems
            "cursor_weapon.py": "src/weapons/cursor_weapon.py",
            "weapon.py": "src/weapons/weapon.py",
            "weapon_system.py": "src/weapons/weapon_system.py",
            
            # Game systems
            "collision.py": "src/systems/collision.py",
            
            # Rendering
            "environment.py": "src/rendering/environment.py",
            "model_loader.py": "src/rendering/model_loader.py",
            "ui.py": "src/rendering/ui.py",
            
            # Assets
            "pistol.glb": "assets/models/pistol.glb",
            
            # Tests
            "test_pistol_loading.py": "tests/test_pistol_loading.py"
        }
        
        # Define import mappings: old_import -> new_import
        self.import_mappings = {
            "from camera import": "from src.core.camera import",
            "from render import": "from src.core.render import",
            "from enemy import": "from src.entities.enemy.enemy import",
            "from enemy_ai import": "from src.entities.enemy.enemy_ai import",
            "from enemy_base import": "from src.entities.enemy.enemy_base import",
            "from enemy_physics import": "from src.entities.enemy.enemy_physics import",
            "from enemy_rendering import": "from src.entities.enemy.enemy_rendering import",
            "from health import": "from src.entities.player.health import",
            "from cursor_weapon import": "from src.weapons.cursor_weapon import",
            "from weapon import": "from src.weapons.weapon import",
            "from weapon_system import": "from src.weapons.weapon_system import",
            "from collision import": "from src.systems.collision import",
            "from environment import": "from src.rendering.environment import",
            "from model_loader import": "from src.rendering.model_loader import",
            "from ui import": "from src.rendering.ui import",
        }
    
    def create_directory_structure(self):
        """Create the new directory structure."""
        print("Creating directory structure...")
        
        # Create base directory
        self.target_dir.mkdir(exist_ok=True)
        
        # Create all subdirectories
        for directory in self.directories:
            dir_path = self.target_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
        
        # Create __init__.py files
        init_paths = [
            "src/__init__.py",
            "src/core/__init__.py",
            "src/entities/__init__.py",
            "src/entities/enemy/__init__.py",
            "src/entities/player/__init__.py",
            "src/weapons/__init__.py",
            "src/systems/__init__.py",
            "src/systems/physics/__init__.py",
            "src/rendering/__init__.py",
            "src/utils/__init__.py",
            "config/__init__.py",
            "tests/__init__.py",
            "tests/unit_tests/__init__.py"
        ]
        
        for init_path in init_paths:
            init_file = self.target_dir / init_path
            init_file.touch()
            print(f"  Created: {init_file}")
    
    def move_files(self):
        """Move files to their new locations."""
        print("\nMoving files...")
        
        for source_file, dest_path in self.file_mappings.items():
            source_path = self.source_dir / source_file
            dest_full_path = self.target_dir / dest_path
            
            if source_path.exists():
                # Ensure destination directory exists
                dest_full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file (don't remove original yet)
                shutil.copy2(source_path, dest_full_path)
                print(f"  Moved: {source_file} -> {dest_path}")
            else:
                print(f"  Warning: {source_file} not found, skipping...")
    
    def update_imports(self):
        """Update import statements in all Python files."""
        print("\nUpdating import statements...")
        
        # Find all Python files in the new structure
        python_files = list(self.target_dir.rglob("*.py"))
        
        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply import mappings
                for old_import, new_import in self.import_mappings.items():
                    content = content.replace(old_import, new_import)
                
                # Special case: update model_loader path for pistol.glb
                if "pistol.glb" in content:
                    content = content.replace('"pistol.glb"', '"assets/models/pistol.glb"')
                    content = content.replace("'pistol.glb'", "'assets/models/pistol.glb'")
                
                # Write back if changes were made
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  Updated imports in: {py_file.relative_to(self.target_dir)}")
                    
            except Exception as e:
                print(f"  Error updating {py_file}: {e}")
    
    def create_config_files(self):
        """Create configuration and project files."""
        print("\nCreating configuration files...")
        
        # Create settings.py
        settings_content = '''"""Game configuration constants."""

# Display settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Weapon settings
DEFAULT_AMMO = 7
RELOAD_TIME = 2.0
FIRE_RATE = 0.2  # Minimum time between shots

# Player settings
PLAYER_MAX_HEALTH = 100
PLAYER_RADIUS = 0.5
DAMAGE_PER_HIT = 20
DAMAGE_COOLDOWN = 1.0  # Seconds between damage instances

# Enemy settings
ENEMY_SPEED = 0.02
ENEMY_MIN_HEALTH = 30
ENEMY_MAX_HEALTH = 80

# Asset paths
MODELS_PATH = "assets/models/"
TEXTURES_PATH = "assets/textures/"
SOUNDS_PATH = "assets/sounds/"

# Camera settings
CAMERA_POSITION = (0.0, 2.0, 5.0)
CAMERA_FOV = 60.0
CAMERA_NEAR = 0.1
CAMERA_FAR = 1000.0
'''
        
        with open(self.target_dir / "config/settings.py", 'w', encoding='utf-8') as f:
            f.write(settings_content)
        print("  Created: config/settings.py")
        
        # Create requirements.txt
        requirements_content = '''pygame>=2.1.0
PyOpenGL>=3.1.0
PyOpenGL-accelerate>=3.1.0
numpy>=1.21.0
pygltflib>=1.13.0
'''
        
        with open(self.target_dir / "requirements.txt", 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        print("  Created: requirements.txt")
        
        # Create README.md
        readme_content = '''# 3D Shooting Game

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
'''
        
        with open(self.target_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("  Created: README.md")
        
        # Create .gitignore
        gitignore_content = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Game-specific
*.log
screenshots/
saves/
'''
        
        with open(self.target_dir / ".gitignore", 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("  Created: .gitignore")
    
    def create_documentation(self):
        """Create basic documentation files."""
        print("\nCreating documentation files...")
        
        # Create game design document
        game_design_content = '''# Game Design Document

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
'''
        
        with open(self.target_dir / "docs/game_design.md", 'w', encoding='utf-8') as f:
            f.write(game_design_content)
        print("  Created: docs/game_design.md")
        
        # Create controls documentation
        controls_content = '''# Game Controls

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
'''
        
        with open(self.target_dir / "docs/controls.md", 'w', encoding='utf-8') as f:
            f.write(controls_content)
        print("  Created: docs/controls.md")
    
    def run_migration(self):
        """Run the complete migration process."""
        print("Starting project migration...")
        print(f"Source: {self.source_dir.resolve()}")
        print(f"Target: {self.target_dir.resolve()}")
        print()
        
        try:
            self.create_directory_structure()
            self.move_files()
            self.update_imports()
            self.create_config_files()
            self.create_documentation()
            
            print(f"\n✅ Migration completed successfully!")
            print(f"Your organized project is now in: {self.target_dir.resolve()}")
            print("\nNext steps:")
            print("1. cd shooting_game")
            print("2. pip install -r requirements.txt")
            print("3. python main.py")
            print("\nNote: Original files are preserved in the current directory.")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Run the migration script."""
    print("3D Shooting Game - Project Migration Script")
    print("=" * 50)
    
    migrator = ProjectMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main()