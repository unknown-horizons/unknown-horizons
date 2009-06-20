#!/usr/bin/python

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

text_translations = dict()

def set_translations():
\tglobal text_translations
\ttext_translations = {
'''

footer = '''\n\t}'''

import glob
import xml.dom.minidom
import os
import sys

def print_no_name(text):
    print '\tWarning: ',
    print 'Label without name found, please consider adding an uniq name, text=("%s")' % text

def list_all_files():
    result = []
    walker = os.walk('content/gui')
    for entry in walker:
        for filename in entry[2]:
            if filename.endswith('.xml'):
               result.append('%s/%s' % (entry[0], filename))
    return result

def content_from_file(filename):
    print '@ %s' % filename
    parsed = xml.dom.minidom.parse(filename)
    labels = parsed.getElementsByTagName('Label')
    for label in labels:
        if not len(label.getAttribute('text')):
            labels.remove(label)
        elif not len(label.getAttribute('name')):
            print_no_name(label.getAttribute('text'))
    label_strings = [ '%s: _("%s")' % (
            ('"%s"' % label.getAttribute('name')).ljust(30),
            label.getAttribute('text')) for label in labels if len(label.getAttribute('text')) and len(label.getAttribute('name'))
                      ]
    if len(label_strings):
        return '\t\t%s : {\n\t\t\t%s},' % (os.path.basename(filename), ',\n\t\t\t'.join(label_strings))
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
