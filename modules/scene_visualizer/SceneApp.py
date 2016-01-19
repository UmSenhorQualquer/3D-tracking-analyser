#! /usr/bin/python
if __name__ == "__main__":  import sys, os; sys.path.append(os.path.join('..','..') )
from __init__ import *
from modules.HeatMapApp import HeatMapApp, lin_dist3d
from matplotlib import cm
import numpy as np, visvis as vv

try:
	from py3DEngine.utils.WavefrontOBJFormat.WavefrontOBJReader import WavefrontOBJReader
	from py3DEngine.bin.RunScene import RunScene
	from CustomScene import CustomScene
	py3DEngine_loaded = True
except:
	py3DEngine_loaded = False






class SceneApp(HeatMapApp):
	
	def __init__(self, title=''):
		self._points_values = None #used to map a color for each tracking point

		super(SceneApp, self).__init__(title)

		#this module is loaded only if the py3DEngine exists in the system
		if not py3DEngine_loaded: return
		
		##### CONTROLS ##############################################################################
		self._scene_file 	  		 = ControlFile('Scene')
		self._scene_toggle_objs_list = ControlButton('Show/Hide objects', checkable=True)
		self._scene_objs_list  		 = ControlCheckBoxList('Objects')
		self._scene_opengl 	      	 = ControlOpenGL('OpengGL Scene')
		self._scene_points_alfa 	 = ControlSlider('Transparency', 10, 0, 100)
		self._scene_bg_color 		 = ControlCombo('Background color')
		self._scene_apply_colorBnds  = ControlButton('Apply colors boundaries')
		self._scene_points_size      = ControlCombo('Points size')
		self._scene_obj_color		 = ControlText('Object color')

		#############################################################################################
		self._modules_tabs.update({
			'Heat map': [
				('_heatmapColor','   |   ','Filters:','_toggleHeatmapVars','_toggleSphereVisibility', '_sphere','   |   ','_apply2Heatmap', ' '),
				('_heatmapVarsList','_heatmapVars','_heatmapHigherVarsValues', '_heatMapMinVar', '_heatmapVarsBnds','_heatMapMaxVar'),					
				({	
					'1:Map':['_heatmap'],
					'0:Scene':[ 
						[ 
							('_scene_file',' ', '_scene_toggle_objs_list', ' ','_scene_bg_color','  |  ','_scene_points_size','  |  ','_scene_apply_colorBnds'),
							'_scene_points_alfa',
							'_scene_obj_color',
							'_scene_objs_list'
						],
						'=',
						'_scene_opengl'
					]
				}, '_heatmapColorsBnds')
			]
		})
		#############################################################################################

		self._scene_bg_color += ('White', '1,1,1,1.0')
		self._scene_bg_color += ('Gray', '0.3,0.3,0.3,1.0')
		self._scene_bg_color += ('Black', 'None')

		self._scene_points_size += '1'
		self._scene_points_size += '3'
		self._scene_points_size += '6'
		self._scene_points_size += '8'

		self._scene_objs_list.visible 	= False
		self._scene_obj_color.visible 	= False

		self._scene_objs_list.changed 			= self.__changed_objects_list_event
		self._scene_toggle_objs_list.value  	= self.__toggle_objects_list_event
		self._scene_points_alfa.changed  		= self.__changed_scene_points_alfa_event
		self._scene_bg_color.changed 			= self.__changed_background_color_event
		self._scene_apply_colorBnds.value 		= self.__scene_apply_color_bnds_event
		self._scene_points_size.changed   		= self.__changed_scene_points_size_event
		self._scene_objs_list.selectionChanged 	= self.__selectionchanged_object_list_event
		self._scene_obj_color.changed     		= self.__changed_object_color_event

		self._scene 						= None
		self._scene_file.changed 			= self.__scene_file_selected

		self._scene_opengl.clear_color 			= 1,1,1,1
		self._scene_file.value 		= '/home/ricardo/Desktop/01Apollo201403210900/01Apollo201403210900_Scenario.obj'


	def initForm(self):
		super(SceneApp, self).initForm()
		self._splitters[0].setStretchFactor(0,10)
		self._splitters[0].setStretchFactor(1,90)

	############################################################################################
	### EVENTS #################################################################################
	############################################################################################

	def __changed_object_color_event(self):
		index = self._scene_objs_list.mouseSelectedRowIndex
		self._scene.objects[index].color = eval(self._scene_obj_color.value)
		self._scene_opengl.repaint()

	def __selectionchanged_object_list_event(self):
		index = self._scene_objs_list.mouseSelectedRowIndex
		self._scene_obj_color.value = str(self._scene.objects[index].color)
		self._scene_obj_color.label = 'Object color ({0})'.format(self._scene.objects[index].name)

	def __changed_scene_points_size_event(self):
		self._scene.points_size =  eval(self._scene_points_size.value)
		self._scene_opengl.repaint()

	def __toggle_objects_list_event(self):
		self._scene_objs_list.visible = self._scene_toggle_objs_list.checked
		self._scene_obj_color.visible 	= self._scene_toggle_objs_list.checked

	def __changed_background_color_event(self):
		self._scene_opengl.clear_color 	= eval(self._scene_bg_color.value)

	def __changed_scene_points_alfa_event(self):
		if self._points_values!=None:
			self._scene.colors = self.__gen_colors( self._points_values.copy() )
			self._scene_opengl.repaint()

	def __changed_objects_list_event(self):
		x,y,z = 0.0,0.0,0.0
		count = 0.0

		for obj in self._scene.objects:
			obj.active = obj.name in self._scene_objs_list.value
			obj.draw_faces = True

			if obj.active:
				for point in obj.points:
					x+=point[0]
					y+=point[1]
					z+=point[2]
					count+=1.0

		if count==0.0: count=1.0
		self._scene._center = x/count, y/count, z/count
		self._scene_opengl.repaint()

	def __scene_file_selected(self):
		if len(self._scene_file.value)==0: return

		self._scene = CustomScene()
		w = WavefrontOBJReader(self._scene_file.value)
		self._scene.objects = w.objects

		self._scene_opengl.value = self._scene
		self._scene_objs_list.clear()
		for obj in self._scene.objects: self._scene_objs_list += (obj.name, True)

	def __gen_colors(self, values):
		if len(values)==0: return []
		if self._heatmapColor.value==vv.CM_BONE: 	func = 'bone'
		if self._heatmapColor.value==vv.CM_COOL: 	func = 'cool'
		if self._heatmapColor.value==vv.CM_COPPER: 	func = 'copper'
		if self._heatmapColor.value==vv.CM_GRAY: 	func = 'gray'
		if self._heatmapColor.value==vv.CM_HOT: 	func = 'hot'
		if self._heatmapColor.value==vv.CM_HSV: 	func = 'hsv'
		if self._heatmapColor.value==vv.CM_PINK: 	func = 'pink'
		if self._heatmapColor.value==vv.CM_JET: 	func = 'jet'
		if self._heatmapColor.value==vv.CM_AUTUMN: 	func = 'autumn'
		if self._heatmapColor.value==vv.CM_SPRING: 	func = 'spring'
		if self._heatmapColor.value==vv.CM_SUMMER: 	func = 'summer'
		if self._heatmapColor.value==vv.CM_WINTER: 	func = 'winter'

		normalized_vals = np.float32(values) / np.float32(values).max()
		normalized_vals = normalized_vals - normalized_vals.min()
		maximum			= normalized_vals.max()

		func   = getattr(cm, func)
		colors = []

		alpha = float(self._scene_points_alfa.value)/100.0

		for v in normalized_vals:
			color = func(v/maximum)
			colors.append( (color[0],color[1],color[2],alpha) )

		return colors		

	def __scene_apply_color_bnds_event(self):
		self._scene_apply_colorBnds.form.setStyleSheet("")
		if self._heatmapImg is None or not self._heatmapImg.any(): return

		lower, higher = self._heatmapColorsBnds.value
		a = self._points_values.copy()
		a[a<lower]  = lower
		a[a>higher] = higher
		self._scene.colors = self.__gen_colors( a )

	def changed_heatmap_colors_bounds_event(self):
		super(SceneApp, self).changed_heatmap_colors_bounds_event()
		self._scene_apply_colorBnds.form.setStyleSheet("color: red")

	def changed_heatmap_color_event(self):
		super(SceneApp, self).changed_heatmap_color_event()

		if self._points_values!=None:
			self._scene.colors = self.__gen_colors( self._points_values.copy() )
			self._scene_opengl.repaint()
			
	


	def calculate_heatmap_event(self):
		super(SceneApp, self).calculate_heatmap_event()
		
		if self._scene:
			#Filter for the data from a lower and upper frame
			self._progress.min = lower 	= 0 if self._boundings.value[0]<0 else int(self._boundings.value[0])
			self._progress.max = higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else int(self._boundings.value[1])

			#Calculate the size of the map
			x_diff = self._data.xRange[1]-self._data.xRange[0]
			y_diff = self._data.yRange[1]-self._data.yRange[0]
			z_diff = self._data.zRange[1]-self._data.zRange[0]
			scale  = self.fit_scale(x_diff, y_diff, z_diff) #Fit the best scale value

			try: 	sphere = sphere_x, sphere_y, sphere_z, sphere_r = eval(self._sphere.value)
			except: sphere = None
			min_var, max_var = self._heatmapVarsBnds.value
			which_var = 0 if self._heatmapVarsList.value=='Velocity' else 1
		
			
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

					#Filter position by a defined sphere
					if sphere!=None and lin_dist3d( (x,y,z), (sphere_x, sphere_y, sphere_z) )>sphere_r: continue
					
					#Use variables to construct the map, or positions
					if self._toggleHeatmapVars.checked:
						#velocities array has less 1 element than positions array
						if which_var==0 and len(self._velocities)<=i: continue
						#accelarations array has less 2 element than positions array
						if which_var==1 and len(self._accelerations)<=i: continue
						var  = self._velocities[i] if which_var==0 else self._accelerations[i]
						#Filter by variable boundaries
						if not(min_var<=var<=max_var): continue


					values.append( self._heatmapImg[z,x,y] )
					points.append(position)

			self._progress.value = higher

			self._points_values = np.float32(values)
			self._scene.points = points
			self._scene.colors =  self.__gen_colors( self._points_values.copy() )
			
			self._scene_apply_colorBnds.form.setStyleSheet("")

			self._scene_opengl.repaint()


if __name__ == "__main__":  
	import sys
	sys.path.append('..')

	app.startApp(SceneApp)