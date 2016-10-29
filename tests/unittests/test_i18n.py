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

import mock

import horizons.i18n
from horizons.i18n import change_language, gettext, gettext_lazy
from tests.unittests import TestCase


class Testi18n(TestCase):
	"""
	Test all things related to the horizons.i18n.
	"""
	def setUp(self):
		super(Testi18n, self).setUp()

		# Reset global translation object before each test to keep them isolated
		horizons.i18n._trans = None

	def test_null_translations(self):
		"""
		Without active language, the message will be returned untranslated.
		"""
		self.assertEqual(gettext('Unknown Horizons has crashed.'),
		                 u'Unknown Horizons has crashed.')

	def test_active_translation(self):
		change_language('de')
		self.assertEqual(gettext('Unknown Horizons has crashed.'),
		                 u'Unknown Horizons ist abgestürzt.')

		change_language('fr')
		self.assertEqual(gettext('Unknown Horizons has crashed.'),
		                 u'Unknown Horizons est tombé en panne.')

	def test_gettext_lazy(self):
		text = gettext_lazy('Unknown Horizons has crashed.')

		self.assertEqual(unicode(text), u'Unknown Horizons has crashed.')

		change_language('de')
		self.assertEqual(unicode(text), u'Unknown Horizons ist abgestürzt.')
