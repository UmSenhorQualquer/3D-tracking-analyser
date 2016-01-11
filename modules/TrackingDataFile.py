import csv, cv2, math, numpy as np
from scipy.interpolate import interp1d
from TrackingRow import TrackingRow


class TrackingDataFile:

	def __init__(self, spamreader, separator=',', frameCol=0, xCol=1, yCol=2, zCol=None):
		self._data = []

		
		TrackingRow.FRAME_COL = frameCol
		TrackingRow.X_COL 	  = xCol
		TrackingRow.Y_COL 	  = yCol
		TrackingRow.Z_COL 	  = zCol

		self._xRange = [0,0]
		self._yRange = [0,0]
		self._zRange = [0,0]

		self._separator 	= separator
		if spamreader is not None: self.import_csv(spamreader)
		

	def import_csv(self, spamreader):		
		data = []		
		for i, row in enumerate(spamreader):
			if TrackingRow.TOTAL_COLS<len(row): TrackingRow.TOTAL_COLS = len(row)

			rowdata = TrackingRow(row)
			if self._xRange[0]>rowdata.x:  self._xRange[0]=rowdata.x
			if self._xRange[1]<rowdata.x:  self._xRange[1]=rowdata.x

			if self._yRange[0]>rowdata.y:  self._yRange[0]=rowdata.y
			if self._yRange[1]<rowdata.y:  self._yRange[1]=rowdata.y

			if self._zRange[0]>rowdata.z:  self._zRange[0]=rowdata.z
			if self._zRange[1]<rowdata.z:  self._zRange[1]=rowdata.z
			data.append(rowdata)

		self._data = data

	def export_csv(self, filename):
		with open(filename, 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=self._separator)
			for data in self._data:
				if data!=None:
					spamwriter.writerow(data.row)


	def __getitem__(self, index):
		return self._data[index] if index<len(self._data) else None

	def __len__(self): return len(self._data)


	@property
	def xRange(self): return self._xRange

	@property
	def yRange(self): return self._yRange

	@property
	def zRange(self): return self._zRange



if __name__=='__main__':
	with open('/home/ricardo/Desktop/01Apollo201403210900/2013.11.23_10.59_scene_out.csv', 'U') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=';')
		data = TrackingDataFile(spamreader)
	
