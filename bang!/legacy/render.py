from OpenGL.GL import *
from OpenGL.GLU import *

class Render:
    @staticmethod
    def init_opengl():
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)  # Black clear color
        
        # Set up perspective projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, 800.0/600.0, 0.1, 1000.0)
        
        glMatrixMode(GL_MODELVIEW)
        
        # Enable lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Set up a bright point light source
        light_position = [0.0, 20.0, 0.0, 1.0]  # Point light at (0, 20, 0)
        light_ambient = [0.4, 0.4, 0.5, 1.0]    # Soft blue ambient light
        light_diffuse = [1.0, 1.0, 0.9, 1.0]    # Bright white diffuse light
        light_specular = [1.0, 1.0, 1.0, 1.0]   # White specular highlights
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
        
        # Set light attenuation for point light
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.01)
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.001)