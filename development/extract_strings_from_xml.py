#!/usr/bin/python
# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
# Copyright (C) 2009 The Unknown Horizons Team
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
# WARNING: This fiile is generated automagically. If
#          you need to update it follow the procedure
#          outlined below.
#
# * Generate a bare version using
#     python development/extract_strings_from_xml.py \\
#       horizons/i18n/guitranslations.py
# * Do the manual postprocessing needed, a diff between
#   the versions help figuring out what is needed.
#   Currently you want to replace the Version strings by
#   the magic from horizons/constants.py
# ###################################################

text_translations = dict()

def set_translations():
\tglobal text_translations
\ttext_translations = {
'''

footer = '''\n\t}\n'''

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
    walker = os.walk('content/gui')
    for entry in walker:
        for filename in entry[2]:
            if filename.endswith('.xml'):
               result.append('%s/%s' % (entry[0], filename))
    return result

def content_from_element(element_name, parse_tree, text_name='text'):
    element_list = parse_tree.getElementsByTagName(element_name)
    for element in element_list:
        if not len(element.getAttribute('name')):
            print_n_no_name(element_name, element.getAttribute(text_name))

    element_strings = [ '%s: _("%s")' % (
            ('"%s"' % element.getAttribute('name')).ljust(30),
            element.getAttribute(text_name)) for element in element_list
                      if len(element.getAttribute(text_name)) and len(element.getAttribute('name'))
                      ]
    return element_strings

def content_from_file(filename):
    print '@ %s' % filename
    parsed = xml.dom.minidom.parse(filename)

    strings = content_from_element('Label', parsed) + \
        content_from_element('Button', parsed) + \
        content_from_element('CheckBox', parsed) + \
        content_from_element('Window', parsed, 'title') + \
        content_from_element('TooltipButton', parsed, 'tooltip')


    if len(strings):
        return '\t\t"%s" : {\n\t\t\t%s},' % (filename[12:], ',\n\t\t\t'.join(strings))
    else:
        return ''

xmlfiles = list_all_files()

filesnipets = [ content_from_file(filename) for filename in xmlfiles ]

while True:
    try:
        filesnipets.remove('')
    except ValueError:
        break

if len(sys.argv) > 1:
    file(sys.argv[1], 'w').write('%s%s%s' % ( header, '\n'.join(filesnipets), footer ))
else:
    print
    print 'Copy ==========>'
    print '%s%s%s' % ( header, '\n'.join(filesnipets), footer )
    print '<=========='
