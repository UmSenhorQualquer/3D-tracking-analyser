#! /usr/bin/python
from __init__ import *
from TrackingDataFile 	 import TrackingDataFile
from PyQt4 import QtGui
import numpy as np, math, csv, os, cv2, visvis as vv

def lin_dist3d(p0, p1):   return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2 + (p0[2] - p1[2])**2)

class BaseApp(BaseWidget):
	"""Application form"""

	def __init__(self, title=''):
		super(BaseApp,self).__init__(title)

		self._progress 	= ControlProgress('Processing')
		self._boundings = ControlBoundingSlider('Ranges', horizontal = True)
		self._formset 	= [(' ','Frames bounding',' '),'_boundings',' ','_progress']

		#Controls organization definition		
		self.mainmenu = [
				{ 'File': [
						{'Open csv file': self.__open_tracking_file },
						'-',
						{'Export data': self.__export_tracking_file },
						'-',
						{'Exit': exit}
					]
				}
			]

		self._data = None

		#Events definition
		self._csvParser = CsvParserDialog()
		self._csvParser.loadFileEvent = self.load_tracking_file
		self._boundings.changed = self.frames_boundings_changed


	def frames_boundings_changed(self):
		pass
		
		

	def __open_tracking_file(self): 
		#Open the CSV parser window
		self._csvParser.show()

	def load_tracking_file(self):
		#Load all the data from the CSV to the memory
		if self._csvParser.filename!=None:
			
			separator 	= self._csvParser.separator
			frame 	  	= self._csvParser.frameColumn
			x     		= self._csvParser.xColumn
			y     		= self._csvParser.yColumn
			z     		= self._csvParser.zColumn

			#Load the file to memory
			self._data = TrackingDataFile(self._csvParser, separator, frame, x, y, z); self._csvParser.close()
			
			self._progress.min = 0
			self._progress.max = len(self._data)
			self._boundings.min = -len(self._data)*0.05
			self._boundings.max = len(self._data)*1.05
			self._boundings.value = 0, len(self._data)
			
			
			self._velocities	= []
			self._accelerations = []

			lastVelocity 		= None
			for i in range(len(self._data)-1):
				
				if self._data[i]!=None:
					pos0 = self._data[i].position
					pos1 = self._data[i+1].position

					#calculate the velocity
					velocity = lin_dist3d(pos1, pos0)
					self._velocities.append( velocity )

					#calculate the acceleration
					if lastVelocity!=None:  self._accelerations.append( velocity-lastVelocity )
					lastVelocity = velocity

				self._progress.value = i

			self._progress.value = len(self._data)


	def __export_tracking_file(self):

		filename = QtGui.QFileDialog.getSaveFileName(self, 'Select a file', selectedFilter='*.csv')
		if not filename: return
		filename = str(filename)

		lower = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		xDiff = int(round( (self._data.xRange[1]-self._data.xRange[0]+1)*self.SCALE))
		yDiff = int(round( (self._data.yRange[1]-self._data.yRange[0]+1)*self.SCALE))
		zDiff = int(round( (self._data.zRange[1]-self._data.zRange[0]+1)*self.SCALE))

		try:
			sphere = sphere_x, sphere_y, sphere_z, sphere_r = eval(self._sphere.value)
		except:
			sphere = None

		min_vel, max_vel = self._velocityBnds.value

		with open(filename, 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',')
	
	
			for i in range(int(lower), int(higher)-1 ):
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

					pos0 = self._data[i].position
					pos1 = self._data[i+1].position
					vel = lin_dist3d(pos1, pos0)*1000.0

					if 	(min_vel<=vel<=max_vel) and \
						(
							((sphere!=None and lin_dist3d( (x,y,z), (sphere_x, sphere_y, sphere_z) )<=sphere_r)) or \
							sphere==None
						):
						spamwriter.writerow(self._data[i].row)
					
					
		
		
	######################################################################################
	#### EVENTS ##########################################################################
	######################################################################################





if __name__ == "__main__":  app.startApp(BaseApp)
