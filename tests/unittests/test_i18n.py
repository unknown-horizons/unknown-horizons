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

import polib
import pytest

import horizons.i18n
from horizons.i18n import change_language, disable_translations, gettext as T, gettext_lazy as LazyT


@pytest.fixture(autouse=True)
def i18n(tmpdir, mocker):
	"""
	Create temporary MO files, so we don't have to rely on them beeing build outside of tests,
	or have to build all of them by running setup.py build_i18n
	"""
	horizons.i18n.reset_language()

	de_dir = tmpdir.mkdir('de')
	de_dir.mkdir('de')
	de_mo_dir = de_dir.mkdir('de', 'LC_MESSAGES')

	po = polib.POFile()
	po.metadata = {'Content-Type': 'text/plain; charset=utf-8'}
	po.append(polib.POEntry(msgid='McAvoy or Stewart? These timelines are confusing.',
				msgstr='McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.'))
	po.save_as_mofile(str(de_mo_dir.join('unknown-horizons.mo')))

	fr_dir = tmpdir.mkdir('fr')
	fr_dir.mkdir('fr')
	fr_mo_dir = fr_dir.mkdir('fr', 'LC_MESSAGES')

	po = polib.POFile()
	po.metadata = {'Content-Type': 'text/plain; charset=utf-8'}
	po.append(polib.POEntry(msgid='McAvoy or Stewart? These timelines are confusing.',
				msgstr='McAvoy ou Stewart? Ces délais sont confus.'))
	po.save_as_mofile(str(fr_mo_dir.join('unknown-horizons.mo')))

	languages = {
		'de': str(de_dir),
		'fr': str(fr_dir)
	}
	mocker.patch('horizons.i18n.find_available_languages', return_value=languages)


def test_null_translations():
	"""
	Without active language, the message will be returned untranslated.
	"""
	assert T('McAvoy or Stewart? These timelines are confusing.') ==\
		'McAvoy or Stewart? These timelines are confusing.'


def test_active_translation():
	change_language('de')
	assert T('McAvoy or Stewart? These timelines are confusing.') ==\
		 'McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.'

	change_language('fr')
	assert T('McAvoy or Stewart? These timelines are confusing.') ==\
		 'McAvoy ou Stewart? Ces délais sont confus.'


def test_gettext_lazy():
	text = LazyT('McAvoy or Stewart? These timelines are confusing.')

	assert str(text) == 'McAvoy or Stewart? These timelines are confusing.'

	change_language('de')
	assert str(text) == 'McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.'


def test_disable_translations():
	change_language('de')
	assert T('McAvoy or Stewart? These timelines are confusing.') ==\
		 'McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.'

	with disable_translations():
		assert T('McAvoy or Stewart? These timelines are confusing.') ==\
			 'McAvoy or Stewart? These timelines are confusing.'

	assert T('McAvoy or Stewart? These timelines are confusing.') ==\
		 'McAvoy oder Stewart? Diese Zeitlinien sind verwirrend.'
