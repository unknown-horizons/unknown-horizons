#!/usr/bin/env python2
# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import os
import os.path
import sys

def remove_double(liste):
	return [i.replace('\\\\', '\\') for i in liste]

if not os.path.split(os.getcwd())[1] == 'development':
	print "This program expects to be invoked from the Unknown Horizons development directory"
	sys.exit(-1)

os.chdir('..') #Change to the root directory

installed_files = [] #List of files being installed
installed_dirs  = [] #List of directories being installed

inst = []
remf = []
remd = []

for root, dirs, files in os.walk('.'):
	if 'development' in dirs:
		dirs.remove('development')
	if '.git' in dirs:
		dirs.remove('.git')
	if root[-4:] == 'fife' and len(root.split('\\')) == 2:
		for d in dirs[:]:
			if d not in ('engine', 'tools'):
				dirs.remove(d)
	if '.gitignore' in files:
		files.remove('.gitignore')
	if 'Thumbs.db' in files:
		files.remove('Thumbs.db')
	if 'Setup.exe' in files:
		files.remove('Setup.exe')

	if files or dirs:
		rootp = root[2:]
		if rootp[:4] == 'fife':
			if rootp[-4:] == 'fife' and len(rootp.split('\\')) == 1:
				files = filter(lambda f: f in ('AUTHORS', 'COPYING', 'README'), files)
			elif 'editor' in rootp.split('\\'):
				files = filter(lambda s: s.split('.')[-1] not in ('pyc', 'log'), files)
			else:
				files = filter(lambda s: s.split('.')[-1] in ('dll', 'py', 'pyd'), files)
			if not len(files):
				continue
		else:
			files = filter(lambda s: s.split('.')[-1] not in ('pyc', 'log', 'nsi'), files)
		inst.append( ('	SetOutPath "$INSTDIR/{0!s}"'.format(rootp)).replace('/', '\\'))
		installed_dirs.append(rootp)
		for j in files:
			inst.append( ('	File "./{0!s}/{1!s}"'.format(rootp, j)).replace('/', '\\'))
			installed_files.append('{0!s}/{1!s}'.format(rootp, j))
			if j[-3:] == '.py':
				installed_files.append('{0!s}.pyc'.format('{0!s}/{1!s}'.format(rootp, j))[:-3])

installed_dirs.extend(['fife\\engine\\python', 'fife\\engine', 'fife'])

for f in installed_files:
	remf.append( ('	Delete "$INSTDIR/{0!s}"'.format(f)).replace('/', '\\'))

for d in installed_dirs:
	pref = ""
	for i in d.split('/'):
		pref = i if not pref else "{0!s}/{1!s}".format(pref, i)
		remd.append( ('	RMDir "$INSTDIR/{0!s}"'.format(pref)).replace('/', '\\'))

if len(sys.argv) > 1:
	version = sys.argv[1]
else:
	version = raw_input('Version: ')

file('install.nsi', 'w').write(file('development/nsi.template', 'r').read() % (version, '\n'.join(remove_double(inst)), "0x%08X", '\n'.join(remove_double(remf)), '\n'.join(remove_double(sorted(list(set(remd)), lambda x,y: 1 if len(x) < len(y) else -1)))))
