import pygame
import os
import sys
from pathlib import Path

class SoundSystem:
    """Handles all game audio including sound effects and music"""
    
    def __init__(self):
        self.sounds = {}
        self.sound_enabled = True
        self.volume = 0.7  # Default volume (0.0 to 1.0)
        
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                print("Sound system initialized successfully")
            except pygame.error as e:
                print(f"Warning: Could not initialize sound system: {e}")
                self.sound_enabled = False
                return
        
        # Load sound files
        self.load_sounds()
    
    def load_sounds(self):
        """Load all sound files from the assets/sounds directory"""
        if not self.sound_enabled:
            return
            
        # Get the directory where this script would be located (src/audio/)
        script_dir = Path(__file__).parent if hasattr(Path(__file__), 'parent') else Path.cwd()
        
        # Try different possible paths for the sounds directory
        possible_sound_dirs = [
            script_dir.parent.parent / "assets" / "sfx",  # fps_game/assets/sounds/
            script_dir.parent / "assets" / "sfx",         # from src/
            Path.cwd() / "assets" / "sfx",                # from project root
            Path.cwd() / "sfx",                           # sounds/ in current directory
            Path.cwd(),                                      # current directory
        ]
        
        sounds_to_load = {
            'gun': 'gun.mp3',
            'reload': 'reload.mp3'
        }
        
        sounds_dir = None
        
        # Find the sounds directory
        for sound_dir in possible_sound_dirs:
            if sound_dir.exists():
                # Check if at least one of our required sound files exists
                if any((sound_dir / filename).exists() for filename in sounds_to_load.values()):
                    sounds_dir = sound_dir
                    print(f"Found sounds directory: {sounds_dir}")
                    break
        
        if not sounds_dir:
            print("Warning: Could not find sounds directory with gun.mp3 and reload.mp3")
            print("Expected directory structure:")
            for dir_path in possible_sound_dirs[:3]:
                print(f"  {dir_path}")
            print("Please ensure your sound files are in one of these locations")
            return
        
        # Load each sound file
        for sound_name, filename in sounds_to_load.items():
            filepath = sounds_dir / filename
            
            if filepath.exists():
                try:
                    sound = pygame.mixer.Sound(str(filepath))
                    sound.set_volume(self.volume)
                    self.sounds[sound_name] = sound
                    print(f"Loaded sound: {sound_name} from {filepath}")
                except pygame.error as e:
                    print(f"Error loading sound {filepath}: {e}")
            else:
                print(f"Warning: Sound file not found: {filepath}")
                
        print(f"Sound system loaded {len(self.sounds)} sounds successfully")
    
    def play_sound(self, sound_name, volume_override=None):
        """Play a sound effect by name"""
        if not self.sound_enabled or sound_name not in self.sounds:
            if sound_name not in self.sounds and self.sound_enabled:
                print(f"Warning: Sound '{sound_name}' not found")
            return
            
        try:
            sound = self.sounds[sound_name]
            
            # Set volume if override provided
            if volume_override is not None:
                original_volume = sound.get_volume()
                sound.set_volume(volume_override)
                sound.play()
                # Restore original volume after a short delay (non-blocking)
                pygame.time.set_timer(pygame.USEREVENT + 1, 100)  # Reset volume after 100ms
            else:
                sound.play()
                
        except pygame.error as e:
            print(f"Error playing sound '{sound_name}': {e}")
    
    def play_gun_sound(self):
        """Play the gun shooting sound"""
        self.play_sound('gun', volume_override=0.8)  # Slightly louder for gun
    
    def play_reload_sound(self):
        """Play the reload sound"""
        self.play_sound('reload', volume_override=0.6)  # Slightly quieter for reload
    
    def set_volume(self, volume):
        """Set the master volume for all sounds (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.sound_enabled = not self.sound_enabled
        print(f"Sound {'enabled' if self.sound_enabled else 'disabled'}")
        return self.sound_enabled
    
    def stop_all_sounds(self):
        """Stop all currently playing sounds"""
        if self.sound_enabled:
            pygame.mixer.stop()
    
    def is_sound_available(self, sound_name):
        """Check if a specific sound is loaded and available"""
        return self.sound_enabled and sound_name in self.sounds


# Global sound system instance
sound_system = None

def initialize_sound_system():
    """Initialize the global sound system"""
    global sound_system
    if sound_system is None:
        sound_system = SoundSystem()
    return sound_system

def get_sound_system():
    """Get the global sound system instance"""
    global sound_system
    if sound_system is None:
        sound_system = initialize_sound_system()
    return sound_system

def play_gun_sound():
    """Convenience function to play gun sound"""
    get_sound_system().play_gun_sound()

def play_reload_sound():
    """Convenience function to play reload sound"""
    get_sound_system().play_reload_sound()

def cleanup_sound_system():
    """Clean up the sound system"""
    global sound_system
    if sound_system:
        sound_system.stop_all_sounds()
        pygame.mixer.quit()
        sound_system = None