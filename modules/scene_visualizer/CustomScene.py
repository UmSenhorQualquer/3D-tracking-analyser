from py3DEngine.scenes.GLScene import GLScene
import math, cv2, numpy as np
try:
	from OpenGL.GL import *
	from OpenGL.GLUT import *
	from OpenGL.GLU import *
except:
	print 'No OpenGL libs'


class CustomScene(GLScene):
	def __init__(self):
		super(CustomScene,self).__init__()
		self.points = []
		self.colors = []
		self._center = 0,0,0



	def DrawGLScene(self):
		glTranslatef(-self._center[0], -self._center[1], 0)
		super(CustomScene, self).DrawGLScene()

		glEnable( GL_POINT_SMOOTH );
		glEnable( GL_LINE_SMOOTH );
		glEnable( GL_POLYGON_SMOOTH );
		glHint( GL_POINT_SMOOTH_HINT, GL_NICEST );
		glHint( GL_LINE_SMOOTH_HINT, GL_NICEST );
		glHint( GL_POLYGON_SMOOTH_HINT, GL_NICEST );		

		if len(self.points)>0:
			glPointSize(3)
			glEnableClientState(GL_COLOR_ARRAY)
			glEnableClientState(GL_VERTEX_ARRAY)
			glColorPointer(4, GL_FLOAT, 0, np.array(self.colors) );
			glVertexPointer(3, GL_FLOAT, 0, np.array(self.points) )
			glDrawElements(GL_POINTS,len(self.points), GL_UNSIGNED_SHORT, range(len(self.points)))
			glDisableClientState(GL_VERTEX_ARRAY)
			glDisableClientState(GL_COLOR_ARRAY)
			
			glPointSize(1)
			
