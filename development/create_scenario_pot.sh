#!/bin/sh

###############################################################################
#
# == I18N DEV USE CASES: CHEATSHEET ==
#
# ** Refer to  development/copy_pofiles.sh  for help with building or updating
#    the translation files for Unknown Horizons.
#
###############################################################################

# Extract strings from a scenario file for easy translation in pootle.
#
# Usage: sh create_scenario_pot.sh scenario [po-directory]
#
# If a path is given, it's assumed to be the path to the translation files
# from pootle for the scenario, and the .po files in there are used to
# generate translated scenarios in horizons/scenarios/.
#
# If you are looking for a way to compile the tutorial translations:
# The file development/copy_pofiles.sh does this (and a bit more). No need to
# call this script directly thus, unless you want to translate more scenarios.

# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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


if [ x$1 = x ]; then
    echo "No scenario file given!"
    exit 1
elif [ ! -f content/scenarios/$1_en.yaml ]; then
    echo "content/scenarios/$1_en.yaml doesn't exist!"
    exit 1
fi

VERSION=$(python2 -c 'from horizons.constants import VERSION
print "%s" % VERSION.RELEASE_VERSION')

python2 << END > po/$1.py
import yaml

COMMENT_MESSAGEWIDGET = 'This message is displayed in the widget on the left screen part. Please keep it short enough to fit there!'
COMMENT_HEADING       = 'This is a logbook page heading. Space is VERY short, please only translate to strings that fit (roughly 30 characters max).'
COMMENT_TEXT          = 'This is the text body of a logbook page.'

def prep(string):
	retval = string.replace("\n",    r'\n')
	retval = retval.replace('"',     r'\"')
	retval = retval.replace(' [br]', r'[br]')
	###############.replace('[br] ', r'[br]')
	return retval

def write(comment, string):
	retval = '#%s\n' % comment + '_("%s")' % (string)
	print retval.encode('utf-8')

scenario = yaml.load(open('content/scenarios/$1_en.yaml', 'r'))
write('scenario difficulty', prep(scenario['difficulty']))
write('scenario author', prep(scenario['author']))
write('scenario description', prep(scenario['description']))

for event in scenario['events']:
	for action in event['actions']:
		at = action['type']
		if at not in ('message', 'logbook'):
			continue
		elif at == 'logbook':
			for widget_def in action['arguments']:
				if not widget_def:
					continue
				if isinstance(widget_def, basestring):
					content = widget_def.rstrip('\n')
					# ignore strings that only consist of newlines
					if not content:
						continue
					comment = COMMENT_TEXT
					widget = prep(content)
				elif widget_def[0] == 'Label' and widget_def[1]:
					content = widget_def[1].rstrip('\n')
					# ignore strings that only consist of newlines
					if not content:
						continue
					comment = COMMENT_TEXT
					widget = prep(content)
				elif widget_def[0] == 'Headline':
					comment = COMMENT_HEADING
					widget = prep(widget_def[1].rstrip('\n'))
				elif widget_def[0] == 'Message' and widget_def[1]:
					content = widget_def[1].rstrip('\n')
					# ignore strings that only consist of newlines
					if not content:
						continue
					comment = COMMENT_MESSAGEWIDGET
					widget = prep(widget_def[1].rstrip('\n'))
				elif widget_def[0] in ('Image', 'Gallery', 'Pagebreak'):
					continue
				write(comment, widget)
END

xgettext --output-dir=po --output=$1.pot \
         --from-code=UTF-8 \
	    --add-comments \
	    --add-location \
         --width=80 \
	    --sort-by-file  \
         --copyright-holder='The Unknown Horizons Team' \
         --package-name='Unknown Horizons' \
         --package-version=$VERSION \
         --msgid-bugs-address=translate-uh@lists.unknown-horizons.org \
         po/$1.py
rm po/$1.py

# some strings contain two entries per line => remove line numbers from both
perl -pi -e 's,(#: .*):[0-9][0-9]*,\1,g' po/$1.pot
perl -pi -e 's,(#: .*):[0-9][0-9]*,\1,g' po/$1.pot


diff=$(git diff --numstat po/$1.pot |awk '{print $1;}')
if [ $diff -le 2 ]; then      # only changed version and date (two lines)
    git checkout -- po/$1.pot # => discard this template change
fi

if [ "x$2" = x ]; then
    exit
fi

# Create .mo files and extract the translations using gettext.
echo "   Compiling these translations for $1:"
for file in $(ls $2); do
    path=$(pwd)/$2/$file
    lang=`basename "$path" | sed "s,$1-,,;s,.po,,"`
    mo=po/mo/$lang/LC_MESSAGES
    R='s,:,,g;s,.po,,g;s,alencia,,g;s,(/.*//|messages|message|translations),\t,g;s/[.,]//g'
    mkdir -p $mo
    msgfmt --statistics $path -o $mo/$1.mo --check-format -v 2>&1 |perl -npe "$R"
    numbers=$(msgfmt --statistics $path -o $mo/$1.mo --check-format 2>&1) # this does not include -v!

    python2 << END > content/scenarios/$1_$lang.yaml
import yaml
import gettext

translation = gettext.translation('$1', 'po/mo', ['$lang'])
translation.install(unicode=True)

def unprep(trans):
	return trans.replace(' [br]', '[br]')
	#########trans = trans.replace('[br] ', '[br]')

def translate(arg):
	if isinstance(arg, int) or not arg:
		return arg
	return (_(unprep(arg))).replace('[br] ', '[br]')

scenario = yaml.load(open('content/scenarios/$1_en.yaml', 'r'))

scenario['difficulty'] = _(scenario['difficulty'])
scenario['author'] = _(scenario['author'])
scenario['description'] = _(scenario['description'])
scenario['locale'] = '$lang'
scenario['translation_status'] = '$numbers'

for i, event in enumerate(scenario['events']):
	for j, action in enumerate(event['actions']):
		if action['type'] not in ('message', 'logbook'):
			continue
		elif action['type'] == 'message':
			action['arguments'] = map(translate, action['arguments'])
		elif action['type'] == 'logbook':
			old_args = action['arguments']
			action['arguments'] = []
			for widget in old_args:
				if isinstance(widget, basestring):
					action['arguments'].append(translate(widget.rstrip('\n')))
				elif widget[0] in ('Label', 'Headline'):
					text = translate(widget[1].rstrip('\n'))
					action['arguments'].append([widget[0], text])
				else:
					action['arguments'].append(widget) # no translation for everything else
		event['actions'][j] = action
	scenario['events'][i] = event

print """
# DON'T EDIT THIS FILE.

# It was automatically generated with development/create_scenario_pot.sh using
# translation files from pootle. Documentation on this process is found here:
#   development/copy_pofiles.sh
"""
print yaml.dump(scenario, line_break=u'\n')
END

done

rm -rf po/mo
