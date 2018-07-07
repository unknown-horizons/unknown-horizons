#!/usr/bin/env python3
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

from __future__ import print_function
import re
import subprocess
import os
import sys
import inspect

from collections import defaultdict
from glob import glob

cmd_folder = os.path.realpath(
    os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "..")))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from horizons.constants import LANGUAGENAMES


LANG_RE = re.compile(r'.*/(.*).po')
SCENARIO_LANG_RE = re.compile(r'.*/(.*)/[^/]*.po')

INTERFACE_TRANSLATIONS = glob('po/uh/*.po')
INTERFACE_TEMPLATE = 'po/uh/unknown-horizons.pot'

MP_SERVER_TRANSLATIONS = glob('po/uh-server/*.po')
MP_SERVER_TEMPLATE = 'po/uh-server/unknown-horizons-server.pot'

GLOSSARY_TRANSLATIONS = glob('po/terminology/*.po')
GLOSSARY_TEMPLATE = 'po/terminology/pootle-terminology.pot'

SCENARIO_TRANSLATIONS = {}
SCENARIO_TEMPLATE = {}
ALL_SCENARIOS = ('tutorial', 'The_Unknown')
for s in ALL_SCENARIOS:
	SCENARIO_TRANSLATIONS[s] = glob('po/scenarios/*/{}.po'.format(s))
	SCENARIO_TEMPLATE[s] = 'po/scenarios/templates/{}.pot'.format(s)

VOICES_TRANSLATIONS = glob('po/voices/*.po')
VOICES_TEMPLATE = 'po/voices/unknown-horizons-voices.pot'

GLOBAL_AUTHORS = ('Translators', 'Chris Oelmueller', 'Michal Čihař', 'Michal Čihař Čihař')
language_authors = defaultdict(set)


def update_from_template(input_po, input_template):
	"""
	@param input_po: the translation to be updated against new template
	@param input_template: the reference .pot template catalog
	"""
	print('Updating {}:'.format(input_po))
	try:
		subprocess.call([
		    'msgmerge',
		    '--previous',
		    '--update',
		    input_po,
		    input_template, ],
		    stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError:
		#TODO handle
		print('Error while updating translation `{}`. Exiting.'.format(input_po))
		sys.exit(1)


def update_authors_per_file(input_po, regexp=LANG_RE, since='weblate-credits..', pushed_by='Weblate'):
	authors = subprocess.check_output([
	    'git',
	    'log',
	    since,
	    '--committer',
	    pushed_by,
	    '--format=%an',
	    input_po, ],
	    stderr=subprocess.STDOUT)

	#TODO Clearly the above can never fail, ever. But what if it did?
	lang = regexp.search(input_po).groups()[0]
	for author in authors.decode('utf-8').split('\n'):
		if not author:
			continue
		if author in GLOBAL_AUTHORS:
			continue
		english_lang = LANGUAGENAMES.get_english(lang)
		language_authors[english_lang].add(author)


def main():
	# Main interface translation (old 'uh' project in pootle)
	for f in INTERFACE_TRANSLATIONS:
		update_from_template(f, INTERFACE_TEMPLATE)
		update_authors_per_file(f)

	# MP server message translation (old 'mp-server' project in pootle)
	for f in MP_SERVER_TRANSLATIONS:
		update_from_template(f, MP_SERVER_TEMPLATE)
		update_authors_per_file(f)

	# Glossary translation (old 'terminology' project in pootle)
	#for f in GLOSSARY_TRANSLATIONS:
	#	update_from_template(f, GLOSSARY_TEMPLATE)
	#	update_authors_per_file(f)

	# Scenario translation (old 'scenarios' project in pootle)
	for scenario, translations in SCENARIO_TRANSLATIONS.items():
		for f in translations:
			update_from_template(f, SCENARIO_TEMPLATE[scenario])
			update_authors_per_file(f, regexp=SCENARIO_LANG_RE)

	# Voices translation
	for f in VOICES_TRANSLATIONS:
		update_from_template(f, VOICES_TEMPLATE)
		update_authors_per_file(f)

	# Output data ready for AUTHORS.md copy/paste
	print('-- New translation contributors since last update:')
	sort_order = lambda e: LANGUAGENAMES.get_by_value(e[0], english=True)
	for language, authors in sorted(language_authors.items(), key=sort_order):
		print('\n####', language)
		# TODO
		# The sorted() below will not correctly sort names containing non-ascii.
		# You'll need to rely on manual copy/paste and ordering anyways, so just
		# keep your eyes open a bit more than usual.
		for author in sorted(authors):
			print_ready = map(str.capitalize, author.split())
			print('*', ' '.join(print_ready))


if __name__ == '__main__':
	main()
