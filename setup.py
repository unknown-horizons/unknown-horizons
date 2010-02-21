#!/usr/bin/env python

from distutils.core import setup
from distutils.command.build import build
from distutils.spawn import spawn, find_executable
from glob import glob
import os
import os.path

data = [('share/applications', ('content/unknown-horizons.desktop', )),
	('share/pixmaps', ('content/unknown-horizons.xpm', ))]

for i in filter(lambda x: len(x[2]), os.walk('content')):
	if not '.svn' in os.path.split(i[0]):
		data.append( ('share/unknown-horizons/%s' % i[0], [ '%s/%s' % (i[0], j) for j in i[2]] ) )

for i in os.listdir('po'):
	if os.path.isdir('po/%s' % i):
		if os.path.exists('po/%s/LC_MESSAGES/unknownhorizons.mo' % i):
			data.append( ('share/locale/%s/LC_MESSAGES' % i, ('po/%s/LC_MESSAGES/unknownhorizons.mo' % i,)))

#trans = glob('po/*/LC_MESSAGES/unknownhorizons.mo')

data = filter(lambda x: '.svn' not in x[0], data)

packages = []
for root, dirs, files in os.walk('horizons'):
	if '.svn' in dirs:
		dirs.remove('.svn')
	packages.append(root)

class build_man(build):
	description = "Build the Manpage"

	def run(self):
		if not find_executable('xsltproc'):
			self.warn("Can't build manpage, needs xsltproc")
			return

		for p in ('/usr/share/sgml/docbook/xsl-ns-stylesheets/manpages/docbook.xsl', \
							'/usr/share/xml/docbook/stylesheet/nwalsh/manpages/docbook.xsl', \
							'/usr/share/xml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl'):
			if os.path.exists(p):
				stylesheet = p
				break
		else:
			self.warn("Can't find a suitable stylesheet!")
			return

		self.make_file(['doc/manpage.xml'], 'unknown-horizons.6', spawn, (['xsltproc', stylesheet, 'doc/manpage.xml'],))
		self.distribution.data_files.append(('share/man/man6', ('unknown-horizons.6',)))

build.sub_commands.append(('build_man', None))

cmdclass = {'build_man': build_man}

setup(name='UnknownHorizons',
	  version='2009.2',
	  description='Realtime Economy Simulation and Strategy Game',
	  author='The Unknown Horizons Team',
	  author_email='team@unknown-horizons.org',
	  url='http://www.unknown-horizons.org',
	  packages=packages,
	data_files=data,
	cmdclass=cmdclass,
	scripts=['unknown-horizons']
	  )
