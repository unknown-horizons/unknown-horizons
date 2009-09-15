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

import logging
from horizons.i18n.guitranslations import set_translations, text_translations
import horizons.main
import pychan
from os.path import basename

log = logging.getLogger("i18n")

# init translations
set_translations()

# save translated widgets
translated_widgets = {}

"""
def set_text(widget, text):
	gui.find_child(name=widget).text = text

def set_title(widget, title):
	gui.findChild(name=widget).title = title
"""

def load_xml_translated(filename):
	"""Just like pychan's load_xml, but translates strings according to the data specified
	in guitranslations.py"""
	global translated_widgets
	try:
		untranslated = pychan.loadXML('content/gui/%s' % filename)
	except (IOError, ValueError), e:
		print 'PLEASE REPORT: invalid path %s in translation!', e
		untranslated = pychan.loadXML(filename)


	if filename in guitranslations.text_translations:
		for i in guitranslations.text_translations[filename].iteritems():
			try:
				widget = untranslated.findChild(name=i[0])
				if isinstance(widget, pychan.widgets.Label)\
						or isinstance(widget, pychan.widgets.Button):
					widget.text = i[1]
					widget.adaptLayout()
				elif isinstance(widget, pychan.widgets.Window):
					widget.title = i[1]
			except AttributeError, e:
				print e
				print i, ' in ', filename
	else:
		log.debug('No translation for file %s', filename)

	translated_widgets[filename] = untranslated

	return untranslated

def update_all_translations():
	set_translations()
	global translated_widgets
	for i in translated_widgets.iteritems():
		for j in guitranslations.text_translations.get(i[0],{}).iteritems():
			try:
				i[1].findChild(name=j[0]).text = j[1]
			except AttributeError, e:
				print e
				print i, ' in ', i[0]
