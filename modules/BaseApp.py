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

		#Only creates the variable if didn't exists yet.
		if not hasattr(self,'_modules_tabs'): self._modules_tabs = {}


		self._formset 	= [(' ','Frames bounding',' '),'_boundings',self._modules_tabs,'_progress']

		#Controls organization definition		
		self.mainmenu = [
				{ 'File': [
						{'Open csv file': self.__open_tracking_file },
						'-',
						{'Export data': self.export_tracking_file },
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
			
			self._progress.min 		= 0
			self._progress.max 		= len(self._data)
			self._boundings.min 	= -len(self._data)*0.05
			self._boundings.max 	= len(self._data)*1.05
			self._boundings.value 	= 0, len(self._data)
						
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


	def export_tracking_file(self):

		filename = QtGui.QFileDialog.getSaveFileName(self, 'Select a file', selectedFilter='*.csv')
		if not filename: return
		filename = str(filename)

		if not filename.lower().endswith('.csv'): filename += '.csv'

		#Export only the selected bounds
		lower = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		with open(filename, 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',')
	
			for i in range(int(lower), int(higher) ):
				self._progress.value = i
				if self._data[i]!=None: spamwriter.writerow(self._data[i].row)
					
					
		
		
	######################################################################################
	#### EVENTS ##########################################################################
	######################################################################################





if __name__ == "__main__":  app.startApp(BaseApp)
