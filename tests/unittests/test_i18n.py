# coding: utf-8

# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

import os
import shutil
import tempfile

import mock
import polib

import horizons.i18n
from horizons.i18n import change_language, gettext, gettext_lazy
from tests.unittests import TestCase


class Testi18n(TestCase):
	"""
	Test all things related to the horizons.i18n.
	"""
	def setUp(self):
		super(Testi18n, self).setUp()

		horizons.i18n.reset_language()

		# Create temporary MO files, so we don't have to rely on them beeing build outside
		# of tests, or have to build all of them by running setup.py build_i18n
		self.de_dir = tempfile.mkdtemp()
		de_mo_dir = os.path.join(self.de_dir, 'de', 'LC_MESSAGES')
		os.makedirs(de_mo_dir)

		po = polib.POFile()
		po.metadata = {'Content-Type': 'text/plain; charset=utf-8'}
		po.append(polib.POEntry(msgid='McAvoy or Stewart? These timelines are confusing.',
					msgstr=u'McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.'))
		po.save_as_mofile(os.path.join(de_mo_dir, 'unknown-horizons.mo'))

		self.fr_dir = tempfile.mkdtemp()
		fr_mo_dir = os.path.join(self.fr_dir, 'fr', 'LC_MESSAGES')
		os.makedirs(fr_mo_dir)

		po = polib.POFile()
		po.metadata = {'Content-Type': 'text/plain; charset=utf-8'}
		po.append(polib.POEntry(msgid='McAvoy or Stewart? These timelines are confusing.',
					msgstr=u'McAvoy ou Stewart? Ces délais sont confus.'))
		po.save_as_mofile(os.path.join(fr_mo_dir, 'unknown-horizons.mo'))

		languages = {
			'de': self.de_dir,
			'fr': self.fr_dir
		}
		self.find_languages_patcher = mock.patch('horizons.i18n.find_available_languages',
		                                         return_value=languages)
		self.find_languages_patcher.start()

	def tearDown(self):
		super(Testi18n, self).tearDown()

		self.find_languages_patcher.stop()
		shutil.rmtree(self.fr_dir)
		shutil.rmtree(self.de_dir)

	def test_null_translations(self):
		"""
		Without active language, the message will be returned untranslated.
		"""
		self.assertEqual(gettext('McAvoy or Stewart? These timelines are confusing.'),
		                'McAvoy or Stewart? These timelines are confusing.')

	def test_active_translation(self):
		change_language('de')
		self.assertEqual(gettext('McAvoy or Stewart? These timelines are confusing.'),
		                 u'McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.')

		change_language('fr')
		self.assertEqual(gettext('McAvoy or Stewart? These timelines are confusing.'),
		                 u'McAvoy ou Stewart? Ces délais sont confus.')

	def test_gettext_lazy(self):
		text = gettext_lazy('McAvoy or Stewart? These timelines are confusing.')

		self.assertEqual(unicode(text), u'McAvoy or Stewart? These timelines are confusing.')

		change_language('de')
		self.assertEqual(unicode(text), u'McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.')
