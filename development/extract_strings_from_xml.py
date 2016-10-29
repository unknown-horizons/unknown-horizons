#!/usr/bin/env python2
# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
# ** Refer to  development/create_pot.sh  for help with building or updating
#    the translation files for Unknown Horizons.
#
###############################################################################
#
# THIS SCRIPT IS A HELPER SCRIPT. DO NOT INVOKE MANUALLY!
#
###############################################################################

from __future__ import print_function
import os
import sys
from xml.dom import minidom


if len(sys.argv) != 2:
	print('Error: Provide a file to write strings to as argument. Exiting.')
	sys.exit(1)

header = u'''\
# Encoding: utf-8
# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
# ** Refer to  development/create_pot.sh  for help with building or updating
#    the translation files for Unknown Horizons.
#
###############################################################################
#
# WARNING: This file is generated automagically.
#          You need to update it to see changes to strings in-game.
#          DO NOT MANUALLY UPDATE THIS FILE (by editing strings).
#          The script to generate .pot templates calls the following:
# ./development/extract_strings_from_xml.py  horizons/gui/translations.py
#
# NOTE: In string-freeze mode (shortly before releases, usually
#       announced in a meeting), updates to this file must not happen
#       without permission of the responsible translation admin!
#
###############################################################################

from horizons.constants import VERSION
from horizons.ext.typing import Tuple
from horizons.i18n import gettext as _

text_translations = {} # type: Dict[str, Dict[Tuple[str, str], str]]

def set_translations():
	global text_translations
	text_translations = {
'''

FOOTER = u'''
	}
'''

FILE = u'''
	{filename!r} : {{
{entries}		}},
'''

ENTRY = u'''\
		({widget!r:<32}, {attribute!r:<10}): {text},
'''

files_to_skip = [
	'credits.xml',
	'stringpreviewwidget.xml',
	'startup_error_popup.xml',
]


def print_n_no_name(n, text):
	print('\tWarning: ', end=' ')
	print('%s without name. Add unique name if desired: text="%s"' % (n, text))

def list_all_files():
	result = []
	walker = os.walk('content/gui/xml')
	for root, dirs, files in walker:
		for filename in files:
			if filename.endswith('.xml'):
				result.append(('%s/%s' % (root, filename), filename not in files_to_skip))
	return sorted(result)

def content_from_element(element_name, parse_tree, attribute):
	"""Extracts text content of one attribute from a widget in the DOM.

	element_name: name of widget
	parse_tree: xml tree to parse
	attribute: usually 'text' or 'helptext'
	"""
	default_names = {
		'OkButton': u'okButton',
		'CancelButton': u'cancelButton',
		'DeleteButton': u'deleteButton',
	}
	element_strings = []
	element_list = parse_tree.getElementsByTagName(element_name)

	for element in element_list:
		name = element.getAttribute('name')
		text = element.getAttribute(attribute)
		i18n = element.getAttribute('comment') # translator comment about widget context
		if i18n == 'noi18n':
			# comment='noi18n' in widgets where translation is not desired
			continue

		if i18n == 'noi18n_%s' % attribute:
			# comment='noi18n_tooltip' in widgets where tooltip translation is not
			# desired, but text should be translated.
			continue

		if not name:
			if element_name in default_names:
				name = default_names[element_name]
			elif text:
				print_n_no_name(element_name, text)

		if text and name:
			if name == 'version_label':
				text = 'VERSION.string()'
			else:
				text = '_(u"%s")' % text
			newline = ENTRY.format(attribute=attribute, widget=name, text=text)
			element_strings.append(newline)

	return ''.join(sorted(element_strings))

def content_from_file(filename, parse=True):
	"""Set parse=False if you want to list the widget in guitranslations,
	but not the strings. Usually because those strings are not reasonable
	to translate (credits, development widgets).
	"""
	def empty():
		return FILE.format(filename=printname, entries='')

	parsed = minidom.parse(filename)

	#HACK! we strip the string until no "/" occurs and then use the remaining part
	# this is necessary because of our dynamic widget loading (by unique file names)
	printname = filename.rsplit("/", 1)[1]
	if not parse:
		return empty()

	strings = ''
	for w in ['Button', 'CheckBox', 'Label', 'RadioButton']:
		strings += content_from_element(w, parsed, 'text')
	for w in ['CancelButton', 'DeleteButton', 'OkButton', 'Button', 'Icon', 'ImageButton', 'Label', 'ProgressBar']:
		strings += content_from_element(w, parsed, 'helptext')

	if not strings:
		return empty()

	return FILE.format(filename=printname, entries=strings)

filesnippets = (content_from_file(filename, parse) for (filename, parse) in list_all_files())
filesnippets = ''.join(content for content in filesnippets if content)

output = '%s%s%s' % (header, filesnippets, FOOTER)

file(sys.argv[1], 'w').write(output.encode('utf-8'))
