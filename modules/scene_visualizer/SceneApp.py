#! /usr/bin/python
if __name__ == "__main__":  import sys; sys.path.append('..')
from __init__ import *
from HeatMapApp import HeatMapApp
try:
	from py3DEngine.utils.WavefrontOBJFormat.WavefrontOBJReader import WavefrontOBJReader
	from py3DEngine.bin.RunScene import RunScene
	from CustomScene import CustomScene
	py3DEngine_loaded = True
except:
	py3DEngine_loaded = False

from matplotlib import cm
from visvis import Point, Pointset
import numpy as np
import visvis as vv

class SceneApp(HeatMapApp):
	
	def __init__(self, title=''):
		self._points_values = None #used to map a color for each tracking point

		super(SceneApp, self).__init__(title)
		if not py3DEngine_loaded: return
		
		self._scene_file 	= ControlFile('Scene')
		self._scene_objects = ControlCheckBoxList('Objects')
		self._gl_scene 	    = ControlOpenGL('OpengGL Scene')
		self._transparency  = ControlSlider('Transparency', 10, 0, 100)
		self._bg_color 		= ControlCombo('Background color')
		self._apply_colorBnds = ControlButton('Apply color boundings')

		self._modules_tabs.update({
			'Heat map': [
					('_colorMap','   |   ','Filters:','_toggleMapVars','_toggleSphere','_sphere','   |   ','_calcButton', ' '),
					('_mapVarsList','_mapvars','_higherValues', '_minVar', '_varsBnds','_maxVar'),					
					({	
						'Map':['_map'],
						'0:Scene':[ 
							[ 
								('_scene_file','_transparency','_bg_color','_apply_colorBnds'),
								'_scene_objects'
							],
							'=',
							'_gl_scene'
						]
					}, '_colorsBnds')
			]
		})

		self._bg_color += ('White', '1,1,1,1.0')
		self._bg_color += ('Gray', '0.3,0.3,0.3,1.0')
		self._bg_color += ('Black', 'None')


		self._scene_objects.changed = self.__object_visibility_changed
		self._transparency.changed  = self.__transparency_changed
		self._bg_color.changed 		= self.__background_color_changed
		self._apply_colorBnds.value = self.__apply_color_bnds

		self._scene 				= None
		self._scene_file.changed 	= self.__scene_file_selected

		self._gl_scene.clear_color 	= 1,1,1,1
		self._scene_file.value 		= '/home/ricardo/Desktop/01Apollo201403210900/01Apollo201403210900_Scenario.obj'


	def initForm(self):
		super(SceneApp, self).initForm()

		self._splitters[0].setStretchFactor(0,10)
		self._splitters[0].setStretchFactor(1,90)

	def __background_color_changed(self):
		self._gl_scene.clear_color 	= eval(self._bg_color.value)

	def __transparency_changed(self):
		if self._points_values!=None:
			self._scene.colors = self.__gen_colors( self._points_values.copy() )
			self._gl_scene.repaint()

	def __object_visibility_changed(self):
		x,y,z = 0.0,0.0,0.0
		count = 0.0


		for obj in self._scene.objects:
			obj.active = obj.name in self._scene_objects.value
			obj.draw_faces = True

			if obj.active:
				for point in obj.points:
					x+=point[0]
					y+=point[1]
					z+=point[2]
					count+=1.0

		if count==0.0: count=1.0
		self._scene._center = x/count, y/count, z/count
		self._gl_scene.repaint()


	def __scene_file_selected(self):
		if len(self._scene_file.value)==0: return

		self._scene = CustomScene()
		w = WavefrontOBJReader(self._scene_file.value)
		self._scene.objects = w.objects

		self._gl_scene.value = self._scene
		self._scene_objects.clear()
		for obj in self._scene.objects: self._scene_objects += (obj.name, True)

	def __gen_colors(self, values):
		if self._colorMap.value==vv.CM_BONE: 	func = 'bone'
		if self._colorMap.value==vv.CM_COOL: 	func = 'cool'
		if self._colorMap.value==vv.CM_COPPER: 	func = 'copper'
		if self._colorMap.value==vv.CM_GRAY: 	func = 'gray'
		if self._colorMap.value==vv.CM_HOT: 	func = 'hot'
		if self._colorMap.value==vv.CM_HSV: 	func = 'hsv'
		if self._colorMap.value==vv.CM_PINK: 	func = 'pink'
		if self._colorMap.value==vv.CM_JET: 	func = 'jet'
		if self._colorMap.value==vv.CM_AUTUMN: 	func = 'autumn'
		if self._colorMap.value==vv.CM_SPRING: 	func = 'spring'
		if self._colorMap.value==vv.CM_SUMMER: 	func = 'summer'
		if self._colorMap.value==vv.CM_WINTER: 	func = 'winter'

		normalized_vals = np.float32(values) / np.float32(values).max()
		normalized_vals = normalized_vals - normalized_vals.min()
		maximum			= normalized_vals.max()

		func   = getattr(cm, func)
		colors = []

		alpha = float(self._transparency.value)/100.0

		for v in normalized_vals:
			color = func(v/maximum)
			colors.append( (color[0],color[1],color[2],alpha) )

		return colors		


	def updateColorMap(self):
		super(SceneApp, self).updateColorMap()

		if self._points_values!=None:
			self._scene.colors = self.__gen_colors( self._points_values.copy() )
			self._gl_scene.repaint()
			
	def __apply_color_bnds(self):
		if self._mapImg is None or not self._mapImg.any(): return

		lower, higher = self._colorsBnds.value
		a = self._points_values.copy()
		a[a<lower]  = lower
		a[a>higher] = higher
		self._scene.colors = self.__gen_colors( a )


	def calculateMap(self):
		super(SceneApp, self).calculateMap()
		
		if self._scene:
			#Filter for the data from a lower and upper frame
			self._progress.min = lower 	= 0 if self._boundings.value[0]<0 else int(self._boundings.value[0])
			self._progress.max = higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else int(self._boundings.value[1])

			#Calculate the size of the map
			x_diff = self._data.xRange[1]-self._data.xRange[0]
			y_diff = self._data.yRange[1]-self._data.yRange[0]
			z_diff = self._data.zRange[1]-self._data.zRange[0]
			scale  = self.calc_scale(x_diff, y_diff, z_diff) #Fit the best scale value
			
			values = []
			points = []
			for i in range(lower, higher):
				if (i % 3000)==0:self._progress.value = i
				if self._data[i]!=None:
					x,y,z = position = self._data[i].position

					x += abs(self._data.xRange[0])
					y += abs(self._data.yRange[0])
					z += abs(self._data.zRange[0])
					x = int(round(x*scale))
					y = int(round(y*scale))
					z = int(round(z*scale))

					values.append( self._mapImg[z,x,y] )
					points.append(position)

			self._progress.value = higher

			self._points_values = np.float32(values)
			self._scene.points = points
			self._scene.colors =  self.__gen_colors( self._points_values.copy() )
				


if __name__ == "__main__":  
	import sys
	sys.path.append('..')

	app.startApp(SceneApp)