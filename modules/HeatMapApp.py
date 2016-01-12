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

		self.SCALE  = 10.0
		self._mapImg = None
		self._velocities    = None
		self._accelerations = None


		self._map   			= ControlVisVisVolume("Volume")
		self._toggleSphere      = ControlButton('Filter by a region', 		checkable=True)
		self._sphere 			= ControlText('Position filter (x,y,z,radius)')
		self._scale 			= ControlText('Scale','10.0',helptext='Scale position values')



		self._toggleMapVars    	= ControlButton('Select variables', 		checkable=True)
		self._varsBnds			= ControlBoundingSlider('Variable bounds', 	horizontal = True)
		self._higherValues 		= ControlCheckBox('Most higher', helptext='Show only the higher values')

		self._colorMap 			= ControlCombo('Color map')
		self._calcButton 		= ControlButton('Apply')

		self._colorsBnds		= ControlBoundingSlider('Colors', horizontal = False)
		self._mapVarsList		= ControlCombo('Variables')

		self._minVar 			= ControlText('Min vel.')
		self._maxVar 			= ControlText('Max vel.')

		self._modules_tabs.update({
			'Heat map': [
					('_scale','_colorMap','   |   ','Filters:','_toggleMapVars','_toggleSphere','_sphere','   |   ','_calcButton', ' '),
					('_mapVarsList', '_higherValues', '_minVar', '_varsBnds','_maxVar'),					
					('_map','_colorsBnds')
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

		self._colorMap.changed   = self.__updateColorMap
		self._toggleSphere.value = self.__toggle_sphere
		self._toggleMapVars.value   = self.__toggle_variables
		self._sphere.visible 		= False
		self._varsBnds.visible 		= False
		self._mapVarsList.visible 	= False
		self._minVar.visible 		= False
		self._maxVar.visible 		= False
		self._higherValues.visible  = False

		self._varsBnds.convert_2_int   = False
		self._colorsBnds.convert_2_int = False
		

		self._calcButton.value 		= self.__calculateMap
		self._mapVarsList.changed 	= self.__update_variables_bounds
		self._minVar.changed 		= self.__minVarChanged
		self._maxVar.changed 		= self.__maxVarChanged
		self._colorMap.value 		= vv.CM_HSV
		self._colorsBnds.changed	= self.__refreshColorsEvent

	def frames_boundings_changed(self):
		super(HeatMapApp,self).frames_boundings_changed()
		self.__update_variables_bounds()


	def __toggle_sphere(self):
		self._sphere.visible = self._toggleSphere.checked

	def __toggle_variables(self):
		self._mapVarsList.visible 	= self._toggleMapVars.checked
		self._varsBnds.visible 		= self._toggleMapVars.checked
		self._minVar.visible 		= self._toggleMapVars.checked
		self._maxVar.visible 		= self._toggleMapVars.checked
		self._higherValues.visible  = self._toggleMapVars.checked

	def __refreshColorsEvent(self):
		if self._mapImg is None or not self._mapImg.any(): return

		color_min, color_max = self._colorsBnds.value

		img 				= self._mapImg.copy()
		img[img<color_min]	= color_min
		img[img>color_max]	= color_max
		self._map.value 	= img

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

	def __updateColorMap(self):
		self._map.colorMap = self._colorMap.value

	

		

	def __calculateMap(self):
		#Filter for the data from a lower and upper frame
		lower 	= 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher 	= len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]


		self._progress.min = lower
		self._progress.max = higher

		xDiff = int( round( (self._data.xRange[1]-self._data.xRange[0]+1)*self.SCALE) )
		yDiff = int( round( (self._data.yRange[1]-self._data.yRange[0]+1)*self.SCALE) )
		zDiff = int( round( (self._data.zRange[1]-self._data.zRange[0]+1)*self.SCALE) )

		try:
			sphere = sphere_x, sphere_y, sphere_z, sphere_r = eval(self._sphere.value)
		except:
			sphere = None

		min_var, max_var = self._varsBnds.value

		which_var = 0 if self._mapVarsList.value=='Velocity' else 1

		img = np.zeros( (xDiff,yDiff,zDiff), dtype=np.float32)
		for i in range( int(lower), int(higher)-1-which_var ):
			self._progress.value = i
			if self._data[i]!=None:
				position = self._data[i].position
			
				x, y, z = position
				x += abs(self._data.xRange[0])
				y += abs(self._data.yRange[0])
				z += abs(self._data.zRange[0])
				x = int(round(x*self.SCALE))
				y = int(round(y*self.SCALE))
				z = int(round(z*self.SCALE))

				if sphere!=None and lin_dist3d( (x,y,z), (sphere_x, sphere_y, sphere_z) )>sphere_r: continue
				
				if self._toggleMapVars.checked:
					var  = self._velocities[i] if which_var==0 else self._accelerations[i]
					if not(min_var<=var<=max_var): continue

					if self._higherValues.value:
						tmp = img[x-2:x+2,y-2:y+2,z-2:z+2]
						tmp[tmp<var] = var
					else:
						img[x-2:x+2,y-2:y+2,z-2:z+2] += var
				else:
					img[x-2:x+2,y-2:y+2,z-2:z+2] += 1.0
		

		color_min = np.min(img)
		color_max = np.max(img)
		self._colorsBnds.min = color_min - (color_max-color_min)*0.1
		self._colorsBnds.max = color_max + (color_max-color_min)*0.1
		self._colorsBnds.value = color_min, color_max

		self._mapImg 	= None
		self._map.value = np.zeros((1,1), dtype=np.float32)
		
		self._map.value = img
		self._mapImg 	= img

		
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


		with open(filename, 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',')
	
			for i in range(int(lower), int(higher) ):
				self._progress.value = i

				position = self._data[i].position
				x, y, z  = position
				x += abs(self._data.xRange[0])
				y += abs(self._data.yRange[0])
				z += abs(self._data.zRange[0])
				x = int(round(x*self.SCALE))
				y = int(round(y*self.SCALE))
				z = int(round(z*self.SCALE))

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
