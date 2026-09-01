#!/usr/bin/env python3

import os
import struct

def test_pistol_file():
    """Simple test to verify the pistol.glb file can be read"""
    
    print("=== PISTOL MODEL FILE TEST ===")
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    
    # Check if pistol.glb exists
    if not os.path.exists('pistol.glb'):
        print("ERROR: pistol.glb not found!")
        print("Make sure the pistol.glb file is in the same directory as your Python scripts.")
        return False
    
    # Check file size
    file_size = os.path.getsize('pistol.glb')
    print(f"pistol.glb found! Size: {file_size} bytes")
    
    # Try to read the header
    try:
        with open('pistol.glb', 'rb') as f:
            magic = f.read(4)
            print(f"Magic bytes: {magic}")
            
            if magic != b'glTF':
                print("ERROR: Not a valid GLB file!")
                return False
            
            version = struct.unpack('<I', f.read(4))[0]
            length = struct.unpack('<I', f.read(4))[0]
            print(f"GLB version: {version}")
            print(f"Total length: {length}")
            
            if file_size != length:
                print(f"WARNING: File size ({file_size}) doesn't match header length ({length})")
            
            print("SUCCESS: pistol.glb appears to be a valid GLB file!")
            return True
            
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return False

if __name__ == "__main__":
    test_pistol_file()