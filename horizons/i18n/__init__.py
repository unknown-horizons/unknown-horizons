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

"""
Maps _ to the gettext call. Use: T(string). N_ takes care of plural forms for
different languages. It masks ngettext calls (str, plural-aware T() ) to create
different translation strings depending on the counter value. Not all languages
have only two plural forms "One" / "Anything else". Use: N_("{n} dungeon", "{n}
dungeons", n).format(n=n) where n is a counter.

We will need to make gettext recognize namespaces some time, but hardcoded
'unknown-horizons' works for now since we currently only use one namespace.
"""

import gettext as gettext_module
import glob
import json
import locale
import logging
import os
import platform
from contextlib import contextmanager

import horizons.globals
from horizons.constants import FONTDEFS, LANGUAGENAMES
from horizons.ext.speaklater import make_lazy_gettext
from horizons.messaging import LanguageChanged

log = logging.getLogger("i18n")


# Sentinel for when no language is loaded or translations are disabled.
# Using NullTranslations means gettext, ngettext, and lazy gettext all behave
# correctly without special-casing None, and English/fallback is the same
# concept as "no active translation".
_NULL_TRANSLATIONS = gettext_module.NullTranslations()

# currently active translation object
_trans: gettext_module.NullTranslations = _NULL_TRANSLATIONS


def gettext(message: str) -> str:
	return _trans.gettext(message)


gettext_lazy = make_lazy_gettext(lambda: gettext)


def ngettext(message1: str, message2: str, count: int) -> str:
	return _trans.ngettext(message1, message2, count)


LANGCACHE: dict[str, str] = {}


@contextmanager
def disable_translations():
	"""
	Temporarily disables translations. Affects gettext and lazy gettext objects.
	"""
	global _trans
	original_translation = _trans
	_trans = _NULL_TRANSLATIONS
	try:
		yield
	finally:
		_trans = original_translation


def reset_language() -> None:
	"""
	Reset global state to initial.
	"""
	global _trans
	global LANGCACHE
	_trans = _NULL_TRANSLATIONS
	LANGCACHE = {}


def find_available_languages(domain='unknown-horizons', update=False):
	"""Returns a dict( lang_key -> locale_dir )"""
	global LANGCACHE
	if LANGCACHE and not update:
		return LANGCACHE

	alternatives = ('content/lang',
	                'build/mo',
	                # Relative to the content dir we chdir'ed into, so this
	                # resolves for any install prefix, /app/share included.
	                '../locale',
	                '/usr/share/locale',
	                '/usr/share/games/locale',
	                '/usr/local/share/locale',
	                '/usr/local/share/games/locale')

	LANGCACHE = {}

	for i in alternatives:
		for j in glob.glob(f'{i}/*/*/{domain}.mo'):
			splited = j.split(os.sep)
			key = splited[-3]
			if key not in LANGCACHE:
				LANGCACHE[key] = os.sep.join(splited[:-3])

	# there's always a default, which is english
	LANGCACHE[LANGUAGENAMES['']] = ''
	LANGCACHE['en'] = ''

	return LANGCACHE


def get_fontdef_for_locale(locale):
	"""Returns path to the fontdef file for a locale. Unifont is default."""
	fontdef_file = FONTDEFS.get(locale, 'unifont')
	return os.path.join('content', 'fonts', f'{fontdef_file}.xml')


def change_language(language=None):
	"""Load/change the language of Unknown Horizons.
	Called on startup and when changing the language in the settings menu.
	"""
	global _trans

	if language: # non-default
		try:
			# NOTE about gettext fallback mechanism:
			# English is not shipped as .mo file, thus if English is
			# selected we use NullTranslations to get English output.
			fallback = (language == 'en')
			trans = gettext_module.translation('unknown-horizons', find_available_languages()[language],
			                                   languages=[language], fallback=fallback)
			_trans = trans
		except (OSError, KeyError, ValueError) as err:
			# KeyError can happen with a settings file written to by more than one UH
			# installation (one that has compiled language files and one that hasn't)
			# ValueError can be raised by gettext if for instance the plural forms are
			# corrupted.
			log.warning("Configured language %s could not be loaded.", language)
			log.warning("Error: %s", err)
			log.warning("Continuing with English as fallback.")
			horizons.globals.fife.set_uh_setting('Language', LANGUAGENAMES[''])
			return change_language() # recurse
	else:
		# default locale
		if platform.system() == "Windows": # win doesn't set the language variable by default
			os.environ['LANGUAGE'] = locale.getdefaultlocale()[0]
		_trans = gettext_module.translation('unknown-horizons', 'content/lang',
		                                   fallback=True)

	# update fonts
	new_locale = language or horizons.globals.fife.get_locale()
	fontdef = get_fontdef_for_locale(new_locale)
	horizons.globals.fife.pychan.loadFonts(fontdef)

	LanguageChanged.broadcast(None)


def get_language_translation_stats(language_code: str) -> int:
	"""
	Return percentage of translated strings for given language.
	"""
	if language_code not in LANGCACHE:
		raise Exception(f'Unknown language "{language_code}"')

	try:
		with open(os.path.join('content', 'lang', 'stats.json')) as f:
			data = json.load(f)
			return data[language_code]
	except FileNotFoundError:
		return
