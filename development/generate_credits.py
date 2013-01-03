#!/usr/bin/env python2
# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

from collections import defaultdict

try:
	from markdown import markdown
except ImportError:
	print 'You need the python module "markdown" to run this script.\n'
	raise
try:
	from bs4 import BeautifulSoup
except ImportError:
	print 'You need the python module "BeautifulSoup" to run this script.\n'
	raise

from horizons.constants import LANGUAGENAMES


sections = ['UH-Team', 'Patchers', 'Translators', 'Packagers', 'Special Thanks']
section_widgets = {s: 'credits_' + s.lower() for s in sections}
section_widgets.update({'UH-Team': 'credits_team', 'Special Thanks': 'credits_thanks'})
sections += ['Project Coordination', 'Programming',
             'Game-Play Design', 'Sound and Music Artists', 'Graphics Artists',
]
# Whether to add ScrollAreas around the page
huge_pages = ['Translators']
# Whether to reduce the section margins
wide_pages = ['Special Thanks']

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

def creditsort(item):
	if item[0] in sections:
		return sections.index(item[0])
	return item[0]
def languagesort(item):
	return LANGUAGENAMES.get_by_value(item[0], english=True)
def namesort(item, attr='string'):
	return getattr(item, attr).lower()
def h3sort(item):
	return (languagesort(item), creditsort(item), item[0].lower())

def write(f, level, text, newline=True):
	wtext = u'\n' * newline + u'\t' * level + text
	f.write(wtext.encode('utf8'))

def close_box(box, level):
	write(f, level, u'</%sBox>' % box)
def close_vbox(level):
	close_box('V', level)
def close_hbox(level):
	close_box('H', level)


# This looks great, right? See below for what is stored here and how.
credits = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

with open(INPUT) as authors:
	# markdown to html
	html = markdown(authors.read().decode('utf8'))

soup = BeautifulSoup(html)

for c in soup('ul'):
	# bottom-up parsing since this is not particularly well formed html:
	# For each heading, find the superordinated heading by just looking up
	# previous tags until a higher-level heading is found. Do this for all
	# unordered lists (i.e. bullet point lists in markdown).
	h3 = c.find_previous('h3')
	h2 = h3.find_previous('h2')
	h1 = h2.find_previous('h1')
	credits[h1.string][h2.string][h3.string].append(list(c.children))

# Now manually write pychan-suited xml file
with open(OUTPUT, 'w') as f:
	write(f, 0, HEADER, newline=False)
	for h1, dct in sorted(credits.items(), key=creditsort):  # credits pages (pickbelts)
		write(f, 0, u'\n<HBox name="%s" position="185,45" padding="10">' % section_widgets[h1.string])
		for LR, dct in sorted(dct.items()):  # 'L' (left pane) or 'R' (right pane)
			if h1.string in huge_pages:
				write(f, 1, u'<ScrollArea name="%s" vertical_scrollbar="1" '
				            u'max_size="310,470" min_size="310,470">' % h1.string.lower())
				# Make sure there is no max_size set in this case!
				write(f, 1, u'<VBox min_size="310,500">')
			else:
				write(f, 1, u'<VBox max_size="310,500" min_size="310,500">')
			if LR == 'L':
				write(f, 2, u'<Label text="%s" name="headline" />' % h1.string)
				write(f, 2, u'<Icon image="content/gui/images/background/hr.png" />')
			for h3, ul in sorted(dct.items(), key=h3sort):  # subheadings
				write(f, 2, u'<VBox> <Label text="%s" name="headline" />' % h3.string)
				for items in ul:  # logical groups, unsorted
					wide = h1.string in wide_pages
					write(f, 3, u'<VBox name="box%s">' % (wide and u'_wide' or u''))
					for li in sorted(items, key=namesort):  # finally, names
						if li == '\n':
							continue
						write(f, 4, u'<Label text="%s" />' % li.string)
					close_vbox(3)
				close_vbox(2)
			close_vbox(1)
			if h1.string in huge_pages:
				write(f, 1, u'</ScrollArea>')
		close_hbox(0)
	write(f, 0, FOOTER)
