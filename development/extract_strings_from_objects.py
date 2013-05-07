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

###############################################################################
#
# == I18N DEV USE CASES: CHEATSHEET ==
#
# ** Refer to  development/copy_pofiles.sh  for help with building or updating
#    the translation files for Unknown Horizons.
#
###############################################################################
#
# THIS SCRIPT IS A HELPER SCRIPT. DO NOT INVOKE MANUALLY!
#
###############################################################################


HEADER = '''\
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

###############################################################################
#
# == I18N DEV USE CASES: CHEATSHEET ==
#
# ** Refer to  development/copy_pofiles.sh  for help with building or updating
#    the translation files for Unknown Horizons.
#
###############################################################################
#
# WARNING: This file is generated automagically.
#          You need to update it to see changes to strings in-game.
#          DO NOT MANUALLY UPDATE THIS FILE (by editing strings).
#          The script to generate .pot templates calls the following:
# ./development/extract_strings_from_objects.py  horizons/i18n/objecttranslations.py
#
# NOTE: In string-freeze mode (shortly before releases, usually
#       announced in a meeting), updates to this file must not happen
#       without permission of the responsible translation admin!
#
###############################################################################

object_translations = {}

def set_translations():
	"""Instead of overwriting object_translations, operates on the same
	object (i.e. deleting dict keys, then updating) so that everything
	importing object_translations once keeps getting updates. #1905, #1909
	"""
	global object_translations
	object_translations.clear()
	object_translations.update({
'''

FOOTER = '''
	})
'''
ROWINDENT = '''
		'''

OBJECT_PATH = 'content/objects/'

locations_to_translate = [
	OBJECT_PATH + 'buildings/',
	OBJECT_PATH + 'units/ships/',
	OBJECT_PATH + 'gui_buildmenu/',
	]

files_to_skip = [
	'usablefisher.yaml',
	]

import os
import sys

from yaml import load
from yaml import SafeLoader as Loader

from horizons.constants import TIER, RES, UNITS, BUILDINGS

# cannot import parse_token from horizons.util.yamlcache here!
#TODO Make sure to keep both in sync and/or fix the import trouble!
def parse_token(token, token_klass):
	"""Helper function that tries to parse a constant name.
	Does not do error detection, but passes unparseable stuff through.
	Allowed values: integer or token_klass.LIKE_IN_CONSTANTS
	@param token_klass: "TIER", "RES", "UNITS" or "BUILDINGS"
	"""
	classes = {'TIER': TIER, 'RES': RES, 'UNITS': UNITS, 'BUILDINGS': BUILDINGS}

	if not isinstance(token, basestring):
		return token # probably numeric already
	if not token.startswith(token_klass):
		return token
	try:
		return getattr( classes[token_klass], token.split(".", 2)[1])
	except AttributeError as e: # token not defined here
		err = "This means that you either have to add an entry in horizons/constants.py "\
		      "in the class %s for %s,\nor %s is actually a typo." % (token_klass, token, token)
		raise Exception( str(e) + "\n\n" + err +"\n" )

def list_all_files():
	result = []
	for folder in locations_to_translate:
		for directory, subdirs, files in os.walk(folder):
			for filename in files:
				if filename.endswith('.yaml') and filename not in files_to_skip:
					result.append(os.path.join(directory, filename))
	return sorted(result)

def content_from_file(filename):
	parsed = load(file(filename, 'r'), Loader=Loader)
	object_strings = []
	if not parsed:
		return ''
	def add_line(value, component, sep, key, filename):
		if value.startswith('_ '):
			text = '_("{value}")'.format(value=value[2:])
			component = component + sep + str(parse_token(key, 'TIER'))
			filename = filename.rsplit('.yaml')[0].split(OBJECT_PATH)[1].replace('/',':')
			comment = '%s of %s' %(component, filename)
			object_strings.append('# %s' %comment + ROWINDENT + '%-30s: %s' % (('"%s"') % component, text))

	for component, value in parsed.iteritems():
		if isinstance(value, basestring):
			add_line(value, component, '', '', filename)
		elif isinstance(value, dict):
			for key, subvalue in value.iteritems():
				if isinstance(subvalue, basestring):
					add_line(subvalue, component, "_", str(key), filename)
		elif isinstance(value, list): # build menu definitions
			for attrlist in value:
				if isinstance(attrlist, dict):
					for key, subvalue in attrlist.iteritems():
						if isinstance(subvalue, basestring):
							add_line(subvalue, component, "_", str(key), filename)
				else:
					for subvalue in attrlist:
						if isinstance(subvalue, basestring):
							add_line(subvalue, 'headline', '', '', filename)

	strings = sorted(object_strings)

	if strings:
		return ('\n\t"%s" : {' % filename) + \
		       (ROWINDENT + '%s,' % (','+ROWINDENT).join(strings)) + ROWINDENT + '},'
	else:
		return ''

filesnippets = (content_from_file(filename) for filename in list_all_files())
filesnippets = (content for content in filesnippets if content != '')

output = '%s%s%s' % (HEADER, '\n'.join(filesnippets), FOOTER)

if len(sys.argv) > 1:
	file(sys.argv[1], 'w').write(output)
else:
	print output
