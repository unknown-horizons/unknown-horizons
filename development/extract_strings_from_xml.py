#!/usr/bin/env python
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


header = '''# ###################################################
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
# ./development/extract_strings_from_xml.py  horizons/i18n/guitranslations.py
#
# NOTE: In string-freeze mode (shortly before releases, usually
#       announced in a meeting), updates to this file must not happen
#       without permission of the responsible translation admin!
#
###############################################################################

from horizons.constants import VERSION

text_translations = dict()

def set_translations():
\tglobal text_translations
\ttext_translations = {
'''

FOOTER = '''\n\t}\n'''
ROWINDENT = '\n\t\t'

files_to_skip = [
	'call_for_support.xml',
	'credits0.xml',
	'credits1.xml',
	'credits2.xml',
	'credits3.xml',
	'credits4.xml',
	'stringpreviewwidget.xml',
	'startup_error_popup.xml'
	]

import xml.dom.minidom
import os
import sys

def print_n_no_name(n, text):
	print '\tWarning: ',
	print '%s without name. Add unique name if desired: text="%s"' % (n, text)

def list_all_files():
	result = []
	walker = os.walk('content/gui/xml')
	for entry in walker:
		for filename in entry[2]:
			if filename.endswith('.xml') and filename not in files_to_skip:
				result.append('%s/%s' % (entry[0], filename))
	return sorted(result)

def content_from_element(element_name, parse_tree, text_name):

	def _set_default_name(element, default_name):
		element.setAttribute('name', default_name)

	defaults = {'OkButton' : 'okButton',
	            'CancelButton' : 'cancelButton',
	            'DeleteButton' : 'deleteButton',
	           }
	element_strings = []
	element_list = parse_tree.getElementsByTagName(element_name)

	for element in element_list:
		if not len(element.getAttribute('name')):
			if defaults.has_key(element_name):
				_set_default_name(element, defaults[element_name])
			else:
				print_n_no_name(element_name, element.getAttribute(text_name))

		name = element.getAttribute('name')
		text = element.getAttribute(text_name)
		i18n = element.getAttribute('comment') # translator comment about widget context
		if len(text) and len(name) and i18n != 'noi18n':
			#comment='noi18n' in widgets where translation is not desired
			if name == 'version_label':
				text = 'VERSION.string()'
			else:
				text = '_("%s")' % text
			comment = '(%s of widget: %s)' % (text_name, name) + (' %s' % (i18n) if i18n else '')
			element_strings.append('# %s' %comment + ROWINDENT + '(%-30s, %-10s): %s' % (('"%s"' % name), ('"%s"') % text_name, text))

	return sorted(element_strings)

def content_from_file(filename):
	print '@ %s' % filename
	parsed = xml.dom.minidom.parse(filename)

	strings = \
		content_from_element('Button', parsed, 'text') + \
		content_from_element('CheckBox', parsed, 'text') + \
		content_from_element('Label', parsed, 'text') + \
		content_from_element('RadioButton', parsed, 'text') + \
\
		content_from_element('CancelButton', parsed, 'helptext') + \
		content_from_element('DeleteButton', parsed, 'helptext') + \
		content_from_element('OkButton', parsed, 'helptext') + \
\
		content_from_element('Button', parsed, 'helptext') + \
		content_from_element('Icon', parsed, 'helptext') + \
		content_from_element('Label', parsed, 'helptext') + \
		content_from_element('ProgressBar', parsed, 'helptext') + \
		content_from_element('ToggleImageButton', parsed, 'helptext')

	if len(strings):
		printname = filename.rsplit("/",1)[1]
		#HACK! we strip the string until no "/" occurs and then use the remaining part
		# this is necessary because of our dynamic widget loading (by unique file names)
		return ('\n\t"%s" : {' % printname) + (ROWINDENT + '%s,' % (','+ROWINDENT).join(strings)) + ROWINDENT + '},'
	else:
		return ''

filesnippets = (content_from_file(filename) for filename in list_all_files())
filesnippets = (content for content in filesnippets if content != '')

output = '%s%s%s' % (header, '\n'.join(filesnippets), FOOTER)

if len(sys.argv) > 1:
	file(sys.argv[1], 'w').write(output)
else:
	print
	print 'Copy ==========>'
	print output
	print '<=========='
