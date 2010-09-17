#!/bin/sh

# Extract strings from tutorial_en.yaml for easy translation in pootle.
#
# If a path is given, it's assumed to be the path to the translation files
# from pootle for the tutorial, and the .po files in there are used to
# generate translated tutorials in horizons/scenarios/.

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

def prep(x):
	return x.replace("\n", r'\n').replace('"', r'\"')
def write(x):
	print ('_("%s")' % x).encode('utf-8')

scenario = yaml.load(open('content/scenarios/tutorial_en.yaml', 'r'))
write(prep(scenario['difficulty']))
write(prep(scenario['author']))
write(prep(scenario['description']))

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
			write(argument)
END

xgettext --output-dir=po --output=tutorial.pot \
         --from-code=UTF-8 --add-comments --no-wrap --sort-by-file \
         --copyright-holder='The Unknown Horizons Team' \
         --msgid-bugs-address=team@unknown-horizons.org \
         po/tutorial_en.py
rm po/tutorial_en.py


if [ "x$1" = x ]; then
    exit
fi

# Create .mo files and extract the translations using gettext.
for path in "$1"/*.po; do
    lang=`basename "$path" | sed 's,tutorial-,,;s,.po,,'`
    mo=po/mo/$lang/LC_MESSAGES
    echo $lang:
    mkdir -p $mo && msgfmt --statistics $path -o $mo/tutorial.mo

    python << END > content/scenarios/tutorial_$lang.yaml
import yaml
import gettext

translation = gettext.translation('tutorial', 'po/mo', ['$lang'])
translation.install(unicode=True)

def translate(x):
	if isinstance(x, int) or not x:
		return x
	return _(x)

scenario = yaml.load(open('content/scenarios/tutorial_en.yaml', 'r'))

scenario['difficulty'] = _(scenario['difficulty'])
scenario['author'] = _(scenario['author'])
scenario['description'] = _(scenario['description'])

for i, event in enumerate(scenario['events']):
	for j, action in enumerate(event['actions']):
		if action['type'] not in ('message', 'logbook', 'logbook_w'):
			continue
		action['arguments'] = map(translate, action['arguments'])
		event['actions'][j] = action
	scenario['events'][i] = event

print """
# DON'T EDIT THIS FILE.

# It was automatically generated with development/create_scenario_pot.sh using
# translation files from pootle.
"""
print yaml.dump(scenario, line_break=u'\n')
END

done

rm -rf po/mo
