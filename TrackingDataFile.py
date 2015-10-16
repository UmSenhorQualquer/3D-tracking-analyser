import csv, cv2, math, numpy as np
from scipy.interpolate import interp1d
from TrackingRow import TrackingRow


class TrackingDataFile:

	def __init__(self, filename=None, separator=',', frameCol=0, xCol=1, yCol=2, zCol=None):
		self._data = []

		TrackingRow.FRAME_COL = frameCol
		TrackingRow.X_COL 	  = xCol
		TrackingRow.Y_COL 	  = yCol
		TrackingRow.Z_COL 	  = zCol

		self._xRange = [0,0]
		self._yRange = [0,0]
		self._zRange = [0,0]

		self._separator 	= separator
		if filename!=None and filename!='': self.importCSV(filename)

	def importCSV(self, filename):
		with open(filename, 'U') as csvfile:
			spamreader = csv.reader(csvfile, delimiter=self._separator, quotechar='"')
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

				#If the first frame is not 0 then insert none values until the first frame with the position
				#if len(data)==0 and rowdata.frame>0:  data = [None for i in range(rowdata.frame)]
				#Add none values for missing frames
				#if len(data)>0 and data[-1]!=None and (rowdata.frame-data[-1].frame)>1:
				#	for i in range(data[-1].frame+1, rowdata.frame): data.append(None)

				data.append(rowdata)
			self._data = data

	

	

	def exportCSV(self, filename):
		with open(filename, 'wb') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=self._separator)
			#spamwriter.writerow(['Frame','Name','pos X','pos Y','head X','head Y','tail X','tail Y'])
			for data in self._data:
				if data!=None:
					spamwriter.writerow(data.row)

	@property
	def xRange(self): return self._xRange

	@property
	def yRange(self): return self._yRange

	@property
	def zRange(self): return self._zRange
	

	def __getitem__(self, index):
		if index<len(self._data):
			return self._data[index]
		else:
			return None



	def __len__(self): return len(self._data)



if __name__=='__main__':
	data = TrackingDataFile('tmp/output/virgin_wt_CS_2_2014-02-26-103556-0000_mtout.csv')
