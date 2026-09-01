from OpenGL.GL import *

class Box:
    def __init__(self, x, y, z, size=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Set material properties for the box
        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.8, 0.4, 0.2, 1.0])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.9, 0.5, 0.3, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.2, 0.2, 0.2, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 20.0)
        
        s = self.size / 2.0
        
        # Draw cube faces
        glBegin(GL_QUADS)
        
        # Front face
        glNormal3f(0, 0, 1)
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)
        
        # Back face
        glNormal3f(0, 0, -1)
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(s, -s, -s)
        
        # Top face
        glNormal3f(0, 1, 0)
        glVertex3f(-s, s, -s)
        glVertex3f(-s, s, s)
        glVertex3f(s, s, s)
        glVertex3f(s, s, -s)
        
        # Bottom face
        glNormal3f(0, -1, 0)
        glVertex3f(-s, -s, -s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, -s, s)
        glVertex3f(-s, -s, s)
        
        # Right face
        glNormal3f(1, 0, 0)
        glVertex3f(s, -s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(s, s, s)
        glVertex3f(s, -s, s)
        
        # Left face
        glNormal3f(-1, 0, 0)
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, -s, s)
        glVertex3f(-s, s, s)
        glVertex3f(-s, s, -s)
        
        glEnd()
        glPopMatrix()
    
    def intersects_ray(self, ray_start, ray_dir, max_distance):
        # Simple AABB ray intersection that returns distance to intersection
        s = self.size / 2.0
        box_min = [self.x - s, self.y - s, self.z - s]
        box_max = [self.x + s, self.y + s, self.z + s]
        
        t_min = 0.0
        t_max = max_distance
        
        for i in range(3):
            if abs(ray_dir[i]) < 0.0001:  # Ray is parallel to slab
                if ray_start[i] < box_min[i] or ray_start[i] > box_max[i]:
                    return None
            else:
                t1 = (box_min[i] - ray_start[i]) / ray_dir[i]
                t2 = (box_max[i] - ray_start[i]) / ray_dir[i]
                
                if t1 > t2:
                    t1, t2 = t2, t1
                
                t_min = max(t_min, t1)
                t_max = min(t_max, t2)
                
                if t_min > t_max:
                    return None
        
        # Return the distance to the intersection point
        return t_min if t_min <= max_distance and t_min >= 0 else None