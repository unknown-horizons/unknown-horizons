#!/usr/bin/env python

from __future__ import with_statement
from distutils.core import setup
from distutils.command.build import build
from distutils.spawn import spawn, find_executable
from DistUtilsExtra.command import *
import os
import platform
from glob import glob
from commands import getoutput
from shutil import move, rmtree

# Ensure we are in the correct directory
os.chdir(os.path.realpath(os.path.dirname(__file__)))

if platform.dist()[0].lower() in ('debian', 'ubuntu'):
	executable_path = 'games'
else:
	executable_path = 'bin'

data = [
        (executable_path, ('unknown-horizons', )),
        ('share/pixmaps', ('content/unknown-horizons.xpm', )),
        ('share/unknown-horizons', ('settings-dist.xml', ))
       ]

for root, dirs, files in filter(lambda x: len(x[2]), os.walk('content')):
	data.append(('share/unknown-horizons/%s' % root,
		['%s/%s' % (root, f) for f in files]))

packages = []
for root, dirs, files in os.walk('horizons'):
	packages.append(root)

# Add enet files for build platform
type = platform.system().lower()
arch = platform.machine()
dir = "horizons/network/%s-x%s" % (type, arch[-2:])
package_data = { dir: ['*.so'] }

class _build_i18n(build_i18n.build_i18n):
	def run(self):
		"""
		Check for more information:
		http://hotwire-shell.googlecode.com/svn/trunk/DistUtilsExtra/command/build_i18n.py
		Since specifying a .mofile dir is not supported, we manually move build/mo/
		to a place more appropriate in our opinion, currently content/lang/.
		"""
		build_i18n.build_i18n.run(self)
		rmtree(os.path.join("content", "lang"))
		move(os.path.join("build", "mo"), \
		     os.path.join("content", "lang"))

class _build_man(build):
	description = "build the Manpage"

	def run(self):
		if not find_executable('xsltproc'):
			self.warn("Can't build manpage, needs xsltproc")
			return

		self.make_file(['doc/manpage.xml'], 'unknown-horizons.6', spawn, \
		               (['xsltproc',
		                 'http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl',
		                 'doc/manpage.xml'],))
		self.distribution.data_files.append(('share/man/man6', ('unknown-horizons.6',)))

build.sub_commands.append(('build_man', None))

cmdclass = {
	'build': build_extra.build_extra,
	'build_man': _build_man,
	'build_i18n': _build_i18n,
}

setup(
	name='UnknownHorizons',
	version='2011.1',
	description='Realtime Economy Simulation and Strategy Game',
	author='The Unknown Horizons Team',
	author_email='team@unknown-horizons.org',
	url='http://www.unknown-horizons.org',
	packages=packages,
	package_data=package_data,
	data_files=data,
	cmdclass=cmdclass)
