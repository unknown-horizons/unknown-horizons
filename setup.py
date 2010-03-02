#!/usr/bin/env python

from __future__ import with_statement
from distutils.core import setup
from distutils.command.build import build
from distutils.spawn import spawn, find_executable
from DistUtilsExtra.command import *
import os
import platform
from glob import glob

# Ensure we are in the correct directory
os.chdir(os.path.realpath(os.path.dirname(__file__)))

if platform.dist()[0].lower() in ('debian', 'ubuntu'):
	executable_path = 'games'
else:
	executable_path = 'bin'

data = [
	(executable_path, ('unknown-horizons', )),
	('share/pixmaps', ('content/unknown-horizons.xpm', ))]

for root, dirs, files in filter(lambda x: len(x[2]), os.walk('content')):
	if '.svn' in dirs:
		dirs.remove('.svn')
	data.append(('share/unknown-horizons/%s' % root,
		['%s/%s' % (root, f) for f in files]))

data = filter(lambda x: '.svn' not in x[0], data)

packages = []
for root, dirs, files in os.walk('horizons'):
	if '.svn' in dirs:
		dirs.remove('.svn')
	packages.append(root)

class _build_i18n(build_i18n.build_i18n):
 
	def run(self):
		# Generate POTFILES.in from POTFILES.in.in
		if os.path.isfile("po/POTFILES.in.in"):
			lines = []
			with open("po/POTFILES.in.in") as f:
				for line in f:
					lines.extend(glob(line.strip()))
			with open("po/POTFILES.in", "w") as f:
				f.write("\n".join(lines) + "\n")
		
		build_i18n.build_i18n.run(self)

class _build_man(build):
	description = "build the Manpage"

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

cmdclass = {
	'build': build_extra.build_extra,
	'build_man': _build_man,
	'build_i18n': _build_i18n,
}

setup(
	name='UnknownHorizons',
	version='2009.2',
	description='Realtime Economy Simulation and Strategy Game',
	author='The Unknown Horizons Team',
	author_email='team@unknown-horizons.org',
	url='http://www.unknown-horizons.org',
	packages=packages,
	data_files=data,
	cmdclass=cmdclass)
