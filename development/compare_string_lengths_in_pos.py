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
import sys

usage = "<filename> [lower_bound] [upper_bound]"
usage = "<filename>"

if len(sys.argv) < 2:
	print(usage)
	sys.exit(1)

filename = sys.argv[1]

readfile = open(filename, "r")

i = 0
translations = {}

state = 0

for line in readfile:
	line = line.strip()

	if state == 0:
		if "msgid" not in line:
			continue
		translations[i] = {}
		translations[i][0] = line
		state += 1

	elif state == 1:
		if "msgstr" in line:
			translations[i][1] = line
			state += 1
		else:
			translations[i][0] += line

	elif state == 2:
		if line.startswith("#") or not line:
			state = 0
			i += 1
		else:
			translations[i][1] += line


for t in translations:
	orig = translations[t][0]
	trans = translations[t][1]

	if orig.startswith("#") or trans.startswith("#"):
		continue

	if orig.startswith("msgid"):
		orig = orig[6:]
	if trans.startswith("msgstr"):
		trans = trans[7:]

	if trans == "\"\"":
		continue

	len_ratio = float(len(orig)) / len(trans)

	if len_ratio > 1.4 or len_ratio < 0.6 and \
			abs(len(orig) - len(trans)) > 2:
		print('string length ratio:', len_ratio)
		print(orig)
		print(trans)
		print()
