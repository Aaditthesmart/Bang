<div align="center">

# 💥 Bang!

### A Real-World Controlled 3D FPS — Aim with a physical ArUco marker, shoot with a recoil flick, reload with your fist.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![OpenGL](https://img.shields.io/badge/OpenGL-3.1%2B-red?style=for-the-badge&logo=opengl&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-orange?style=for-the-badge&logo=google&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.1%2B-yellow?style=for-the-badge)

</div>

---

## 🎮 What is Bang!?

**Bang!** is a real-time 3D first-person shooter where you don't use a mouse or keyboard to aim — **you use a physical ArUco marker held in front of your webcam**. The game tracks the marker's position, distance, and in-plane rotation to control your weapon in full 3D space. Shoot by flicking the marker upward (a recoil motion), and reload by making a fist with your left hand.

Built as a computer-vision-first game for live demos and expos, Bang! fuses OpenCV pose estimation, MediaPipe hand tracking, quaternion-based weapon mathematics, and real-time 3D rendering into a single cohesive experience.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎯 **ArUco Aiming** | Move a printed marker in front of your webcam — the gun follows in real time |
| 🔫 **Recoil-Gesture Shooting** | A quick upward flick of the marker triggers a shot |
| ✊ **Fist-Gesture Reloading** | Show a closed left fist above the marker to reload |
| 👻 **Ghost Enemies** | 4 constantly-respawning ghost enemies with sinusoidal floating & lateral movement AI |
| 🔢 **Quaternion Weapon Math** | Weapon orientation computed via quaternion multiplication (yaw × roll) |
| 💨 **Particle FX** | Muzzle flash, smoke puffs, and screen-shake on fire |
| 🔊 **Spatial Audio** | Gunshot and reload sound effects via pygame mixer |
| ♾️ **Endless Survival** | Enemies respawn immediately on death — survive as long as possible |
| 🧵 **Threaded Vision** | ArUco detection runs in a dedicated daemon thread — zero UI blocking |
| 🛠️ **Runtime Calibration** | Barrel tip, position sensitivity, roll sensitivity adjustable via hotkeys at runtime |

---

## 🗂️ Project Structure

```
Bang!-main/
│
├── 📄 calibrate.py              # Camera calibration utility (generates calib.json)
├── 📄 estimate.py               # Standalone ArUco pose estimator
├── 📄 monitors.py               # Visualizer helper (degree/position overlay)
├── 📄 aruco.py                  # Print-ready ArUco marker generator
├── 🖼️  aruco_4x4_50_id0.png     # Pre-generated ID-0 marker (print and use!)
├── 📄 calib.json                # Camera intrinsic calibration data (fx, fy, cx, cy)
│
└── bang!/
    ├── legacy/                  # Original monolithic scripts (pre-refactor)
    │
    └── fps_game/                # ✅ Main game package
        ├── 🚀 main.py           # Entry point — Game class & main loop
        ├── 📋 requirements.txt
        ├── 📄 README.md
        │
        ├── assets/
        │   ├── models/          # GLB/OBJ 3D models (ghost, zombie, pistol)
        │   └── sfx/             # Audio files (gun.mp3, reload.mp3)
        │
        ├── config/
        │   └── settings.py      # Global game constants
        │
        └── src/
            ├── core/
            │   ├── camera.py    # Fixed-position camera & OpenGL projection
            │   └── render.py    # OpenGL init (depth test, lighting, perspective)
            │
            ├── vision/
            │   ├── estimate.py  # 🔑 ArUco detection + fist & recoil gesture recognition
            │   └── monitors.py  # Angle/position live visualizer
            │
            ├── weapons/
            │   ├── cursor_weapon.py   # 🔑 QuaternionWeapon — full ArUco→3D transform
            │   ├── weapon.py          # shoot() — raycasting hit detection
            │   └── weapon_system.py   # Ammo, reload timer, fire-rate logic
            │
            ├── entities/
            │   ├── enemy/
            │   │   ├── enemy.py         # Enemy aggregate (AI + physics + rendering)
            │   │   ├── enemy_ai.py      # Lateral movement + sinusoidal float AI
            │   │   ├── enemy_physics.py # Knockback and velocity integration
            │   │   └── enemy_rendering.py # OpenGL cylinder draw calls
            │   └── player/
            │       └── health.py        # HP, damage, death state
            │
            ├── rendering/
            │   ├── environment.py  # Skybox, ground plane, weapon model draw
            │   └── ui.py           # HUD — health bar, ammo, score, title, banner
            │
            ├── systems/
            │   ├── collision.py    # Sphere-cylinder intersection tests
            │   └── particles.py    # Muzzle flash, smoke FX, screen shake
            │
            └── audio/
                └── sound_system.py # pygame.mixer wrapper (init, play, volume, toggle)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py  (Game)                      │
│                                                             │
│   ┌──────────────┐          ┌──────────────────────────┐    │
│   │  Main Thread │          │   ArUco Daemon Thread    │    │
│   │  60 FPS loop │◄────────►│  cap.read() → estimate   │    │
│   │              │  Lock    │  → aruco_data dict        │    │
│   └──────┬───────┘          └──────────────────────────┘    │
│          │                                                   │
│   ┌──────▼──────────────────────────────────────────┐       │
│   │              update()                           │       │
│   │                                                 │       │
│   │  QuaternionWeapon ◄── aruco_data                │       │
│   │       │  yaw × roll quaternion                  │       │
│   │       │  barrel tip → firing direction           │       │
│   │       ▼                                         │       │
│   │  shoot() ──► raycasting ──► Enemy.take_damage() │       │
│   │                                                 │       │
│   │  EnemyAI.update_movement() (per enemy)          │       │
│   │  CollisionSystem.check_multiple_collisions()    │       │
│   │  HealthSystem.take_damage()                     │       │
│   └──────┬──────────────────────────────────────────┘       │
│          │                                                   │
│   ┌──────▼──────────────────────────────────────────┐       │
│   │              render()                           │       │
│   │  draw_skybox → draw_ground → draw_weapon        │       │
│   │  ShootingEffects → enemies.draw() → HUD         │       │
│   └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: Real World → In-Game Action

```
Physical Marker
      │
      ▼
cv2.VideoCapture  →  ArucoDetector.detectMarkers()
      │
      ├─ solvePnP()  ──►  tvec / rvec
      │       │
      │       ├── get_distance()         →  d_to_cam  (forward/back)
      │       ├── get_degree_in_game()   →  d (horiz offset), alpha (yaw)
      │       └── get_inplane_angle()    →  angle (roll)
      │
      ├─ is_shooting()   (deque of last 5 y-coords, up-then-down pattern)
      └─ detect_left_fist()  (MediaPipe 21-landmark curl + compactness check)
            │
            ▼
     aruco_data dict  ──(Lock)──►  QuaternionWeapon.update_full_aruco_data()
                                         │
                              yaw_quaternion × roll_quaternion
                                         │
                              glTranslatef + glMultMatrixf  →  rendered gun
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core application |
| **3D Rendering** | PyOpenGL 3.1 + Pygame | OpenGL context, draw calls, windowing |
| **Computer Vision** | OpenCV 4.x (`cv2.aruco`) | ArUco marker detection, `solvePnP` pose estimation |
| **Hand Tracking** | MediaPipe Hands | 21-landmark fist gesture detection for reload |
| **Math** | NumPy + `math` | Quaternion multiplication, rotation matrices, vector ops |
| **3D Models** | pygltflib | Loading `.glb` assets (pistol, ghost, zombie) |
| **Audio** | pygame.mixer | Gunshot / reload SFX with volume control |
| **Concurrency** | `threading.Thread` (daemon) | ArUco vision loop decoupled from render loop |
| **Calibration** | JSON (`calib.json`) | Pinhole camera intrinsics (fx, fy, cx, cy) |

---

## 🎯 Gesture & Control Reference

### Physical Controls (Camera + Marker)

| Gesture | Action |
|---|---|
| Move marker **left / right** | Aim weapon horizontally |
| Move marker **closer / further** | Weapon moves forward / backward in scene |
| **Rotate** marker in-plane | Weapon rolls (tilts) on its axis |
| **Flick marker up, then down** | 🔫 **SHOOT** |
| Make a **fist** with LEFT hand above marker | 🔄 **RELOAD** |

### Keyboard Controls (Backup / Calibration)

| Key | Action |
|---|---|
| `Left Click` | Manual shoot |
| `R` | Manual reload |
| `S` | Toggle sound on/off |
| `-` / `+` | Decrease / Increase volume |
| `1` / `2` | Barrel tip Z offset (−/+) |
| `3` / `4` | Barrel tip Y offset (+/−) |
| `5` / `6` | Barrel tip X offset (+/−) |
| `7` / `8` | Position sensitivity (−/+) |
| `ESC` | Quit |

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10+**
- A webcam
- A printed (or screen-displayed) **4×4 ArUco marker ID 0** — see `aruco_4x4_50_id0.png`

### 1. Clone the Repository

```bash
git clone https://github.com/Aaditthesmart/Bang.git
cd Bang
```

### 2. Install Dependencies

```bash
pip install pygame PyOpenGL PyOpenGL-accelerate numpy pygltflib opencv-contrib-python mediapipe
```

> **Note:** `opencv-contrib-python` is required for the `cv2.aruco` module. Do **not** install plain `opencv-python` alongside it.

### 3. Calibrate Your Camera (Recommended)

For best tracking accuracy, calibrate your webcam using a checkerboard pattern:

```bash
python calibrate.py
```

This writes `calib.json` with your camera's intrinsic parameters. If you skip this step, a default matrix for 1280×720 is used automatically.

### 4. Run the Game

```bash
cd bang!/fps_game
python main.py
```

---

## 🔬 How the Vision Pipeline Works

### ArUco Pose Estimation

Each frame, `cv2.ArucoDetector.detectMarkers()` finds the 4×4 ID-0 marker. The four corner coordinates are passed to `cv2.solvePnP()` with the known real-world marker size (3 cm) to solve for the 6-DoF pose:

- **tvec** → translation of the marker center relative to the camera
- **rvec** → Rodrigues rotation vector

From these, three quantities drive the weapon:

```
d         = horizontal position offset  →  weapon left/right in scene
alpha     = yaw angle (radians)         →  weapon aims left/right
angle     = get_inplane_angle(rvec)     →  weapon roll (Z-axis rotation)
d_to_cam  = pinhole model Z distance    →  weapon forward/back in scene
```

### Shoot Detection

The last 5 marker center Y-coordinates are stored in a `deque`. A shot fires when the sequence contains:
- An **upward step** (Y decreases) ≥ 3px
- Followed by a **downward step** (Y increases) ≥ 3px
- With an overall amplitude ≥ 6px
- And minimal horizontal drift (< 35px X spread)

A 5-frame cooldown prevents double-fires.

### Reload Detection (MediaPipe Fist)

MediaPipe Hands produces 21 3D landmarks per hand. For the **left hand**, the system computes:

1. **Curl ratio** per finger: `fingertip-to-palm / PIP-to-palm`. If < 1.3 → finger is curled.
2. **Compactness**: average distance between adjacent fingertips < 0.08 normalized units → fist is tight.
3. **Position check**: hand average Y-coordinate is **above** the ArUco marker center.

All three conditions together → reload triggered, with a 30-frame cooldown.

### Quaternion Weapon Math

The weapon orientation is represented as two quaternions composed together:

```
q_yaw  = quaternion rotating around Y-axis by α (horizontal aim angle)
q_roll = quaternion rotating around Z-axis by β (in-plane marker angle)
q_total = q_yaw ⊗ q_roll   (Hamilton product)
```

`q_total` is converted to a 4×4 column-major matrix and passed to `glMultMatrixf()` for rendering. Raycasting for hit detection uses the **barrel tip position** + **firing direction** derived from the same quaternion.

---

## 👾 Enemy AI

Ghost enemies exhibit three simultaneous behaviors:

1. **Lateral patrol**: Each ghost bounces left/right within ±12 units, switching direction on boundary contact.
2. **Sinusoidal float**: Y-position oscillates using `A·sin(t·f + φ)` where `φ` is unique per ghost (derived from spawn position) to prevent synchronized bobbing.
3. **Ghost sway**: A slow secondary sine on X and Z axes produces a subtle, eerie drift.

Enemies have variable HP and size (randomized at spawn) and respawn instantly after death to maintain endless gameplay.

---

## 📁 Calibration Files

| File | Description |
|---|---|
| `calib.json` | Camera intrinsics: `fx`, `fy`, `cx`, `cy` (generated by `calibrate.py`) |
| `aruco_4x4_50_id0.png` | Pre-generated 4×4_50 ArUco marker, ID 0. Print at ~5×5 cm. |

### calib.json format
```json
{
  "fx": 800.0,
  "fy": 800.0,
  "cx": 640.0,
  "cy": 360.0
}
```

---

## 🧩 Module Reference

| Module | Class / Function | Role |
|---|---|---|
| `vision/estimate.py` | `Estimate` | Full ArUco pipeline: detection, pose, gestures |
| `weapons/cursor_weapon.py` | `QuaternionWeapon` | ArUco data → quaternion → GL transform |
| `weapons/weapon.py` | `shoot()` | Raycast from barrel tip, enemy hit check |
| `weapons/weapon_system.py` | `WeaponSystem` | Ammo counter, reload timer, fire rate |
| `entities/enemy/enemy_ai.py` | `EnemyAI` | Lateral + float + sway movement |
| `entities/enemy/enemy_rendering.py` | — | OpenGL cylinder primitive draw |
| `systems/collision.py` | `CollisionSystem` | Sphere ↔ cylinder collision |
| `systems/particles.py` | `ShootingEffects` | Muzzle flash, smoke, screen shake |
| `rendering/ui.py` | — | HUD rendering (health, ammo, score) |
| `audio/sound_system.py` | — | pygame.mixer SFX management |
| `core/camera.py` | `Camera` | Fixed-position, applies `gluLookAt` |
| `core/render.py` | `Render` | OpenGL state init (depth, blend, fog) |

---

## 🤝 Contributing

Pull requests are welcome. Please open an issue first to discuss major changes.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push and open a PR

---

## 📜 License

This project is open source. See [LICENSE](LICENSE) for details.

---

<div align="center">
Made with ❤️ and a lot of ArUco markers
</div>
