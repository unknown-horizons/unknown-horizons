# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

"""
Maps _ to the ugettext unicode gettext call. Use: _(string).
N_ takes care of plural forms for different languages. It masks ungettext
calls (unicode, plural-aware _() ) to create different translation strings
depending on the counter value. Not all languages have only two plural forms
"One" / "Anything else". Use: N_("{n} dungeon", "{n} dungeons", n).format(n=n)
where n is a counter.

We will need to make gettext recognise namespaces some time, but hardcoded
'unknown-horizons' works for now since we currently only use one namespace.
"""

import platform
import gettext
import os
import logging
import locale
import weakref

from horizons.constants import LANGUAGENAMES
from horizons.i18n import objecttranslations, guitranslations
from horizons.i18n.utils import get_fontdef_for_locale, find_available_languages

log = logging.getLogger("i18n")

# init translations
guitranslations.set_translations()
objecttranslations.set_translations()

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
			widget = untranslated.findChild(name=entry[0][0])
			if widget is not None:
				replace_attribute(widget, entry[0][1], entry[1])
				widget.adaptLayout()
	else:
		log.debug('No translation key in i18n.guitranslations for file %s', filename)

	# save as weakref for updates to translations
	translated_widgets[filename] = weakref.ref(untranslated)

	return untranslated


def update_all_translations():
	"""Update the translations in every active widget"""
	from horizons.gui.gui import build_help_strings
	global translated_widgets
	guitranslations.set_translations()
	objecttranslations.set_translations()
	for (filename, widget) in translated_widgets.iteritems():
		widget = widget() # resolve weakref
		if not widget:
			continue
		for (element_name, attribute), translation in guitranslations.text_translations.get(filename,{}).iteritems():
			element = widget.findChild(name=element_name)
			replace_attribute(element, attribute, translation)
		if filename == 'help.xml':
			build_help_strings(widget)
		widget.adaptLayout()


def replace_attribute(widget, attribute, text):
	if hasattr(widget, attribute):
		setattr(widget, attribute, text)
	else:
		log.debug("Could not replace attribute %s in widget %s", attribute, widget)


def change_language(language=None):
	"""Load/change the language of Unknown Horizons.

	Called on startup and when changing the language in the settings menu.
	"""
	import horizons.main

	if language: # non-default
		try:
			# NOTE about gettext fallback mechanism:
			# English is not shipped as .mo file, thus if English is
			# selected we use NullTranslations to get English output.
			fallback = (language == 'en')
			trans = gettext.translation('unknown-horizons', find_available_languages()[language],
										languages=[language], fallback=fallback)
			trans.install(unicode=True, names=['ngettext',])
		except IOError:
			#xgettext:python-format
			print "Configured language {lang} could not be loaded.".format(lang=language)
			horizons.main.fife.set_uh_setting('Language', LANGUAGENAMES[''])
			return change_language() # recurse
	else:
		# default locale
		if platform.system() == "Windows": # win doesn't set the language variable by default
			os.environ[ 'LANGUAGE' ] = locale.getdefaultlocale()[0]
		gettext.install('unknown-horizons', 'content/lang', unicode=True, names=['ngettext',])

	# expose the plural-aware translate function as builtin N_ (gettext does the same to _)
	import __builtin__
	__builtin__.__dict__['N_'] = __builtin__.__dict__['ngettext']

	# update fonts
	fontdef = get_fontdef_for_locale(language or horizons.main.fife.get_locale())
	horizons.main.fife.pychan.loadFonts(fontdef)

	# dynamically reset all translations of active widgets
	update_all_translations()
