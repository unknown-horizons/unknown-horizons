#!/usr/bin/env python2
# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

import pstats
import sys


if not sys.argv:
	print 'profile_output.py file [ sortstats [ ( callees | callers ) ] ]'
	sys.exit(1)

p = pstats.Stats(sys.argv[1])

p.strip_dirs()

arg2 = None if len(sys.argv) < 3 else sys.argv[2]

p.sort_stats(-1 if arg2 is None else arg2)

if not len(sys.argv) > 3:
	p.print_stats()
elif sys.argv[3] == 'callees':
	p.print_callees()
elif sys.argv[3] == 'callers':
	p.print_callers()
else:
	print 'invalid arg'

