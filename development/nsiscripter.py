#!/usr/bin/python

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
	if '.svn' in dirs:
		dirs.remove('.svn')
	if 'development' in dirs:
		dirs.remove('development')
	if '.git' in dirs:
		dirs.remove('.git')
	if 'screenshots' in dirs:
		dirs.remove('screenshots')
	if root[-4:] == 'fife' and len(root.split('\\')) == 2:
		for d in dirs[:]:
			if d not in ('engine', 'tools'):
				dirs.remove(d)
	if '.gitignore' in files:
		files.remove('.gitignore')
	if 'Thumbs.db' in files:
		files.remove('Thumbs.db')

	if not len(files) == 0:
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
			files = filter(lambda s: s.split('.')[-1] not in ('pyc',), files)
		inst.append( ('  SetOutPath "$INSTDIR/%s"' % rootp).replace('/', '\\'))
		installed_dirs.append(rootp)
		for j in files:
			inst.append( ('  File "./%s/%s"' % (rootp, j)).replace('/', '\\'))
			installed_files.append('%s/%s' % (rootp, j))
			if j[-3:] == '.py':
				installed_files.append('%s.pyc' % ('%s/%s' % (rootp, j))[:-3])

for f in installed_files:
	remf.append( ('  Delete "$INSTDIR/%s"' % f).replace('/', '\\'))

for d in installed_dirs:
	pref = ""
	for i in d.split('/'):
		pref = i if len(pref) == 0 else "%s/%s" % (pref, i)
		remd.append( ('  RMDir "$INSTDIR/%s"' % pref).replace('/', '\\'))

if len(sys.argv) > 1:
	version = sys.argv[1]
else:
	version = raw_input('Version: ')

file('install.nsi', 'w').write(file('development/nsi.template', 'r').read() % (version, '\n'.join(remove_double(inst)), '\n'.join(remove_double(remf)), '\n'.join(remove_double(sorted(list(set(remd)), lambda x,y: 1 if len(x) < len(y) else -1)))))
