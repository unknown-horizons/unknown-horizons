#!/usr/bin/env python2
# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from collections import OrderedDict


sections = ['UH-Team_New', 'UH-Team_Old', 'Patchers', 'Translators', 'Packagers', 'Special Thanks']
section_widgets = {s: 'credits_' + s.lower() for s in sections}
section_widgets.update({'UH-Team-2016/2017': 'credits_team_2016','UH-Team-2015': 'credits_team_2015', 'Special Thanks': 'credits_thanks'})

# Whether to add ScrollAreas around the page
huge_pages = ['UH-Team-2016/2017', 'UH-Team-2015', 'Patchers', 'Translators']

INPUT = 'doc/AUTHORS.md'
OUTPUT = 'content/gui/xml/mainmenu/credits.xml'

HEADER = ur'''<?xml version="1.0"?>

<!--  /!\ WARNING /!\
This document was auto-generated from %s.
Please edit %s instead if you need to change something,
afterwards run %s to refresh this file.
-->

<Container name="credits_window" size="1000,580">
	<Icon image="content/gui/images/background/book.png" position="100,0" />
	<Container name="left_pickbelts" size="170,580" position="30,0" />''' % (INPUT, INPUT, __file__)
FOOTER = ur'''
<OkButton position="800,500" helptext="Exit to main menu" />

<Container name="right_pickbelts" position="835,0" size="170,580" />

</Container>'''

XML_MESS = [  # (search, replace) list of stuff we need to replace before writing xml manually
	('&', '&amp;'),
]

def write(f, level, text, newline=True):
	wtext = u'\n' * newline + u'\t' * level + text
	for search, replace in XML_MESS:
		wtext = wtext.replace(search, replace)
	f.write(wtext.encode('utf8'))

def close_box(box, level):
	write(f, level, u'</%sBox>' % box)
def close_vbox(level):
	close_box('V', level)
def close_hbox(level):
	close_box('H', level)


class PageBreak(Exception):
	"""Used to wrap content onto two-page logbook layout."""


def parse_markdown(infile):
	"""Parses very simple markdown files (#headings and *lists).

	No support for line breaks."""
	tree = OrderedDict()
	headings = [(0, tree)]

	with open(infile) as f:
		for line in f:
			line = line.strip()
			if line.startswith('#'):
				parts = line.split(' ')
				heading_level = parts[0].count('##')
				while heading_level <= headings[-1][0]:
					headings.pop()

				parts = parts[1:]
				if set(parts[-1]) == set('#'):
					parts = parts[:-1]
				text = ' '.join(parts)
				dct = OrderedDict()
				headings[-1][1][text] = dct
				headings.append((heading_level, dct))
			elif line.startswith('*') or line.startswith('- -'):
				if 'items' not in headings[-1][1]:
					headings[-1][1]['items'] = []

				heading = line[1:].lstrip()
				headings[-1][1]['items'].append(heading)
			elif not line:
				pass
			else:
				raise Exception('Unexpected line: ' + line)
	return headings[0][1]


def write_page(heading, content):
	def write_page_header():
		if heading in huge_pages:
			write(f, 1, u'<ScrollArea name="%s" '
					  u'max_size="310,500" min_size="310,500">' % heading.lower())
			# Make sure there is no max_size set in this case!
			write(f, 1, u'<VBox min_size="310,500">')
		else:
			write(f, 1, u'<VBox max_size="310,500" min_size="310,500">')

	def write_page_footer():
		close_vbox(1)
		if heading in huge_pages:
			write(f, 1, u'</ScrollArea>')

	write(f, 0, u'\n<HBox name="%s" position="185,45">' % section_widgets[heading])

	write_page_header()

	write(f, 2, u'<Label text="%s" name="headline" />' % heading)
	write(f, 2, u'<hr />')

	for h3, lines in content.items():
		try:
			write_subsection(h3, lines)
		except PageBreak:
			# On to the right part of this page, add second VBox to HBox
			write_page_footer()
			write_page_header()

	write_page_footer()
	close_hbox(0)


def write_subsection(subheading, subcontent):
	write(f, 2, u'<VBox> <Label text="%s" name="headline" />' % subheading)
	write(f, 3, u'<VBox name="box">')
	for line in subcontent['items']:  # finally, names
		if set(line) == set('- '):
			close_vbox(3)
			close_vbox(2)
			raise PageBreak
		else:
			write(f, 4, u'<Label text="%s" />' % unicode(line, 'utf-8'))
	close_vbox(3)
	close_vbox(2)


credits = parse_markdown(INPUT)

# Now manually write pychan-suited xml file

with open(OUTPUT, 'w') as f:
	write(f, 0, HEADER, newline=False)
	for h1, dct in credits.items():  # credits pages (pickbelts)
		write_page(h1, dct)
	write(f, 0, FOOTER)
