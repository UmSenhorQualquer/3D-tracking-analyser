#! /usr/bin/python
from __init__ import *
from ChooseColumnsWindow import ChooseColumnsWindow
from TrackingDataFile import TrackingDataFile
from PyQt4 import QtCore, QtGui
import numpy as np, math, csv
import os, cv2, numpy as np
import datetime, time
import visvis as vv

try:
	import dicom, dicom.UID
	from dicom.dataset import Dataset, FileDataset
except:
	print("no dicom library installed")


def lin_dist3d(p0, p1):   return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2 + (p0[2] - p1[2])**2)


#Not being used at the moment
def write_dicom(pixel_array,filename):
	"""
	INPUTS:
	pixel_array: 2D numpy ndarray.  If pixel_array is larger than 2D, errors.
	filename: string name for the output file.
	"""

	## This code block was tak en from the output of a MATLAB secondary
	## capture.  I do not know what the long dotted UIDs mean, but
	## this code works.
	file_meta = Dataset()
	file_meta.MediaStorageSOPClassUID = 'Secondary Capture Image Storage'
	file_meta.MediaStorageSOPInstanceUID = '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385720736873780'
	file_meta.ImplementationClassUID = '1.3.6.1.4.1.9590.100.1.0.100.4.0'
	ds = FileDataset(filename, {},file_meta = file_meta,preamble="\0"*128)
	ds.Modality = 'WSD'
	ds.ContentDate = str(datetime.date.today()).replace('-','')
	ds.ContentTime = str(time.time()) #milliseconds since the epoch
	ds.StudyInstanceUID =  '1.3.6.1.4.1.9590.100.1.1.124313977412360175234271287472804872093'
	ds.SeriesInstanceUID = '1.3.6.1.4.1.9590.100.1.1.369231118011061003403421859172643143649'
	ds.SOPInstanceUID =    '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385720736873780'
	ds.SOPClassUID = 'Secondary Capture Image Storage'
	ds.SecondaryCaptureDeviceManufctur = 'Python 2.7.3'

	## These are the necessary imaging components of the FileDataset object.
	ds.SamplesPerPixel = 1
	ds.PhotometricInterpretation = "MONOCHROME2"
	ds.PixelRepresentation = 0
	ds.HighBit = 15
	ds.BitsStored = 16
	ds.BitsAllocated = 16
	ds.SmallestImagePixelValue = '\\x00\\x00'
	ds.LargestImagePixelValue = '\\xff\\xff'
	ds.Columns = pixel_array.shape[0]
	ds.Rows = pixel_array.shape[1]
	if pixel_array.dtype != np.uint16:
		pixel_array = pixel_array.astype(np.uint16)
	ds.PixelData = pixel_array.tostring()

	ds.save_as(filename)
	return

class TrackingDensity(BaseWidget):
	"""Application form"""

	def __init__(self):
		super(TrackingDensity,self).__init__('Tracking density')

		self.SCALE = 10.0


		self._visvis   			= ControlVisVisVolume("Volume")
		self._graph   			= ControlVisVis("Graph")
		self._progress 			= ControlProgress('Generating cube')
		self._sphere 			= ControlText('Position filter (x,y,z,radius)')
		self._colorMap 			= ControlCombo('Color map')
		self._boundings 		= ControlBoundingSlider('Ranges', horizontal = True)
		self._calcButton 		= ControlButton('Calculate map')
		self._posOverTimeButton = ControlButton('Calculate position over time')
		self._velOverTimeButton = ControlButton('Velocity over time')
		self._accOverTimeButton = ControlButton('Accelaration over time')
		self._velocityBnds		= ControlBoundingSlider('Velocities thresh', horizontal = True)
		
		self._formset = [
			'_boundings',
			{
				'Map': [ ('_colorMap','_sphere','_calcButton'),'_velocityBnds','_visvis'],
				'Graphs': [ 
					('_posOverTimeButton','_velOverTimeButton', '_accOverTimeButton'),
					'_graph'],
			},
			'_progress'
		]

		self._colorMap.addItem( 'Bone', vv.CM_BONE )
		self._colorMap.addItem( 'Cool', vv.CM_COOL )
		self._colorMap.addItem( 'Copper', vv.CM_COPPER )
		self._colorMap.addItem( 'Gray', vv.CM_GRAY )
		self._colorMap.addItem( 'Hot', vv.CM_HOT )
		self._colorMap.addItem( 'HSV', vv.CM_HSV )
		self._colorMap.addItem( 'Jet', vv.CM_JET )
		self._colorMap.addItem( 'Pink', vv.CM_PINK )
		self._colorMap.addItem( 'Autumn', vv.CM_AUTUMN )
		self._colorMap.addItem( 'Spring', vv.CM_SPRING )
		self._colorMap.addItem( 'Summer', vv.CM_SUMMER )
		self._colorMap.addItem( 'Winter', vv.CM_WINTER )

		self._colorMap.changed = self.__updateColorMap
		
		self.mainmenu = [
				{ 'File': [
						{'Open': self.__open_tracking_file },
						'-',
						{'Export': self.__export_tracking_file },
						'-',
						{'Exit': exit}
					]
				}
			]

		self._fileSetupWindow = ChooseColumnsWindow()
		self._fileSetupWindow.loadFileEvent = self.__load_tracking_file
		self._calcButton.value = self.__calculateMap
		self._posOverTimeButton.value = self.__calculate_2d_positions_overtime
		self._velOverTimeButton.value = self.__velocity_overtime
		self._accOverTimeButton.value = self.__accelaration_overtime

		self._colorMap.value = vv.CM_HSV

		
	def __updateColorMap(self):
		self._visvis.colorMap = self._colorMap.value

	def __open_tracking_file(self):
		self._fileSetupWindow.show()

	def __load_tracking_file(self):
		if self._fileSetupWindow.filename!=None:
			
			separator = self._fileSetupWindow.separator
			frame = self._fileSetupWindow.frameColumn
			x     = self._fileSetupWindow.xColumn
			y     = self._fileSetupWindow.yColumn
			z     = self._fileSetupWindow.zColumn

			self._data = TrackingDataFile(self._fileSetupWindow.filename, separator, frame, x, y, z)
		
			self._fileSetupWindow.close()
			
			self._boundings.min = -len(self._data)/100.0
			self._boundings.max = len(self._data)+len(self._data)/100.0
			self._boundings.value = [0, len(self._data)]

			self._velocityBnds.max = 100000
			self._velocityBnds.value = 0,100000

			
			self.__calculateMap()


	def __accelaration_overtime(self):
		lower = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		accelarations = []
		for i in range(int(lower), int(higher)-2 ):
			self._progress.value = i
			if self._data[i]!=None:
				pos0 = self._data[i].position
				pos1 = self._data[i+1].position
				pos2 = self._data[i+2].position
				vel0 = lin_dist3d(pos1, pos0)
				vel1 = lin_dist3d(pos2, pos1)

				accelarations.append( (i, vel1-vel0) )
		
		self._graph.value = [accelarations]
			
	def __velocity_overtime(self):
		lower = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		xs = []
		ys = []
		zs = []
		cs = []
		velocities = []

		for i in range( int(lower), int(higher)-1 ):
			self._progress.value = i
			if self._data[i]!=None:
				pos0 = self._data[i].position
				pos1 = self._data[i+1].position
				#velocities.append( (i, lin_dist3d(pos1, pos0)) )
				velocities.append( (i, lin_dist3d(pos1, pos0)) )

				xs.append(pos1[0])
				ys.append(pos1[1])
				#zs.append(pos1[2])
				zs.append(i)
				cs.append(lin_dist3d(pos1, pos0))

		self._velocityBnds.min = int(round(np.min( np.array(cs) )*1000))
		self._velocityBnds.max = int(round(np.max( np.array(cs) )*1000))
		self._velocityBnds.value = self._velocityBnds.min, self._velocityBnds.max
		
		self._graph.value = [velocities]

		"""
		self._mpl.axes = self._mpl.fig.add_subplot(111, projection='3d')
		self._mpl.axes.clear(); 
		pts = self._mpl.axes.scatter(xs, ys, zs, c=cs)
		self._mpl.fig.colorbar(pts
		"""
		
		"""
		from mpl_toolkits.mplot3d import Axes3D
		import matplotlib.pyplot as plt
		fig = plt.figure()
		ax 	= fig.gca(projection='3d')
		pts = ax.scatter(xs, ys, zs, c=cs)
		fig.colorbar(pts )
		ax.set_aspect('equal', 'datalim')
		plt.show()"""



	def __calculate_2d_positions_overtime(self):
		lower = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		positions = []
		for i in range(int(lower), int(higher) ):
			self._progress.value = i
			if self._data[i]!=None:
				x,y,z = self._data[i].position
				positions.append( (x,y,i) )
		
		self._graph.value = [positions]

	def __calculateMap(self):

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

		img = np.zeros( (xDiff,yDiff,zDiff), dtype=np.float32)
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

				if not(min_vel<=vel<=max_vel): continue

				if sphere!=None and lin_dist3d( (x,y,z), (sphere_x, sphere_y, sphere_z) )>sphere_r:
					continue
				
				img[x-2:x+2,y-2:y+2,z-2:z+2] += 1
		
		self._visvis.value = img
		

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
	
	
			for i in range(int(lower), int(higher) ):
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

					if 	not(min_vel<=vel<=max_vel) and \
						sphere!=None and lin_dist3d( (x,y,z), (sphere_x, sphere_y, sphere_z) )<=sphere_r:
						spamwriter.writerow(self._data[i].row)
					
					
		
		
	######################################################################################
	#### EVENTS ##########################################################################
	######################################################################################





if __name__ == "__main__":  app.startApp(TrackingDensity)
