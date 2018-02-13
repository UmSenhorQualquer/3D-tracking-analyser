#! /usr/bin/python
from AnyQt.QtWidgets import QFileDialog
from modules.BaseApp import BaseApp
import numpy as np, math, csv, os, cv2, visvis as vv, decimal

from pyforms.controls import ControlButton
from pyforms.controls import ControlText
from pyforms.controls import ControlCombo
from pyforms.controls import ControlBoundingSlider
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlVisVisVolume

def lin_dist3d(p0, p1):   return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2 + (p0[2] - p1[2])**2)



class HeatMapApp(BaseApp):
	"""Application form"""

	def __init__(self, title='Heat map'):
		super(HeatMapApp, self).__init__(title)

		self._heatmapImg 	= None #Store a numpy array with the heatmap
		self._velocities    = None #Store the velocities for each frame
		self._accelerations = None #Store the accelarations for each frame

		##### CONTROLS ##############################################################################
		self._heatmap   				= ControlVisVisVolume("Volume")
		self._toggleSphereVisibility 	= ControlButton('Filter by a region', checkable=True)
		self._sphere 					= ControlText('Position filter (x,y,z,radius)')

		self._toggleHeatmapVars    		= ControlButton('Select variables', checkable=True)
		self._heatmapVarsBnds			= ControlBoundingSlider('Variable bounds', horizontal=True)
		self._heatmapHigherVarsValues 	= ControlCheckBox('Most higher', helptext='Show only the higher values')

		self._heatmapColor 				= ControlCombo('Color map')
		self._apply2Heatmap 			= ControlButton('Apply to map')

		self._heatmapColorsBnds			= ControlBoundingSlider('Colors', horizontal=False)
		self._heatmapVarsList			= ControlCombo('Variables')
		self._heatmapVars				= ControlCheckBox('Map variables')

		self._heatMapMinVar				= ControlText('Min vel.')
		self._heatMapMaxVar				= ControlText('Max vel.')

		#############################################################################################
		self._modules_tabs.update({
			'Heat map': [
				('_heatmapColor','   |   ','Filters:','_toggleHeatmapVars','_toggleSphereVisibility', '_sphere','   |   ','_apply2Heatmap', ' '),
				('_heatmapVarsList','_heatmapVars','_heatmapHigherVarsValues', '_heatMapMinVar', '_heatmapVarsBnds','_heatMapMaxVar'),					
				{'Map':('_heatmap','_heatmapColorsBnds')}
			]
		})
		#############################################################################################
		
		self._heatmapVarsList += 'Velocity'
		self._heatmapVarsList += 'Acceleration'		

		self._heatmapColor.add_item( 'Bone', 	vv.CM_BONE )
		self._heatmapColor.add_item( 'Cool', 	vv.CM_COOL )
		self._heatmapColor.add_item( 'Copper', 	vv.CM_COPPER )
		self._heatmapColor.add_item( 'Gray', 	vv.CM_GRAY )
		self._heatmapColor.add_item( 'Hot', 		vv.CM_HOT )
		self._heatmapColor.add_item( 'HSV', 		vv.CM_HSV )
		self._heatmapColor.add_item( 'Jet', 		vv.CM_JET )
		self._heatmapColor.add_item( 'Pink', 	vv.CM_PINK )
		self._heatmapColor.add_item( 'Autumn', 	vv.CM_AUTUMN )
		self._heatmapColor.add_item( 'Spring', 	vv.CM_SPRING )
		self._heatmapColor.add_item( 'Summer', 	vv.CM_SUMMER )
		self._heatmapColor.add_item( 'Winter', 	vv.CM_WINTER )
		self._heatmapColor.value = vv.CM_HSV		

		self._sphere.hide()
		self._heatmapVarsBnds.hide()
		self._heatmapVarsList.hide()
		self._heatMapMinVar.hide()
		self._heatMapMaxVar.hide()
		self._heatmapVars.hide()
		self._heatmapHigherVarsValues.hide()
		self._heatmapVarsBnds.convert_2_int   	= False
		self._heatmapColorsBnds.convert_2_int 	= False
		
		self._apply2Heatmap.value 			= self.calculate_heatmap_event
		self._heatmapColor.changed   		= self.changed_heatmap_color_event
		self._toggleSphereVisibility.value 	= self.__toggle_sphere_visiblity_event
		self._toggleHeatmapVars.value   	= self.__toggle_variables_visibility_event
		self._heatmapVarsList.changed 		= self.__changed_heatmap_variables_list_event
		self._heatMapMinVar.changed 		= self.__changed_heatmap_minVar_event
		self._heatMapMaxVar.changed 		= self.__changed_heatmap_maxVar_event
		self._heatmapColorsBnds.changed		= self.changed_heatmap_colors_bounds_event
		self._heatmapVars.changed 			= self.__changed_heatmap_variables_event

		

	############################################################################################
	### AUXILIAR FUNCTIONS #####################################################################
	############################################################################################

	def __calc_heatmap_size(self, x_diff, y_diff, z_diff, scale=None):
		"""
		Calculate the heatmap size
		"""
		if scale==None: scale = self.fit_scale(x_size, y_size, z_size)
		x_scaled_size = int( round( (x_diff+1)*scale) )
		y_scaled_size = int( round( (y_diff+1)*scale) )
		z_scaled_size = int( round( (z_diff+1)*scale) )
		return x_scaled_size, y_scaled_size, z_scaled_size

	def fit_scale(self, x_diff, y_diff, z_diff):
		"""
		Calculate the scale value that should be applied to each position, so they can fit in an numpy array
		"""
		scale 		= 1.0
		new_scale 	= 1.0
		x_size, y_size, z_size = 0,0,0
		
		#The maximum allowed size for the heatmap is (2000,2000,2000)
		while x_size<=2000.0 and y_size<=2000.0 and z_size<=2000.0:
			scale 		= new_scale
			new_scale 	= scale * 10.0
			x_size, y_size, z_size = self.__calc_heatmap_size(x_diff, y_diff, z_diff, new_scale)
		return scale


	############################################################################################
	### EVENTS #################################################################################
	############################################################################################

	def __changed_heatmap_variables_event(self):
		if self._heatmapVars.value:
			self._heatmapHigherVarsValues.show()
		else:
			self._heatmapHigherVarsValues.hide()

	def __toggle_sphere_visiblity_event(self):
		if self._toggleSphereVisibility.checked:
			self._sphere.show()
		else:
			self._sphere.hide()

	def __toggle_variables_visibility_event(self):
		if self._toggleHeatmapVars.checked:
			self._heatmapVarsList.show()
			self._heatmapVarsBnds.show()
			self._heatMapMinVar.show()
			self._heatMapMaxVar.show()
			self._heatmapVars.show()
		else:
			self._heatmapVarsList.hide()
			self._heatmapVarsBnds.hide()
			self._heatMapMinVar.hide()
			self._heatMapMaxVar.hide()
			self._heatmapVars.hide()
		

	def changed_heatmap_colors_bounds_event(self):
		if self._heatmapImg is None or not self._heatmapImg.any(): return
		self._heatmap.colors_limits = self._heatmapColorsBnds.value

	def __changed_heatmap_minVar_event(self):
		if self._heatMapMinVar.value=='': return

		v = eval(self._heatMapMinVar.value)
		self._heatmapVarsBnds.min = v
		values = list(self._heatmapVarsBnds.value)

		if values[0]<v: values[0] = v
		self._heatmapVarsBnds.value = values

	def __changed_heatmap_maxVar_event(self):
		if self._heatMapMaxVar.value=='': return

		v = eval(self._heatMapMaxVar.value)
		self._heatmapVarsBnds.max = v
		values = list(self._heatmapVarsBnds.value)
		
		if values[1]>v: values[1] = v
		self._heatmapVarsBnds.value = values

	def __changed_heatmap_variables_list_event(self):
		
		if self._heatmapVarsList.value=='Velocity' and self._velocities:
			lower 	= int(0 if self._boundings.value[0]<0 else self._boundings.value[0])
			higher 	= int(len(self._velocities) if self._boundings.value[1]>=len(self._velocities) else self._boundings.value[1])
			max_val = max(self._velocities[lower:higher])
			min_val = min(self._velocities[lower:higher])
			self._heatmapVarsBnds.value = round(min_val, 2), round(max_val, 2)
			self._heatMapMinVar.value = str(round(min_val - (max_val-min_val)*0.1, 2))
			self._heatMapMaxVar.value = str(round(max_val + (max_val-min_val)*0.1, 2))

		if self._heatmapVarsList.value=='Acceleration' and self._accelerations:
			lower 	= int(0 if self._boundings.value[0]<0 else self._boundings.value[0])
			higher 	= int(len(self._accelerations) if self._boundings.value[1]>(len(self._accelerations)+1) else self._boundings.value[1])
			max_val = max(self._accelerations[lower:higher])
			min_val = min(self._accelerations[lower:higher])
			self._heatmapVarsBnds.value = round(min_val, 2), round(max_val, 2)
			self._heatMapMinVar.value   = str(round(min_val - (max_val-min_val)*0.1, 2))
			self._heatMapMaxVar.value   = str(round(max_val + (max_val-min_val)*0.1, 2))


	def changed_heatmap_color_event(self): self._heatmap.colorMap = self._heatmapColor.value

	############################################################################################
	### Map generation #########################################################################
	############################################################################################

	def calculate_heatmap_event(self):
		#Filter for the data from a lower and upper frame
		if self._data is None: return
		
		self._progress.min = lower 	= 0 if self._boundings.value[0]<0 else int(self._boundings.value[0])
		self._progress.max = higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else int(self._boundings.value[1])

		#Calculate the size of the map
		x_diff = self._data.xRange[1]-self._data.xRange[0]
		y_diff = self._data.yRange[1]-self._data.yRange[0]
		z_diff = self._data.zRange[1]-self._data.zRange[0]
		scale  = self.fit_scale(x_diff, y_diff, z_diff) #Fit the best scale value
		x_size, y_size, z_size = self.__calc_heatmap_size(x_diff, y_diff, z_diff, scale) #Return the best size for the map image
		
		try: 	sphere = sphere_x, sphere_y, sphere_z, sphere_r = eval(self._sphere.value)
		except: sphere = None
		min_var, max_var = self._heatmapVarsBnds.value
		which_var = 0 if self._heatmapVarsList.value=='Velocity' else 1
		
		#Create the map image
		img = np.zeros( (z_size,x_size,y_size), dtype=np.float32)

		for i in range(lower, higher):
			if (i % 3000)==0: self._progress.value = i
			if self._data[i]!=None:
				position = self._data[i].position
			
				#shift and scale the coordenates, to avoid negative and decimal values
				#is only possible to map in the image positive and integer coordenates
				x, y, z = position
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

					if self._heatmapVars.value:
						#Map the variables
						if self._heatmapHigherVarsValues.value:
							tmp = img[z-1:z+1,x-1:x+1,y-1:y+1]
							tmp[tmp<var] = var
						else:
							img[z-1:z+1,x-1:x+1,y-1:y+1] += var
					else:
						#Map positions
						img[z-1:z+1,x-1:x+1,y-1:y+1] += 1.0
				else:
					#Map positions
					img[z-1:z+1,x-1:x+1,y-1:y+1] += 1.0

		self._progress.value = higher

		color_min = np.min(img)
		color_max = np.max(img)
		self._heatmapColorsBnds.min = color_min - (color_max-color_min)*0.1
		self._heatmapColorsBnds.max = color_max + (color_max-color_min)*0.1
		self._heatmapColorsBnds.value = color_min, color_max

		self._heatmap.value 		= np.zeros((1,1), dtype=np.float32)
		self._heatmap.colors_limits = None		
		self._heatmap.value 		= img
		self._heatmapImg 			= img


	############################################################################################
	### CLASS OVERRIDE FUNCTIONS ###############################################################
	############################################################################################

	def frames_boundings_changed(self):
		super(HeatMapApp,self).frames_boundings_changed()
		self.__changed_heatmap_variables_list_event()

	def load_tracking_file(self):
		super(HeatMapApp,self).load_tracking_file()
		self.__changed_heatmap_variables_list_event()


	def export_tracking_file(self):

		filename,_ = QFileDialog.getSaveFileName(self, 'Select a file', selectedFilter='*.csv')
		if not filename: return
		filename = str(filename)
		if not filename.lower().endswith('.csv'): filename += '.csv'

		#Export only the selected bounds
		lower  = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		which_var = 0 if self._heatmapVarsList.value=='Velocity' else 1
		try:    sphere = sphere_x, sphere_y, sphere_z, sphere_r = eval(self._sphere.value)
		except: sphere = None

		min_var, max_var = self._heatmapVarsBnds.value

		#Calculate the size of the map
		x_diff = self._data.xRange[1]-self._data.xRange[0]
		y_diff = self._data.yRange[1]-self._data.yRange[0]
		z_diff = self._data.zRange[1]-self._data.zRange[0]
		scale  = self.fit_scale(x_diff, y_diff, z_diff) #Fit the best scale value
		
		with open(filename, 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',')
	
			for i in range(int(lower), int(higher) ):
				self._progress.value = i

				position = self._data[i].position
				x, y, z  = position
				x += abs(self._data.xRange[0])
				y += abs(self._data.yRange[0])
				z += abs(self._data.zRange[0])
				x = int(round(x*scale))
				y = int(round(y*scale))
				z = int(round(z*scale))

				if sphere!=None and lin_dist3d( (x,y,z), (sphere_x, sphere_y, sphere_z) )>sphere_r: continue
				
				if self._toggleHeatmapVars.checked:
					var  = self._velocities[i] if which_var==0 else self._accelerations[i]
					if not(min_var<=var<=max_var): continue
				
				if self._data[i]==None: continue

				row2save = self._data[i].row
				if i>lower: 	row2save = row2save + [self._velocities[i]   ]
				if (i+1)>lower: row2save = row2save + [self._accelerations[i]]
				spamwriter.writerow(row2save)

	

if __name__ == "__main__":  app.startApp(HeatMapApp)
