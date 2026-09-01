import struct
import json
import os
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
            print(f"Current working directory: {os.getcwd()}")
            print(f"Files in directory: {os.listdir('.')}")
            return None
            
        try:
            # Load GLTF using pygltflib
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
                import traceback
                traceback.print_exc()
                continue
        
        return {'primitives': primitives} if primitives else None
    
    def _get_accessor_data_pygltflib(self, gltf, accessor_index):
        """Extract data using pygltflib accessor"""
        try:
            print(f"    Getting accessor data for index {accessor_index}")
            
            if accessor_index >= len(gltf.accessors):
                print(f"    ERROR: Accessor index {accessor_index} out of range")
                return None
            
            accessor = gltf.accessors[accessor_index]
            buffer_view = gltf.bufferViews[accessor.bufferView]
            buffer = gltf.buffers[buffer_view.buffer]
            
            print(f"    Accessor: count={accessor.count}, componentType={accessor.componentType}, type={accessor.type}")
            
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
    
    def render_model(self, model_data, scale=1.0, position=(0, 0, 0), rotation=(0, 0, 0)):
        """Render a loaded 3D model"""
        if not model_data:
            print("No model data to render")
            return
            
        if not model_data['meshes']:
            print("No meshes in model data")
            return
        
        print(f"Rendering model with {len(model_data['meshes'])} meshes at position {position}")
        
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
            print(f"Rendering mesh {i} with {len(mesh['primitives'])} primitives")
            for j, primitive in enumerate(mesh['primitives']):
                self._render_primitive(primitive, i, j)
        
        glPopMatrix()
    
    def _render_primitive(self, primitive, mesh_idx, prim_idx):
        """Render a single primitive (triangle list)"""
        vertices = primitive.get('vertices')
        normals = primitive.get('normals')
        indices = primitive.get('indices')
        
        if not vertices:
            print(f"  No vertices in primitive {mesh_idx}-{prim_idx}")
            return
        
        triangle_count = 0
        
        if indices:
            print(f"  Rendering primitive {mesh_idx}-{prim_idx} with indices: {len(indices)} indices, {len(vertices)} vertices")
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
                    triangle_count += 1
            glEnd()
        else:
            print(f"  Rendering primitive {mesh_idx}-{prim_idx} without indices: {len(vertices)} vertices")
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
                    triangle_count += 1
            glEnd()
        
        print(f"  Rendered {triangle_count} triangles for primitive {mesh_idx}-{prim_idx}")


# Global model loader instance
model_loader = GLTFLoader()

def load_pistol_model():
    """Load the pistol model with debugging using pygltflib"""
    print("=== LOADING PISTOL MODEL WITH PYGLTFLIB ===")
    try:
        pistol_model = model_loader.load_glb("pistol.glb")
        if pistol_model:
            print("SUCCESS: Pistol model loaded with pygltflib!")
            print(f"Model contains {len(pistol_model.get('meshes', []))} meshes")
            return pistol_model
        else:
            print("FAILURE: Could not load pistol model with pygltflib")
            return None
    except Exception as e:
        print(f"EXCEPTION loading pistol model with pygltflib: {e}")
        import traceback
        traceback.print_exc()
        return None

def render_pistol(position=(0, 0, 0), rotation=(0, 0, 0), scale=1.0):
    """Render the pistol model at specified position"""
    if hasattr(render_pistol, 'model') and render_pistol.model:
        model_loader.render_model(render_pistol.model, scale, position, rotation)
    else:
        print("No pistol model loaded - rendering fallback")
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
print("Initializing pistol model with pygltflib...")
render_pistol.model = load_pistol_model()
if render_pistol.model:
    print("Pistol model ready for rendering with pygltflib!")
else:
    print("Pistol model failed to load with pygltflib - will use fallback rendering")