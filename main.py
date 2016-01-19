#! /usr/bin/python
from __init__ import *
from modules.GraphApp import GraphApp
from modules.scene_visualizer.SceneApp import SceneApp

class Main(GraphApp, SceneApp):
	
	def __init__(self):
		SceneApp.__init__(self,'Density')
		GraphApp.__init__(self,'Density')
		

if __name__ == "__main__":  app.startApp(Main)