#!/usr/bin/env python
# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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


header = '''# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

# ###################################################################
# WARNING: This file is generated automagically.
#          You need to update it to see changes to strings in-game.
#          DO NOT MANUALLY UPDATE THIS FILE (by editing strings).
#          The script to generate .pot templates calls the following:
# ./development/extract_strings_from_xml.py  horizons/i18n/guitranslations.py
#          If you changed strings in code, you might just run this
#          command as well.
# NOTE: In string-freeze mode (shortly before releases, usually
#       announced in a meeting), updates to this file must not happen
#       without permission of the responsible translation admin!
# ###################################################################

from horizons.constants import VERSION

text_translations = dict()

def set_translations():
\tglobal text_translations
\ttext_translations = {
'''

footer = '''\n\t}\n'''

files_to_skip = {
	'call_for_support.xml',
	'credits0.xml',
	'credits1.xml',
	'credits2.xml',
	'credits3.xml',
	'startup_error_popup.xml'
	}

import glob
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

def content_from_element(element_name, parse_tree, text_name='text'):

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

		if len(element.getAttribute(text_name)) and len(element.getAttribute('name')):
			name = element.getAttribute('name')
			text = element.getAttribute(text_name)
			if name[0:6] == 'noi18n': #prepend 'noi18n' to labels without translation
				break
			if name == 'version_label':
				text = 'VERSION.string()'
			else:
				text = '_("%s")' % text
			element_strings.append('%-30s: (%-10s, %s)' % (('"%s"' % name), ('"%s"') % text_name, text))

	return sorted(element_strings)

def content_from_file(filename):
	print '@ %s' % filename
	parsed = xml.dom.minidom.parse(filename)

	strings = content_from_element('Label', parsed) + \
		content_from_element('Button', parsed) + \
		content_from_element('CheckBox', parsed) + \
		content_from_element('RadioButton', parsed) + \
		content_from_element('Window', parsed, 'title') + \
		content_from_element('OkButton', parsed, 'tooltip') + \
		content_from_element('CancelButton', parsed, 'tooltip') + \
		content_from_element('DeleteButton', parsed, 'tooltip') + \
		content_from_element('TooltipButton', parsed, 'tooltip') + \
		content_from_element('TooltipIcon', parsed, 'tooltip') + \
		content_from_element('TooltipLabel', parsed, 'text') + \
		content_from_element('TooltipLabel', parsed, 'tooltip') + \
		content_from_element('TooltipProgressBar', parsed, 'tooltip') + \
		content_from_element('ToggleImageButton', parsed, 'tooltip')

	if len(strings):
		printname = filename.rsplit("/",1)[1]
		#HACK! we strip the string until no "/" occurs and then use the remaining part
		# this is necessary because of our dynamic widget loading (by unique file names)
		return '\t"%s" : {\n\t\t\t%s,\n\t\t\t},' % (printname, ',\n\t\t\t'.join(strings))
	else:
		return ''

filesnippets = (content_from_file(filename) for filename in list_all_files())
filesnippets = (content for content in filesnippets if content != '')

output = '%s%s%s' % (header, '\n'.join(filesnippets), footer)

if len(sys.argv) > 1:
	file(sys.argv[1], 'w').write(output)
else:
	print
	print 'Copy ==========>'
	print output
	print '<=========='
