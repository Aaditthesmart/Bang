"""Game configuration constants."""

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
