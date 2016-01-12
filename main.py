#! /usr/bin/python
from __init__ import *
from modules.HeatMapApp import HeatMapApp
from modules.GraphApp import GraphApp

class Main(GraphApp, HeatMapApp):
	

	def __init__(self):
		GraphApp.__init__(self,'Density')
		HeatMapApp.__init__(self,'Density')

		print self._modules_tabs



if __name__ == "__main__":  app.startApp(Main)