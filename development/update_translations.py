#!/usr/bin/env python2
# Encoding: utf-8
# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

import subprocess
import sys
from glob import glob

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
	SCENARIO_TRANSLATIONS[s] = glob('po/scenarios/*/%s.po' % s)
	SCENARIO_TEMPLATE[s] = 'po/scenarios/templates/%s.pot' % s


def update_from_template(input_po, input_template):
	"""
	@param input_po: the translation to be updated against new template
	@param input_template: the reference .pot template catalog
	"""
	print 'Updating %s:' % input_po
	try:
		subprocess.call([
			'msgmerge',
			'--update',
			input_po,
			input_template,
		], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError:
		#TODO handle
		print('Error while updating translation `%s`. Exiting.' % input_po)
		sys.exit(1)


def main():
	# Main interface translation (old 'uh' project in pootle)
	for f in INTERFACE_TRANSLATIONS:
		update_from_template(f, INTERFACE_TEMPLATE)

	# MP server message translation (old 'mp-server' project in pootle)
	for f in MP_SERVER_TRANSLATIONS:
		update_from_template(f, MP_SERVER_TEMPLATE)

	# Glossary translation (old 'terminology' project in pootle)
	#for f in GLOSSARY_TRANSLATIONS:
	#	update_from_template(f, GLOSSARY_TEMPLATE)

	# Scenario translation (old 'scenarios' project in pootle)
	for scenario, translations in SCENARIO_TRANSLATIONS.iteritems():
		for f in translations:
			update_from_template(f, SCENARIO_TEMPLATE[scenario])


if __name__ == '__main__':
	main()
