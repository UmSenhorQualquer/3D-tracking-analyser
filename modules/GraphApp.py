#! /usr/bin/python
from __init__ import *
from modules.BaseApp import BaseApp
import numpy as np, math, csv, os, cv2, visvis as vv

from pyforms.controls import ControlVisVis
from pyforms.controls import ControlButton
from pyforms.controls import ControlCheckBoxList

class GraphApp(BaseApp):
	"""Application form"""

	def __init__(self, title='Variables graphs'):
		super(GraphApp,self).__init__(title)

		self._graph   	  = ControlVisVis("Graph")
		self._toggleVars  = ControlButton('Show/Hide variables', checkable=True)
		self._loadGraph   = ControlButton('Apply')
		self._varsList	  = ControlCheckBoxList('Variables')

		self._varsList += ('Frames',True)
		self._varsList += ('X',True)
		self._varsList += ('Y',True)
		self._varsList += ('Z',False)
		self._varsList += ('Velocity',False)
		self._varsList += ('Acceleration',False)

		self._modules_tabs.update({
			'Graphs': [ 
				('_toggleVars',' '),
				'_varsList',
				'_loadGraph',
				'_graph'],
		})
		
		
		self._loadGraph.value 	= self.__calculate_graph
		self._toggleVars.value = self.__show_hide_variables
		self._varsList.hide()
		self._loadGraph.hide()
	
	def __show_hide_variables(self):
		#Show and hide the variables list
		if self._toggleVars.checked:
			self._varsList.show()
			self._loadGraph.show()
		else:
			self._varsList.hide()
			self._loadGraph.hide()
			
	
	def __calculate_graph(self):
		#Render the graph
		if self._data==None:
			self.warning("Please load the data first.", "The data is missing")
			return

		lower  = 0 if self._boundings.value[0]<0 else self._boundings.value[0]
		higher = len(self._data) if self._boundings.value[1]>(len(self._data)+1) else self._boundings.value[1]

		self._progress.min = lower
		self._progress.max = higher

		values = []
		variables = self._varsList.value

		if len(variables)>3:
			self.warning("Please select the maximum of 3 variables.", "Too many variables selected")
			return

		for i in range(int(lower), int(higher)-2 ):
			self._progress.value = i
			if self._data[i]!=None:
				val = []
				pos = self._data[i].position
					
				if 'Frames' in variables: 		val.append(i)
				if 'X' in variables: 			val.append(pos[0])
				if 'Y' in variables: 			val.append(pos[1])
				if 'Z' in variables: 			val.append(pos[2])
				if 'Velocity' in variables: 	val.append(self._velocities[i])
				if 'Acceleration' in variables: val.append(self._accelerations[i])

				values.append( val )
		
		self._graph.value = [values]
		
		
	


if __name__ == "__main__":  app.startApp(GraphApp)
