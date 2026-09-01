#!/usr/bin/env python3
"""
Fix script for model loading issues in the 3D shooting game.
This script will diagnose and fix common model loading problems.
"""

import os
import sys
from pathlib import Path

def check_file_existence():
    """Check if the pistol.glb file exists in the correct location."""
    print("=== CHECKING FILE EXISTENCE ===")
    
    # Check current directory structure
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Expected locations
    locations_to_check = [
        "assets/models/pistol.glb",
        "pistol.glb",
        "../pistol.glb"
    ]
    
    found_file = None
    for location in locations_to_check:
        file_path = current_dir / location
        if file_path.exists():
            print(f"✅ Found pistol.glb at: {file_path}")
            print(f"   File size: {file_path.stat().st_size} bytes")
            found_file = file_path
            break
        else:
            print(f"❌ Not found at: {file_path}")
    
    if not found_file:
        print("\n⚠️  PROBLEM: pistol.glb not found in expected locations!")
        print("   Please ensure the file is in assets/models/pistol.glb")
        return None
        
    return found_file

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n=== CHECKING DEPENDENCIES ===")
    
    required_packages = [
        'pygame',
        'PyOpenGL',
        'numpy',
        'pygltflib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  PROBLEM: Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install " + " ".join(missing_packages))
        return False
    
    return True

def test_glb_file(file_path):
    """Test if the GLB file can be loaded."""
    print(f"\n=== TESTING GLB FILE: {file_path} ===")
    
    try:
        # Test basic file reading
        with open(file_path, 'rb') as f:
            header = f.read(12)
            if len(header) < 12:
                print("❌ File is too small to be a valid GLB")
                return False
            
            magic = header[:4]
            if magic != b'glTF':
                print(f"❌ Invalid magic bytes: {magic} (should be b'glTF')")
                return False
            
            version = int.from_bytes(header[4:8], byteorder='little')
            length = int.from_bytes(header[8:12], byteorder='little')
            
            print(f"✅ GLB Header valid:")
            print(f"   Magic: {magic}")
            print(f"   Version: {version}")
            print(f"   Length: {length} bytes")
            print(f"   Actual file size: {file_path.stat().st_size} bytes")
            
            if file_path.stat().st_size != length:
                print("⚠️  File size mismatch - file might be corrupted")
    
    except Exception as e:
        print(f"❌ Error reading GLB file: {e}")
        return False
    
    # Test pygltflib loading
    try:
        from pygltflib import GLTF2
        print("\n📋 Testing pygltflib loading...")
        gltf = GLTF2().load(str(file_path))
        print(f"✅ pygltflib loaded successfully")
        print(f"   Meshes: {len(gltf.meshes) if gltf.meshes else 0}")
        print(f"   Materials: {len(gltf.materials) if gltf.materials else 0}")
        print(f"   Nodes: {len(gltf.nodes) if gltf.nodes else 0}")
        return True
        
    except Exception as e:
        print(f"❌ pygltflib loading failed: {e}")
        return False

def create_fixed_model_loader():
    """Create a fixed version of the model loader."""
    print("\n=== CREATING FIXED MODEL LOADER ===")
    
    fixed_model_loader = '''import struct
import json
import os
from OpenGL.GL import *
import numpy as np
from pathlib import Path

class GLTFLoader:
    """Loads and renders GLTF/GLB 3D models with improved error handling"""
    
    def __init__(self):
        self.models = {}
        
    def load_glb(self, filepath):
        """Load a GLB (binary GLTF) file with better path resolution"""
        print(f"Attempting to load GLB file: {filepath}")
        
        # Try multiple path resolutions
        file_path = Path(filepath)
        if not file_path.exists():
            # Try relative to script location
            script_dir = Path(__file__).parent
            file_path = script_dir / filepath
            
        if not file_path.exists():
            # Try from project root
            file_path = Path.cwd() / filepath
            
        if not file_path.exists():
            print(f"ERROR: File not found: {filepath}")
            print(f"Tried paths:")
            print(f"  - {Path(filepath)}")
            print(f"  - {Path(__file__).parent / filepath}")
            print(f"  - {Path.cwd() / filepath}")
            return None
            
        try:
            from pygltflib import GLTF2
            # Load GLTF using pygltflib
            gltf = GLTF2().load(str(file_path))
            print(f"Successfully loaded GLTF file")
            print(f"GLTF contains:")
            print(f"  - {len(gltf.meshes) if gltf.meshes else 0} meshes")
            print(f"  - {len(gltf.materials) if gltf.materials else 0} materials")
            print(f"  - {len(gltf.nodes) if gltf.nodes else 0} nodes")
            
            return self._process_gltf_pygltflib(gltf)
                
        except ImportError:
            print("ERROR: pygltflib not installed. Run: pip install pygltflib")
            return None
        except Exception as e:
            print(f"ERROR loading GLB file {filepath}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _process_gltf_pygltflib(self, gltf):
        """Process GLTF data loaded with pygltflib"""
        print("Processing GLTF data...")
        
        model_data = {
            'meshes': [],
            'materials': gltf.materials or [],
            'nodes': gltf.nodes or [],
            'scenes': gltf.scenes or []
        }
        
        if not gltf.meshes:
            print("No meshes found in GLTF file")
            return None
            
        # Process each mesh
        for i, mesh in enumerate(gltf.meshes):
            print(f"Processing mesh {i}: {mesh.name if mesh.name else 'unnamed'}")
            mesh_data = self._process_mesh_pygltflib(gltf, mesh, i)
            if mesh_data:
                model_data['meshes'].append(mesh_data)
                print(f"Successfully processed mesh {i}")
            else:
                print(f"Failed to process mesh {i}")
        
        print(f"Final model has {len(model_data['meshes'])} processed meshes")
        return model_data if model_data['meshes'] else None
    
    def _process_mesh_pygltflib(self, gltf, mesh, mesh_index):
        """Process a single mesh using pygltflib"""
        primitives = []
        
        for j, primitive in enumerate(mesh.primitives):
            try:
                print(f"  Processing primitive {j}")
                
                vertices = None
                normals = None
                indices = None
                
                # Get vertex positions
                if hasattr(primitive.attributes, 'POSITION') and primitive.attributes.POSITION is not None:
                    vertices = self._get_accessor_data_pygltflib(gltf, primitive.attributes.POSITION)
                    if vertices:
                        print(f"  Loaded {len(vertices)} vertices")
                
                # Get normals
                if hasattr(primitive.attributes, 'NORMAL') and primitive.attributes.NORMAL is not None:
                    normals = self._get_accessor_data_pygltflib(gltf, primitive.attributes.NORMAL)
                    if normals:
                        print(f"  Loaded {len(normals)} normals")
                
                # Get indices
                if primitive.indices is not None:
                    indices = self._get_accessor_data_pygltflib(gltf, primitive.indices)
                    if indices:
                        print(f"  Loaded {len(indices)} indices")
                        # Convert to flat list if needed
                        if isinstance(indices[0], (list, tuple)):
                            indices = [idx[0] if isinstance(idx, (list, tuple)) else idx for idx in indices]
                
                if vertices is not None:
                    primitives.append({
                        'vertices': vertices,
                        'normals': normals,
                        'indices': indices,
                        'material': primitive.material if primitive.material is not None else 0
                    })
                    print(f"  Successfully created primitive {j}")
                else:
                    print(f"  No vertices found for primitive {j}")
                    
            except Exception as e:
                print(f"  ERROR processing primitive {j}: {e}")
                continue
        
        return {'primitives': primitives} if primitives else None
    
    def _get_accessor_data_pygltflib(self, gltf, accessor_index):
        """Extract data using pygltflib accessor"""
        try:
            if accessor_index >= len(gltf.accessors):
                print(f"    ERROR: Accessor index {accessor_index} out of range")
                return None
            
            accessor = gltf.accessors[accessor_index]
            buffer_view = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[buffer_view.buffer]
            
            # Get buffer data - pygltflib handles the binary data extraction
            if hasattr(buffer, 'data') and buffer.data:
                buffer_data = buffer.data
            elif hasattr(gltf, 'get_data_from_buffer_uri'):
                buffer_data = gltf.get_data_from_buffer_uri(buffer.uri)
            else:
                print("    ERROR: Cannot access buffer data")
                return None
            
            # Calculate offsets
            buffer_offset = buffer_view.byteOffset if buffer_view.byteOffset else 0
            accessor_offset = accessor.byteOffset if accessor.byteOffset else 0
            total_offset = buffer_offset + accessor_offset
            
            # Map component types to struct formats and sizes
            component_types = {
                5120: ('b', 1),  # BYTE
                5121: ('B', 1),  # UNSIGNED_BYTE
                5122: ('h', 2),  # SHORT
                5123: ('H', 2),  # UNSIGNED_SHORT
                5125: ('I', 4),  # UNSIGNED_INT
                5126: ('f', 4),  # FLOAT
            }
            
            # Map accessor types to component counts
            type_components = {
                'SCALAR': 1,
                'VEC2': 2,
                'VEC3': 3,
                'VEC4': 4
            }
            
            if accessor.componentType not in component_types:
                print(f"    ERROR: Unknown component type: {accessor.componentType}")
                return None
                
            if accessor.type not in type_components:
                print(f"    ERROR: Unknown accessor type: {accessor.type}")
                return None
            
            format_char, byte_size = component_types[accessor.componentType]
            components = type_components[accessor.type]
            
            # Extract data
            data = []
            stride = byte_size * components
            total_bytes_needed = accessor.count * stride
            
            if total_offset + total_bytes_needed > len(buffer_data):
                print(f"    ERROR: Not enough buffer data. Need {total_bytes_needed} bytes, have {len(buffer_data) - total_offset}")
                return None
            
            for i in range(accessor.count):
                item_offset = total_offset + i * stride
                if accessor.type == 'SCALAR':
                    value = struct.unpack_from(f'<{format_char}', buffer_data, item_offset)[0]
                    data.append(value)
                else:
                    values = struct.unpack_from(f'<{components}{format_char}', buffer_data, item_offset)
                    data.append(list(values))
            
            return data
            
        except Exception as e:
            print(f"    ERROR extracting accessor data: {e}")
            return None
    
    def render_model(self, model_data, scale=1.0, position=(0, 0, 0), rotation=(0, 0, 0)):
        """Render a loaded 3D model"""
        if not model_data:
            print("No model data to render")
            return
            
        if not model_data['meshes']:
            print("No meshes in model data")
            return
        
        glPushMatrix()
        
        # Apply transformations
        glTranslatef(position[0], position[1], position[2])
        glRotatef(rotation[0], 1, 0, 0)
        glRotatef(rotation[1], 0, 1, 0)
        glRotatef(rotation[2], 0, 0, 1)
        glScalef(scale, scale, scale)
        
        # Set material properties - make it bright and visible
        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.6, 0.4, 1.0])  # Brownish/metallic
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.7, 0.7, 0.7, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 64.0)
        
        # Render each mesh
        for i, mesh in enumerate(model_data['meshes']):
            for j, primitive in enumerate(mesh['primitives']):
                self._render_primitive(primitive, i, j)
        
        glPopMatrix()
    
    def _render_primitive(self, primitive, mesh_idx, prim_idx):
        """Render a single primitive (triangle list)"""
        vertices = primitive.get('vertices')
        normals = primitive.get('normals')
        indices = primitive.get('indices')
        
        if not vertices:
            return
        
        if indices:
            # Render with indices
            glBegin(GL_TRIANGLES)
            for i in range(0, len(indices), 3):
                if i + 2 < len(indices):
                    for j in range(3):
                        idx = indices[i + j]
                        if isinstance(idx, list):
                            idx = idx[0] if idx else 0
                        if idx < len(vertices):
                            if normals and idx < len(normals):
                                normal = normals[idx]
                                if len(normal) >= 3:
                                    glNormal3f(normal[0], normal[1], normal[2])
                            vertex = vertices[idx]
                            if len(vertex) >= 3:
                                glVertex3f(vertex[0], vertex[1], vertex[2])
            glEnd()
        else:
            # Render without indices
            glBegin(GL_TRIANGLES)
            for i in range(0, len(vertices), 3):
                if i + 2 < len(vertices):
                    for j in range(3):
                        if i + j < len(vertices):
                            if normals and i + j < len(normals):
                                normal = normals[i + j]
                                if len(normal) >= 3:
                                    glNormal3f(normal[0], normal[1], normal[2])
                            vertex = vertices[i + j]
                            if len(vertex) >= 3:
                                glVertex3f(vertex[0], vertex[1], vertex[2])
            glEnd()


# Global model loader instance
model_loader = GLTFLoader()

def load_pistol_model():
    """Load the pistol model with improved error handling"""
    print("=== LOADING PISTOL MODEL ===")
    try:
        pistol_model = model_loader.load_glb("assets/models/pistol.glb")
        if pistol_model:
            print("SUCCESS: Pistol model loaded!")
            return pistol_model
        else:
            print("FAILURE: Could not load pistol model")
            return None
    except Exception as e:
        print(f"EXCEPTION loading pistol model: {e}")
        import traceback
        traceback.print_exc()
        return None

def render_pistol(position=(0, 0, 0), rotation=(0, 0, 0), scale=1.0):
    """Render the pistol model at specified position"""
    if hasattr(render_pistol, 'model') and render_pistol.model:
        model_loader.render_model(render_pistol.model, scale, position, rotation)
    else:
        render_fallback_pistol(position, rotation, scale)

def render_fallback_pistol(position=(0, 0, 0), rotation=(0, 0, 0), scale=1.0):
    """Render a simple box as fallback when model loading fails"""
    glPushMatrix()
    
    # Apply transformations
    glTranslatef(position[0], position[1], position[2])
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)
    glScalef(scale, scale, scale)
    
    # Set bright color so it's visible
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.6, 0.3, 0.3, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.9, 0.5, 0.5, 1.0])
    
    # Draw a simple box (pistol shape)
    glBegin(GL_QUADS)
    
    # Front face
    glNormal3f(0, 0, 1)
    glVertex3f(-0.1, -0.05, 0.3)
    glVertex3f(0.1, -0.05, 0.3)
    glVertex3f(0.1, 0.05, 0.3)
    glVertex3f(-0.1, 0.05, 0.3)
    
    # Back face
    glNormal3f(0, 0, -1)
    glVertex3f(-0.1, -0.05, -0.1)
    glVertex3f(-0.1, 0.05, -0.1)
    glVertex3f(0.1, 0.05, -0.1)
    glVertex3f(0.1, -0.05, -0.1)
    
    # Top face
    glNormal3f(0, 1, 0)
    glVertex3f(-0.1, 0.05, -0.1)
    glVertex3f(-0.1, 0.05, 0.3)
    glVertex3f(0.1, 0.05, 0.3)
    glVertex3f(0.1, 0.05, -0.1)
    
    # Bottom face
    glNormal3f(0, -1, 0)
    glVertex3f(-0.1, -0.05, -0.1)
    glVertex3f(0.1, -0.05, -0.1)
    glVertex3f(0.1, -0.05, 0.3)
    glVertex3f(-0.1, -0.05, 0.3)
    
    # Right face
    glNormal3f(1, 0, 0)
    glVertex3f(0.1, -0.05, -0.1)
    glVertex3f(0.1, 0.05, -0.1)
    glVertex3f(0.1, 0.05, 0.3)
    glVertex3f(0.1, -0.05, 0.3)
    
    # Left face
    glNormal3f(-1, 0, 0)
    glVertex3f(-0.1, -0.05, -0.1)
    glVertex3f(-0.1, -0.05, 0.3)
    glVertex3f(-0.1, 0.05, 0.3)
    glVertex3f(-0.1, 0.05, -0.1)
    
    glEnd()
    
    glPopMatrix()

# Load model on import
print("Initializing pistol model...")
render_pistol.model = load_pistol_model()
if render_pistol.model:
    print("Pistol model ready for rendering!")
else:
    print("Pistol model failed to load - will use fallback rendering")
'''
    
    # Write the fixed model loader
    with open("src/rendering/model_loader.py", 'w', encoding='utf-8') as f:
        f.write(fixed_model_loader)
    
    print("✅ Created fixed model_loader.py")

def main():
    """Main diagnostic and fix function."""
    print("🔧 MODEL LOADING DIAGNOSTIC AND FIX TOOL")
    print("=" * 50)
    
    # Step 1: Check if we're in the right directory
    if not Path("src").exists():
        print("❌ ERROR: Not in the shooting_game directory!")
        print("   Please run this script from inside the shooting_game folder")
        return
    
    # Step 2: Check file existence
    pistol_file = check_file_existence()
    if not pistol_file:
        return
    
    # Step 3: Check dependencies
    if not check_dependencies():
        return
    
    # Step 4: Test the GLB file
    if not test_glb_file(pistol_file):
        return
    
    # Step 5: Create fixed model loader
    create_fixed_model_loader()
    
    print("\n✅ DIAGNOSIS AND FIX COMPLETE!")
    print("\nNext steps:")
    print("1. Make sure you have all dependencies: pip install -r requirements.txt")
    print("2. Run the game: python main.py")
    print("3. The pistol model should now load correctly")

if __name__ == "__main__":
    main()