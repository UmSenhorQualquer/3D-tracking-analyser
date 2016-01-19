#! /usr/bin/python
from __init__ import *
from modules.HeatMapApp import HeatMapApp
from modules.GraphApp import GraphApp
from modules.scene_visualizer.SceneApp import SceneApp

class Main(GraphApp, SceneApp):
	
	def __init__(self):
		GraphApp.__init__(self,'Density')
		SceneApp.__init__(self,'Density')

if __name__ == "__main__":  app.startApp(Main)