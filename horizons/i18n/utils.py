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

from gettext import translation
from horizons.constants import FONTDEFS, LANGUAGENAMES

"""
N_ takes care of plural forms for different languages. It masks ungettext
calls (unicode, plural-aware _() ) to operate on module level after import.
We will need to make it recognise namespaces some time, but hardcoded
'unknown-horizons' works for now since we currently only use one namespace.
"""
namespace_translation = translation('unknown-horizons', fallback=True)
N_ = namespace_translation.ungettext


def find_available_languages():
	"""Returns a dict( lang_key -> locale_dir )"""
	alternatives = ('content/lang',
	                'build/mo',
	                '/usr/share/locale',
	                '/usr/share/games/locale',
	                '/usr/local/share/locale',
	                '/usr/local/share/games/locale')

	import os
	from glob import glob

	languages = {}

	for i in alternatives:
		for j in glob('%s/*/*/unknown-horizons.mo' % i):
			splited = j.split(os.sep)
			key = splited[-3]
			if not key in languages:
				languages[key] = os.sep.join(splited[:-3])
			#TODO we need to strip strings here if an "@" occurs and only
			# use the language code itself (e.g. ca@valencia.po -> ca.po)

	# there's always a default, which is english
	languages[LANGUAGENAMES['']] = ''
	languages['en'] = ''

	return languages

def get_fontdef_for_locale(locale):
	"""Returns path to the fontdef file for a locale. Libertine is default."""
	fontdef_file = 'libertine'
	if locale in FONTDEFS.iterkeys():
		fontdef_file = FONTDEFS[locale]
	return 'content/fonts/{filename}.fontdef'.format(filename = fontdef_file)
