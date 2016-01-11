#! /usr/bin/python
from __init__ import *
from modules.HeatMapApp import HeatMapApp
from modules.GraphApp import GraphApp
from modules.BaseApp import BaseApp

class Main(GraphApp, HeatMapApp,BaseApp):
	

	def __init__(self):
		BaseApp.__init__(self,'Density')
		GraphApp.__init__(self,'Density')
		HeatMapApp.__init__(self,'Density')

		self._formset = [
			(' ','Frames bounding',' '),
			'_boundings',
			{
				'Heat map': [
					('_colorMap','   |   ','Filters:','_toggleMapVars','_toggleSphere','_sphere','   |   ','_calcButton', ' '),
					('_mapVarsList', '_minVar', '_varsBnds','_maxVar'),					
					('_map','_colorsBnds')
				],
				'Graphs': [ 
					('_toggleVars',' '),
					'_varsList',
					'_loadGraph',
					'_graph'
				],				
			},
			'_progress'
		]



if __name__ == "__main__":  app.startApp(Main)