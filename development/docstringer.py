#!/usr/bin/env python

# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import re
is_function = re.compile('^(\\s*)def\\s+([^\\s(]+)\\s*[(](.*)[)]\\s*:\\s*$')
is_decorator = re.compile('^(\\s*)@\\s*(.+)\\s*$')
func_param = re.compile('\\s*(?:,\\s*)?([^,=\\s]+)(?:\\s*=\\s*([^\\s,]+))?')
is_empty = re.compile('^(\\s*)(?:#.*)?$')
import sys
files = sys.argv[1:]
for filename in files:
	file = open(filename, 'rw')
	linenr = 0
	decorators = []
	funk = None
	newfile = []
	for line in file:
		linenr += 1
		empty = is_empty.match(line)
		if empty != None:
			continue
		if line.strip().startswith('def'):
			funk = line
			newfile.append(funk)
		elif funk is not None and line.strip().startswith('"""'):
			newfile.append(line)
			funk = None
		elif funk is not None:
			list = funk[funk.find('(')+1:funk.rfind(')')].split(',')
			indent = funk[0:funk.find('def')]*2
			docstub = [(indent + '"""')]
			tab = '	'
			for i in list:
				if i != 'self':
					docstub.append(("%s@param %s:\n" % (indent, i)))
			docstub.append((indent + '"""'))
			newfile.extend(docstub)
			newfile.append(line)
			funk = None
		else:
			newfile.append(line)

	for line in newfile:
		print line
	print file
	file.writelines(newfile)
	file.close()

#print filepart + ' ' + func.group(2) + ':'
#print decorators
#filepart = "%s:%d" % (filename, linenr)
#filepart += ' ' * (40 - len(filepart))
