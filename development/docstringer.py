#!/usr/bin/env python3

# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import re
import sys

is_function = re.compile(r'^(\s*)def ([^(]+)[(](.*)[)]:\s*$')
is_decorator = re.compile(r'^(\s*)@\s*(.+)\s*$')
func_param = re.compile(r'\s*(?:,\s*)?([^,=\s]+)(?:\s*=\s*([^\s,]+))?')
is_empty = re.compile(r'^(\s*)(?:#.*)?$')

files = sys.argv[1:]
for filename in files:
	print('Adding documentation stubs to:', filename)
	file = open(filename, 'r+')
	funk_reg = None
	newfile = []
	for line in file:
		if is_function.match(line) is not None:
			funk_reg = is_function.match(line)
		elif funk_reg is not None and line.strip().startswith('"""'):
			newfile.append(funk_reg.group())
			newfile.append(line)
			funk_reg = None
		elif funk_reg is not None:
			params = func_param.findall(funk_reg.group(3))
			indent = funk_reg.group(1) + '\t' * (funk_reg.group(2) != '__init__')
			docstub = [(indent + '"""\n')]
			for i in params:
				if i[0] != 'self' and i[0] != 'cls':
					docstub.append(("{}@param {}:\n".format(indent, i[0])))
			docstub.append((indent + '"""\n'))
			if funk_reg.group(2) == '__init__':
				newfile.extend(docstub)
				newfile.append(funk_reg.group())
			else:
				newfile.append(funk_reg.group())
				newfile.extend(docstub)
			newfile.append(line)
			funk_reg = None
		else:
			newfile.append(line)
	file.seek(0)
	file.writelines(newfile)
	file.close()
	print('Done')
