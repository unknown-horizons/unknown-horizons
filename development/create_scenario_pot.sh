#!/bin/sh

# Extract strings from tutorial_en.yaml for easy translation in pootle.

# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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


python << END > po/tutorial_en.py
import yaml

scenario = yaml.load(open('content/scenarios/tutorial_en.yaml', 'r'))
for event in scenario['events']:
	for action in event['actions']:
		if action['type'] not in ('message', 'logbook', 'logbook_w'):
			continue
		for argument in action['arguments']:
			if isinstance(argument, int):
				continue
			argument = argument.replace("\n", r'\n').replace('"', r'\"')
			if not argument:
				continue
			print ('_("%s")' % argument).encode('utf-8')
END

xgettext --output-dir=po --output=tutorial.pot \
         --from-code=UTF-8 --add-comments --no-wrap --sort-by-file \
         --copyright-holder='The Unknown Horizons Team' \
         --msgid-bugs-address=team@unknown-horizons.org \
         po/tutorial_en.py
rm po/tutorial_en.py
