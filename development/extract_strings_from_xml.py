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

# ###################################################
# WARNING: This file is generated automagically. If
#          you need to update it follow the procedure
#          outlined below.
#
# * Generate a bare version using
#     python development/extract_strings_from_xml.py \\
#       horizons/i18n/guitranslations.py
# * Do the manual postprocessing needed, a diff between
#   the versions help figuring out what is needed.
# ###################################################

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
	}

import glob
import xml.dom.minidom
import os
import sys

def print_n_no_name(n, text):
	print '\tWarning: ',
	print '%s without name found, please consider adding an unique name, text=("%s")' % (n, text)

print_label_no_name = lambda x: print_n_no_name('Label', x)
print_window_no_name = lambda x: print_n_no_name('Window', x)

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
	            'DeleteButton' : 'deleteButton'}

	element_list = parse_tree.getElementsByTagName(element_name)
	for element in element_list:
		if not len(element.getAttribute('name')):
			if defaults.has_key(element_name):
				_set_default_name(element, defaults[element_name])
			else:
				print_n_no_name(element_name, element.getAttribute(text_name))

	element_strings = []
	for element in element_list:
		if len(element.getAttribute(text_name)) and len(element.getAttribute('name')):
			name = element.getAttribute('name')
			value = element.getAttribute(text_name)
			if name == 'version_label':
				value = 'VERSION.string()'
			else:
				value = '_("%s")' % value
			element_strings.append('%s: %s' % (('"%s"' % name).ljust(30), value))

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
		content_from_element('TooltipLabel', parsed, 'tooltip') + \
		content_from_element('TooltipProgressBar', parsed, 'tooltip') + \
		content_from_element('ToggleImageButton', parsed, 'tooltip')

	if len(strings):
		printname = filename.rsplit("/",1)[1]
		#HACK! we strip the string until no "/" occurs and then use the remaining part
		# this is necessary because of our dynamic widget loading (by unique file names)
		return '\t\t"%s" : {\n\t\t\t%s},' % (printname, ',\n\t\t\t'.join(strings))
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
