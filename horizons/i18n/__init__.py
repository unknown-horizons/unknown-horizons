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
	global translated_widgets
	if filename in guitranslations.text_translations:
		for i in guitranslations.text_translations[filename].iteritems():
			try:
				widget = untranslated.findChild(name=i[0])
				#TODO what happens to TooltipLabels? their text is untouched (elif)
				# we currently do not use any, but this could cause bugs.
				if hasattr(widget, 'tooltip'):
					widget.tooltip = i[1]
				elif isinstance(widget, pychan.widgets.Label)\
						or isinstance(widget, pychan.widgets.Button):
					widget.text = i[1]
				elif isinstance(widget, pychan.widgets.Window):
					widget.title = i[1]
				widget.adaptLayout()
			except AttributeError, e:
				print e
				print i, ' in ', filename
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
		for element_name, translation in guitranslations.text_translations.get(filename,{}).iteritems():
			try:
				w = widget.findChild(name=element_name)
				#TODO presumably doesn't work with TooltipLabels, see above
				if hasattr(w, 'tooltip'):
					w.tooltip = translation
				else:
					w.text = translation
				widget.adaptLayout()
			except AttributeError, e:
				print e
				print filename, widget
