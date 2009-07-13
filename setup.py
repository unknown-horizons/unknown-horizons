#!/usr/bin/python

from distutils.core import setup
from distutils.command.build import build
from distutils.spawn import spawn, find_executable
from glob import glob
import os
import os.path

data = []

for i in filter(lambda x: len(x[2])  , os.walk('content')):
	data.append( ('share/unknown-horizons/%s' % i[0], [ '%s/%s' % (i[0], j) for j in i[2]] ) )

for i in os.listdir('po'):
	if os.path.isdir('po/%s' % i):
		if os.path.exists('po/%s/LC_MESSAGES/unknownhorizons.mo' % i):
			data.append( ('share/locale/%s/LC_MESSAGES' % i, ('po/%s/LC_MESSAGES/unknownhorizons.mo' % i,)))
#trans = glob('po/*/LC_MESSAGES/unknownhorizons.mo')

data = filter(lambda x: '.svn' not in os.path.split(x[0]), data)

class build_man(build):
	description = "Build the Manpage"
	
	def run(self):
		if not find_executable('xsltproc'):
			self.warn("Can't build manpage, needs xsltproc")
			return

		if os.path.exists('/usr/share/sgml/docbook/xsl-ns-stylesheets/manpages/docbook.xsl'):
			stylesheet = '/usr/share/sgml/docbook/xsl-ns-stylesheets/manpages/docbook.xsl'
		elif os.path.exists('/usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl'):
			stylesheet = '/usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl'
		else:
			self.warn("Can't find a suitable stylesheet!")
			return

		self.make_file(['doc/manpage.xml'], 'unknown-horizons.6', spawn, (['xsltproc', stylesheet, 'doc/manpage.xml'],))
		self.distribution.data_files.append(('share/man/man6', ('unknown-horizons.6',)))

build.sub_commands.append(('build_man', None))

cmdclass = {'build_man': build_man}

setup(name='UnknownHorizons',
	  version='2009.1+svn2463',
	  description='Realtime Economy Simulation and Strategy Game',
	  author='The Unknown Horizons Team',
	  author_email='team@unknown-horizons.org',
	  url='http://www.unknown-horizons.org',
	  packages=['horizons', 
			'horizons.util', 
			'horizons.world',
			'horizons.world.building',
			'horizons.world.units',
			'horizons.world.units.collectors',
			'horizons.world.production',
			'horizons.world.pathfinding',
			'horizons.ai',
			'horizons.ext',
			'horizons.ext.simplejson',
			'horizons.i18n',
			'horizons.gui',
			'horizons.gui.widgets',
			'horizons.gui.tabs',
			'horizons.command',],
	data_files=data,
	cmdclass=cmdclass,
	scripts=['unknown-horizons']
	  )
