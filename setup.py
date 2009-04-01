#!/usr/bin/python

from distutils.core import setup
from glob import glob
import os

data = []

for i in filter(lambda x: len(x[2])  , os.walk('content')):
	data.append( ('share/unknown-horizons/%s' % i[0], [ '%s/%s' % (i[0], j) for j in i[2]] ) )

setup(name='UnknownHorizons',
	  version='2009.0+svn1989',
	  description='Realtime Economy Simulation and Strategy Game',
	  author='The Unknown Horizons Team',
	  author_email='team@unknown-horizons.org',
	  url='http://www.unknown-horizons.org',
	  packages=['horizons', 
				'horizons.util', 
				'horizons.world',
				'horizons.world.building',
				'horizons.world.units',
				'horizons.ai',
				'horizons.gui',
				'horizons.command',],
	  data_files=data,
	  scripts=['unknown-horizons']
	  )
