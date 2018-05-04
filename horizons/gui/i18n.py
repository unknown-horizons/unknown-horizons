# ###################################################
# Copyright (C) 2013-2017 The Unknown Horizons Team
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
import weakref

from horizons.gui import translations
from horizons.messaging import LanguageChanged

log = logging.getLogger("i18n")

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
	if filename in translations.text_translations:
		for (element_name, attribute), translation in translations.text_translations[filename].items():
			widget = untranslated.findChild(name=element_name)
			if widget is not None:
				replace_attribute(widget, attribute, translation)
				widget.adaptLayout()
	else:
		log.debug('No translation key in i18n.guitranslations for file %s', filename)

	# save as weakref for updates to translations
	translated_widgets[filename] = weakref.ref(untranslated)

	return untranslated


def replace_attribute(widget, attribute, text):
	if hasattr(widget, attribute):
		setattr(widget, attribute, text)
	else:
		log.warning("Could not replace attribute %s in widget %s", attribute, widget)


def update_translations(message):
	global translated_widgets
	translations.set_translations()

	for (filename, widget) in translated_widgets.items():
		widget = widget() # resolve weakref
		if not widget:
			continue
		all_widgets = translations.text_translations.get(filename, {})
		for (element_name, attribute), translation in all_widgets.items():
			element = widget.findChild(name=element_name)
			if element is None:
				# something hidden by pychan currently, we cannot find it
				log.debug('Could not find element `%s` in widget `%s` - '
				          'assuming it is hidden', element_name, widget)
				continue
			replace_attribute(element, attribute, translation)
			#NOTE pychan + reloading font = ???
			element.font = element.font
		widget.adaptLayout()


LanguageChanged.subscribe(update_translations)
