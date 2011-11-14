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

import logging
import os
import weakref

from fife.extensions import pychan

import horizons.main
from horizons.i18n.guitranslations import set_translations, text_translations

log = logging.getLogger("i18n")

# init translations
set_translations()

# save translated widgets
translated_widgets = {}

def translate_widget(untranslated, filename):
	"""
	Load widget translations from guitranslations.py file.
	Its entries look like {element_name: (attribute, translation)}.
	The translation is not applied to inactive widgets.
	Check update_all_translations for the application.
	"""
	global translated_widgets
	if filename in guitranslations.text_translations:
		for entry in guitranslations.text_translations[filename].iteritems():
			widget = untranslated.findChild(name=entry[0])
			replace_attribute(widget, entry[1][0], entry[1][1])
			widget.adaptLayout()
	else:
		log.debug('No translation for file %s', filename)

	# save as weakref for updates to translations
	translated_widgets[filename] = weakref.ref(untranslated)

	return untranslated


def update_all_translations():
	"""Update the translations in every active widget"""
	global translated_widgets
	set_translations()
	for (filename, widget) in translated_widgets.iteritems():
		widget = widget() # resolve weakref
		if not widget:
			continue
		for element_name, (attribute, translation) in guitranslations.text_translations.get(filename,{}).iteritems():
			element = widget.findChild(name=element_name)
			replace_attribute(element, attribute, translation)
			widget.adaptLayout()


def replace_attribute(widget, attribute, text):
	if hasattr(widget, attribute):
		setattr(widget, attribute, text)
	else:
		log.debug("Could not replace attribute %s in widget %s", attribute, widget)
