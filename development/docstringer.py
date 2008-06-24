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
	for line in file:
		linenr += 1
		empty = is_empty.match(line)
		if empty != None:
			continue
		decorator = is_decorator.match(line)
		if decorator != None:
			decorators.append(decorator.group(2))
			continue
		func = is_function.match(line)
		if func != None:
			params = func_param.findall(func.group(3))
			the_function = {'file' : filename, 'line' : linenr, 'depth' : len(empty.group(1).expandtabls()), 'name' : func.group(2), 'decorators' : decorators, 'params' : params}
			decorators = []
			continue

#print filepart + ' ' + func.group(2) + ':'
#print decorators
#filepart = "%s:%d" % (filename, linenr)
#filepart += ' ' * (40 - len(filepart))
