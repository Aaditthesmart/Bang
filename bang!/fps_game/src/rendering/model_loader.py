import struct
import json
import os
import sys
from OpenGL.GL import *
import numpy as np
from pygltflib import GLTF2

class GLTFLoader:
    """Loads and renders GLTF/GLB 3D models using pygltflib"""
    
    def __init__(self):
        self.models = {}
        
    def load_glb(self, filepath):
        """Load a GLB (binary GLTF) file using pygltflib"""
        print(f"Attempting to load GLB file with pygltflib: {filepath}")
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {filepath}")
            try:
                # Safely print current directory, handling Unicode issues
                current_dir = os.getcwd()
                print(f"Current working directory: {current_dir}")
            except UnicodeEncodeError:
                print("Current working directory contains Unicode characters that cannot be displayed")
                print("Consider moving the project to a path with only ASCII characters")
            
            try:
                files = os.listdir('.')
                print(f"Files in current directory: {files}")
            except Exception as e:
                print(f"Could not list directory contents: {e}")
            return None
            
        try:
            # Load GLTF using pygltflib - simple approach like working version
            gltf = GLTF2().load(filepath)
            print(f"Successfully loaded GLTF file with pygltflib")
            print(f"GLTF contains:")
            print(f"  - {len(gltf.meshes) if gltf.meshes else 0} meshes")
            print(f"  - {len(gltf.materials) if gltf.materials else 0} materials")
            print(f"  - {len(gltf.nodes) if gltf.nodes else 0} nodes")
            print(f"  - {len(gltf.buffers) if gltf.buffers else 0} buffers")
            print(f"  - {len(gltf.bufferViews) if gltf.bufferViews else 0} buffer views")
            print(f"  - {len(gltf.accessors) if gltf.accessors else 0} accessors")
            
            return self._process_gltf_pygltflib(gltf)
                
        except Exception as e:
            print(f"ERROR loading GLB file {filepath} with pygltflib: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _process_gltf_pygltflib(self, gltf):
        """Process GLTF data loaded with pygltflib"""
        print("Processing GLTF data with pygltflib...")
        
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
            mesh_name = mesh.name if mesh.name else f'mesh_{i}'
            print(f"Processing mesh {i}: {mesh_name}")
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
                        # Print first few vertices for debugging
                        for k in range(min(3, len(vertices))):
                            print(f"    Vertex {k}: {vertices[k]}")
                
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
                        if indices and isinstance(indices[0], (list, tuple)):
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
                import traceback
                traceback.print_exc()
                continue
        
        return {'primitives': primitives} if primitives else None
    
    def _get_accessor_data_pygltflib(self, gltf, accessor_index):
        """Extract data using pygltflib accessor - comprehensive approach"""
        try:
            print(f"    Getting accessor data for index {accessor_index}")
            
            if accessor_index >= len(gltf.accessors):
                print(f"    ERROR: Accessor index {accessor_index} out of range")
                return None
            
            accessor = gltf.accessors[accessor_index]
            
            if accessor.bufferView is None:
                print(f"    ERROR: Accessor {accessor_index} has no bufferView")
                return None
                
            buffer_view = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[buffer_view.buffer]
            
            print(f"    Accessor: count={accessor.count}, componentType={accessor.componentType}, type={accessor.type}")
            
            # Try multiple ways to get buffer data
            buffer_data = None
            
            # Method 1: Direct buffer.data access
            if hasattr(buffer, 'data') and buffer.data:
                buffer_data = buffer.data
                print(f"    Got buffer data from buffer.data ({len(buffer_data)} bytes)")
            
            # Method 2: Try to get from GLTF binary blob
            elif hasattr(gltf, 'binary_blob') and gltf.binary_blob:
                # Check if it's callable (method) or data
                if callable(gltf.binary_blob):
                    try:
                        buffer_data = gltf.binary_blob()
                        print(f"    Got buffer data from gltf.binary_blob() method ({len(buffer_data)} bytes)")
                    except:
                        print("    binary_blob method failed")
                else:
                    buffer_data = gltf.binary_blob
                    print(f"    Got buffer data from gltf.binary_blob attribute ({len(buffer_data)} bytes)")
            
            # Method 3: Try buffer.uri handling
            elif buffer.uri:
                if buffer.uri.startswith('data:'):
                    # Data URI
                    import base64
                    header, data = buffer.uri.split(',', 1)
                    buffer_data = base64.b64decode(data)
                    print(f"    Got buffer data from data URI ({len(buffer_data)} bytes)")
                else:
                    # External file
                    buffer_path = os.path.join(os.path.dirname(gltf.filename), buffer.uri)
                    with open(buffer_path, 'rb') as f:
                        buffer_data = f.read()
                    print(f"    Got buffer data from external file ({len(buffer_data)} bytes)")
            
            # Method 4: Try accessing GLB file directly
            elif hasattr(gltf, 'filename') and gltf.filename:
                buffer_data = self._extract_glb_binary_data(gltf.filename)
                if buffer_data:
                    print(f"    Got buffer data by parsing GLB directly ({len(buffer_data)} bytes)")
            
            if buffer_data is None:
                print("    ERROR: Could not access buffer data through any method")
                print(f"    Buffer attributes: {[attr for attr in dir(buffer) if not attr.startswith('_')]}")
                print(f"    GLTF attributes: {[attr for attr in dir(gltf) if not attr.startswith('_')]}")
                return None
            
            # Calculate offsets
            buffer_offset = buffer_view.byteOffset if buffer_view.byteOffset else 0
            accessor_offset = accessor.byteOffset if accessor.byteOffset else 0
            total_offset = buffer_offset + accessor_offset
            
            print(f"    Buffer offset: {buffer_offset}, Accessor offset: {accessor_offset}")
            print(f"    Total offset: {total_offset}, Buffer size: {len(buffer_data)}")
            
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
            
            print(f"    Format: {format_char}, components: {components}, byte_size: {byte_size}")
            
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
            
            print(f"    Successfully extracted {len(data)} items")
            return data
            
        except Exception as e:
            print(f"    ERROR extracting accessor data with pygltflib: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_glb_binary_data(self, filepath):
        """Manually extract binary data from GLB file as fallback"""
        try:
            with open(filepath, 'rb') as f:
                # Read GLB header
                magic = f.read(4)
                if magic != b'glTF':
                    return None
                
                version = struct.unpack('<I', f.read(4))[0]
                length = struct.unpack('<I', f.read(4))[0]
                
                # Read JSON chunk header
                json_chunk_length = struct.unpack('<I', f.read(4))[0]
                json_chunk_type = f.read(4)
                
                # Skip JSON data
                f.seek(json_chunk_length, 1)
                
                # Check if there's a binary chunk
                if f.tell() < length:
                    # Read binary chunk header
                    bin_chunk_length = struct.unpack('<I', f.read(4))[0]
                    bin_chunk_type = f.read(4)
                    
                    if bin_chunk_type == b'BIN\x00':
                        # Read binary data
                        binary_data = f.read(bin_chunk_length)
                        return binary_data
                
                return None
        except Exception as e:
            print(f"    Error reading GLB binary data manually: {e}")
            return None
    
    def render_model(self, model_data, scale=1.0, position=(0, 0, 0), rotation=(0, 0, 0)):
        """Render a loaded 3D model"""
        if not model_data:
            return
            
        if not model_data['meshes']:
            return
        
        glPushMatrix()
        
        # Apply transformations
        glTranslatef(position[0], position[1], position[2])
        glRotatef(rotation[0], 1, 0, 0)
        glRotatef(rotation[1], 0, 1, 0)
        glRotatef(rotation[2], 0, 0, 1)
        glScalef(scale, scale, scale)
        
        # Ensure we're using material properties, not color
        glDisable(GL_COLOR_MATERIAL)
        
        # Set dark/black material properties for the gun
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])      # Very dark ambient
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.2, 0.2, 0.2, 1.0])      # Dark gray/black
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])     # Subtle specular
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)                      # Medium shininess
        
        # Render each mesh
        for i, mesh in enumerate(model_data['meshes']):
            for j, primitive in enumerate(mesh['primitives']):
                self._render_primitive(primitive, i, j)
        
        # Re-enable color material for other objects
        glEnable(GL_COLOR_MATERIAL)
        
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
    """Load the pistol model with debugging using pygltflib"""
    print("=== LOADING PISTOL MODEL WITH PYGLTFLIB ===")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up to the fps_game root directory (up 2 levels from src/rendering/)
    fps_game_root = os.path.dirname(os.path.dirname(script_dir))
    
    try:
        print(f"Script directory: {script_dir}")
        print(f"FPS game root: {fps_game_root}")
    except UnicodeEncodeError:
        print("Script directory contains Unicode characters - path resolution may work anyway")
    
    # Try different possible paths for the pistol model, relative to fps_game root
    possible_paths = [
        os.path.join(fps_game_root, "assets", "models", "pistol.glb"),  # Correct path
        os.path.join(fps_game_root, "pistol.glb"),  # Root level
        "assets/models/pistol.glb",  # Relative to current working directory
        "pistol.glb",  # Current working directory
        "models/pistol.glb",
        "assets/pistol.glb"
    ]
    
    for filepath in possible_paths:
        try:
            print(f"Trying path: {filepath}")
        except UnicodeEncodeError:
            print("Trying a path with Unicode characters...")
            
        if os.path.exists(filepath):
            try:
                print(f"Found model at: {filepath}")
            except UnicodeEncodeError:
                print("Found model at path with Unicode characters")
                
            try:
                pistol_model = model_loader.load_glb(filepath)
                if pistol_model:
                    print("SUCCESS: Pistol model loaded with pygltflib!")
                    print(f"Model contains {len(pistol_model.get('meshes', []))} meshes")
                    return pistol_model
                else:
                    print("FAILURE: Could not process pistol model with pygltflib")
            except Exception as e:
                print(f"EXCEPTION loading pistol model: {e}")
                import traceback
                traceback.print_exc()
        else:
            try:
                print(f"File not found: {filepath}")
            except UnicodeEncodeError:
                print("File not found at path with Unicode characters")
    
    print("FAILURE: Could not find pistol model in any expected location")
    print("Please ensure pistol.glb is in the assets/models/ folder")
    return None

def render_pistol(position=(0, 0, 0), rotation=(0, 0, 0), scale=1.0):
    """Render the pistol model at specified position"""
    if hasattr(render_pistol, 'model') and render_pistol.model:
        model_loader.render_model(render_pistol.model, scale, position, rotation)
    else:
        # Only print this occasionally to avoid spam
        if not hasattr(render_pistol, 'fallback_message_count'):
            render_pistol.fallback_message_count = 0
        
        render_pistol.fallback_message_count += 1
        if render_pistol.fallback_message_count % 60 == 1:  # Print every 60 frames (1 second at 60 FPS)
            print("No pistol model loaded - using fallback rendering")
        
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
    
    # Ensure we're using material properties, not color
    glDisable(GL_COLOR_MATERIAL)
    
    # Set black/dark gray material properties
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])      # Very dark ambient
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.2, 0.2, 0.2, 1.0])      # Dark gray
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])     # Subtle specular
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)                      # Medium shininess
    
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
    
    # Re-enable color material for other objects
    glEnable(GL_COLOR_MATERIAL)
    
    glPopMatrix()

# Load model on import
print("Initializing pistol model with pygltflib...")
render_pistol.model = load_pistol_model()
if render_pistol.model:
    print("Pistol model ready for rendering with pygltflib!")
else:
    print("Pistol model failed to load with pygltflib - will use fallback rendering")