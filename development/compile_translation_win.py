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

from __future__ import print_function
import os
import glob

if os.path.basename(os.getcwd()) != 'development':
	print('Please run the script from the "development" directory!')
	quit()

if not os.path.isdir('../po/uh/'):
	print('The translations directory does not exist! Quiting..')
	quit()

os.chdir('..')
files = glob.glob('po/uh/*.po')
for x in files:
	file = x.rpartition("\\")[2]
	dir = file[:-len('.po')]
	dir = os.path.join('content', 'lang', dir, 'LC_MESSAGES', '')
	if not os.path.isdir(dir):
		os.makedirs(dir)
	print('Generating translations for', file)
	command = 'msgfmt ' + x + ' -o ' + dir + 'unknown-horizons.mo'
	os.system(command)

print('\n== Completed generating translations ==\n')
