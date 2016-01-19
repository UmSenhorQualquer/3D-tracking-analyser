#! /usr/bin/python
from __init__ import *
from PyQt4 import QtGui
from BaseApp import BaseApp
import numpy as np, math, csv, os, cv2, visvis as vv, decimal


def lin_dist3d(p0, p1):   return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2 + (p0[2] - p1[2])**2)



class HeatMapApp(BaseApp):
	"""Application form"""

	def __init__(self, title='Heat map'):
		super(HeatMapApp, self).__init__(title)

		self._mapImg = None
		self._velocities    = None
		self._accelerations = None


		self._map   			= ControlVisVisVolume("Volume")
		self._toggleSphere      = ControlButton('Filter by a region', 		checkable=True)
		self._sphere 			= ControlText('Position filter (x,y,z,radius)')
		


		self._toggleMapVars    	= ControlButton('Select variables', 		checkable=True)
		self._varsBnds			= ControlBoundingSlider('Variable bounds', 	horizontal = True)
		self._higherValues 		= ControlCheckBox('Most higher', helptext='Show only the higher values')

		self._colorMap 			= ControlCombo('Color map')
		self._calcButton 		= ControlButton('Apply')

		self._colorsBnds		= ControlBoundingSlider('Colors', horizontal = False)
		self._mapVarsList		= ControlCombo('Variables')
		self._mapvars			= ControlCheckBox('Map variables')

		self._minVar 			= ControlText('Min vel.')
		self._maxVar 			= ControlText('Max vel.')

		self._modules_tabs.update({
			'Heat map': [
					('_colorMap','   |   ','Filters:','_toggleMapVars','_toggleSphere','_sphere','   |   ','_calcButton', ' '),
					('_mapVarsList','_mapvars','_higherValues', '_minVar', '_varsBnds','_maxVar'),					
					{'Map':('_map','_colorsBnds')}
			]
		})
		
		
		self._mapVarsList += 'Velocity'
		self._mapVarsList += 'Acceleration'		

		self._colorMap.addItem( 'Bone', 	vv.CM_BONE )
		self._colorMap.addItem( 'Cool', 	vv.CM_COOL )
		self._colorMap.addItem( 'Copper', 	vv.CM_COPPER )
		self._colorMap.addItem( 'Gray', 	vv.CM_GRAY )
		self._colorMap.addItem( 'Hot', 		vv.CM_HOT )
		self._colorMap.addItem( 'HSV', 		vv.CM_HSV )
		self._colorMap.addItem( 'Jet', 		vv.CM_JET )
		self._colorMap.addItem( 'Pink', 	vv.CM_PINK )
		self._colorMap.addItem( 'Autumn', 	vv.CM_AUTUMN )
		self._colorMap.addItem( 'Spring', 	vv.CM_SPRING )
		self._colorMap.addItem( 'Summer', 	vv.CM_SUMMER )
		self._colorMap.addItem( 'Winter', 	vv.CM_WINTER )

		self._colorMap.changed   = self.updateColorMap
		self._toggleSphere.value = self.__toggle_sphere
		self._toggleMapVars.value   = self.__toggle_variables
		self._sphere.visible 		= False
		self._varsBnds.visible 		= False
		self._mapVarsList.visible 	= False
		self._minVar.visible 		= False
		self._maxVar.visible 		= False
		self._mapvars.visible  		= False
		self._higherValues.visible  = False

		self._varsBnds.convert_2_int   = False
		self._colorsBnds.convert_2_int = False
		

		self._calcButton.value 		= self.calculateMap
		self._mapVarsList.changed 	= self.__update_variables_bounds
		self._minVar.changed 		= self.__minVarChanged
		self._maxVar.changed 		= self.__maxVarChanged
		self._colorMap.value 		= vv.CM_HSV
		self._colorsBnds.changed	= self.refreshColorsEvent
		self._mapvars.changed 		= self.__map_variables_changed

		

	############################################################################################
	### AUXILIAR FUNCTIONS #####################################################################
	############################################################################################

	def __calc_map_size(self, x_diff, y_diff, z_diff, scale=None):
		if scale==None: scale = self.calc_scale(x_diff, y_diff, z_diff)

		x_size = int( round( (x_diff+1)*scale) )
		y_size = int( round( (y_diff+1)*scale) )
		z_size = int( round( (z_diff+1)*scale) )
		return x_size, y_size, z_size

	def calc_scale(self, x_diff, y_diff, z_diff):
		scale 		= 1.0
		new_scale 	= 1.0
		x_size, y_size, z_size = 0,0,0
		
		while x_size<=2000.0 and y_size<=2000.0 and z_size<=2000.0:
			scale 		= new_scale
			new_scale 	= scale * 10.0
			x_size, y_size, z_size = self.__calc_map_size(x_diff, y_diff, z_diff, new_scale)
		return scale


	############################################################################################
	### EVENTS #################################################################################
	############################################################################################

	def __map_variables_changed(self):
		self._higherValues.visible = self._mapvars.value

	def __toggle_sphere(self):
		self._sphere.visible = self._toggleSphere.checked

	def __toggle_variables(self):
		self._mapVarsList.visible 	= self._toggleMapVars.checked
		self._varsBnds.visible 		= self._toggleMapVars.checked
		self._minVar.visible 		= self._toggleMapVars.checked
		self._maxVar.visible 		= self._toggleMapVars.checked
		self._mapvars.visible  		= self._toggleMapVars.checked
		

	def refreshColorsEvent(self):
		if self._mapImg is None or not self._mapImg.any(): return
		self._map.colors_limits = self._colorsBnds.value

	def __minVarChanged(self):
		if self._minVar.value=='': return

		v = eval(self._minVar.value)
		self._varsBnds.min = v
		values = list(self._varsBnds.value)

		if values[0]<v: values[0] = v
		self._varsBnds.value = values

	def __maxVarChanged(self):
		if self._maxVar.value=='': return

		v = eval(self._maxVar.value)
		self._varsBnds.max = v
		values = list(self._varsBnds.value)
		
		if values[1]>v: values[1] = v
		self._varsBnds.value = values

	def updateColorMap(self):
		self._map.colorMap = self._colorMap.value

	def __update_variables_bounds(self):
		
		if self._mapVarsList.value=='Velocity' and self._velocities:
			lower 	= int(0 if self._boundings.value[0]<0 else self._boundings.value[0])
			higher 	= int(len(self._velocities) if self._boundings.value[1]>=len(self._velocities) else self._boundings.value[1])
			max_val = max(self._velocities[lower:higher-1])
			min_val = min(self._velocities[lower:higher-1])
			self._varsBnds.value = min_val, max_val			
			diff 	= (max_val-min_val)
			max_val = max_val + diff*0.1
			min_val = min_val - diff*0.1
			self._minVar.value = str(min_val)
			self._maxVar.value = str(max_val)

		if self._mapVarsList.value=='Acceleration' and self._accelerations:
			lower 	= int(0 if self._boundings.value[0]<0 else self._boundings.value[0])
			higher 	= int(len(self._accelerations) if self._boundings.value[1]>(len(self._accelerations)+1) else self._boundings.value[1])
			max_val = max(self._accelerations[lower:higher-1])
			min_val = min(self._accelerations[lower:higher-1])
			self._varsBnds.value = min_val, max_val			
			diff 	= (max_val-min_val)
			max_val = max_val + diff*0.1
			min_val = min_val - diff*0.1
			self._minVar.value = str(min_val)
			self._maxVar.value = str(max_val)



	############################################################################################
	### Map generation #########################################################################
	############################################################################################

	def calculateMap(self):
		#Filter for the data from a lower and upper frame
		self._progress.min = lower 	= 0 if self._boundings.value[0]<0 else int(self._boundings.value[0])
		self._progress.max = higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else int(self._boundings.value[1])

		

		#Calculate the size of the map
		x_diff = self._data.xRange[1]-self._data.xRange[0]
		y_diff = self._data.yRange[1]-self._data.yRange[0]
		z_diff = self._data.zRange[1]-self._data.zRange[0]
		scale  = self.calc_scale(x_diff, y_diff, z_diff) #Fit the best scale value
		x_size, y_size, z_size = self.__calc_map_size(x_diff, y_diff, z_diff, scale) #Return the best size for the map image
		
		try: 	sphere = sphere_x, sphere_y, sphere_z, sphere_r = eval(self._sphere.value)
		except: sphere = None
		min_var, max_var = self._varsBnds.value
		which_var = 0 if self._mapVarsList.value=='Velocity' else 1
		
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
				if self._toggleMapVars.checked:
					#velocities array has less 1 element than positions array
					if which_var==0 and len(self._velocities)<=i: continue
					#accelarations array has less 2 element than positions array
					if which_var==1 and len(self._accelerations)<=i: continue

					var  = self._velocities[i] if which_var==0 else self._accelerations[i]

					#Filter by variable boundaries
					if not(min_var<=var<=max_var): continue

					if self._mapvars.value:
						#Map the variables
						if self._higherValues.value:
							tmp = img[x-1:x+1,y-1:y+1,z-1:z+1]
							tmp[tmp<var] = var
						else:
							img[x-1:x+1,y-1:y+1,z-1:z+1] += var
					else:
						#Map positions
						img[z-1:z+1,x-1:x+1,y-1:y+1] += 1.0
				else:
					#Map positions
					img[z-1:z+1,x-1:x+1,y-1:y+1] += 1.0

		self._map.colors_limits = None
		self._progress.value = higher

		color_min = np.min(img)
		color_max = np.max(img)
		self._colorsBnds.min = color_min - (color_max-color_min)*0.1
		self._colorsBnds.max = color_max + (color_max-color_min)*0.1
		self._colorsBnds.value = color_min, color_max

		self._mapImg 	= None
		self._map.value = np.zeros((1,1), dtype=np.float32)
		
		self._map.value = img
		self._mapImg 	= img



	############################################################################################
	### CLASS OVERRIDE FUNCTIONS ###############################################################
	############################################################################################

	def frames_boundings_changed(self):
		super(HeatMapApp,self).frames_boundings_changed()
		self.__update_variables_bounds()

	def load_tracking_file(self):
		super(HeatMapApp,self).load_tracking_file()
		self.__update_variables_bounds()

	def export_tracking_file(self):

		filename = QtGui.QFileDialog.getSaveFileName(self, 'Select a file', selectedFilter='*.csv')
		if not filename: return
		filename = str(filename)
		if not filename.lower().endswith('.csv'): filename += '.csv'

		#Export only the selected bounds
		lower  = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		which_var = 0 if self._mapVarsList.value=='Velocity' else 1
		try:
			sphere = sphere_x, sphere_y, sphere_z, sphere_r = eval(self._sphere.value)
		except:
			sphere = None

		min_var, max_var = self._varsBnds.value

		#Calculate the size of the map
		x_diff = self._data.xRange[1]-self._data.xRange[0]
		y_diff = self._data.yRange[1]-self._data.yRange[0]
		z_diff = self._data.zRange[1]-self._data.zRange[0]
		scale  = self.calc_scale(x_diff, y_diff, z_diff) #Fit the best scale value
		
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
				
				if self._toggleMapVars.checked:
					var  = self._velocities[i] if which_var==0 else self._accelerations[i]
					if not(min_var<=var<=max_var): continue
				
				if self._data[i]==None: continue

				row2save = self._data[i].row
				if i>lower: 	row2save = row2save + [self._velocities[i]   ]
				if (i+1)>lower: row2save = row2save + [self._accelerations[i]]
				spamwriter.writerow(row2save)

	

if __name__ == "__main__":  app.startApp(HeatMapApp)
