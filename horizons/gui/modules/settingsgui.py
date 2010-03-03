# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from fife.extensions import pychan

import horizons.main

from horizons.settings import Settings
from horizons.i18n.utils import find_available_languages
from horizons.i18n import update_all_translations

class SettingsGui(object):
	def show_settings(self):
		"""Shows the settings.
		"""
		fife = horizons.main.fife
		settings = Settings()

		resolutions = [str(w) + "x" + str(h) for w, h in fife.settings.getPossibleResolutions() if w >= 1024 and h >= 768]
		if len(resolutions) == 0:
			old = fife.settings.isFullScreen()
			fife.settings.setFullScreen(1)
			resolutions = [str(w) + "x" + str(h) for w, h in fife.settings.getPossibleResolutions() if w >= 1024 and h >= 768]
			fife.settings.setFullScreen(1 if old else 0)
		try:
			resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))
		except ValueError:
			resolutions.append(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height))

		languages_map = dict(reversed(find_available_languages()))
		languages_map[_('System default')] = ''

		dlg = self.widgets['settings']
		dlg.distributeInitialData({
			'language' : languages_map.keys(),
			'autosaveinterval' : range(0, 60, 2),
			'savedautosaves' : range(1, 30),
			'savedquicksaves' : range(1, 30),
			'screen_resolution' : resolutions,
			'screen_renderer' : ["OpenGL", "SDL"],
			'screen_bpp' : ["Desktop", "16", "24", "32"]
		})

		dlg.distributeData({
			'autosaveinterval' : settings.savegame.autosaveinterval/2,
			'savedautosaves' : settings.savegame.savedautosaves-1,
			'savedquicksaves' : settings.savegame.savedquicksaves-1,
			'screen_resolution' : resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height)),
			'screen_renderer' : 0 if settings.fife.renderer.backend == 'OpenGL' else 1,
			'screen_bpp' : int(settings.fife.screen.bpp / 10), # 0:0 16:1 24:2 32:3 :)
			'screen_fullscreen' : settings.fife.screen.fullscreen,
			'sound_enable_opt' : settings.sound.enabled,
			'language' : languages_map.keys().index(_('System default') if \
		      settings.language.name == '' or settings.language.name == 'System default' else \
		      settings.language.name)
		})

		dlg.mapEvents({
			'volume_music' : pychan.tools.callbackWithArguments(self.set_volume, dlg.findChild(name='volume_music_value'), dlg.findChild(name='volume_music')),
			'volume_effects' : pychan.tools.callbackWithArguments(self.set_volume, dlg.findChild(name='volume_effects_value'), dlg.findChild(name='volume_effects'))
		})

		# Save old music volumes in case the user presses cancel
		volume_music_intial = settings.sound.volume_music
		volume_effects_intial = settings.sound.volume_effects

		# Set music volume display and slider correctly
		volume_music = dlg.findChild(name='volume_music')
		volume_music.setValue(settings.sound.volume_music)
		volume_music_value =  dlg.findChild(name='volume_music_value')
		volume_music_value.text = unicode(int(volume_music.getValue() * 100 * 5)) + '%'

		# Set effects volume display and slider correctly
		volume_effects = dlg.findChild(name='volume_effects')
		volume_effects.setValue(settings.sound.volume_effects)
		volume_effects_value =  dlg.findChild(name='volume_effects_value')
		volume_effects_value.text = unicode(int(volume_effects.getValue() * 100 * 2)) + '%'

		if not self.show_dialog(dlg, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False):
			if settings.sound.enabled:
				fife.emitter['bgsound'].setGain(volume_music_intial)
				fife.emitter['effects'].setGain(volume_effects_intial)
				fife.emitter['speech'].setGain(volume_effects_intial)
				for e in fife.emitter['ambient']:
					e.setGain(volume_effects_intial)
			return

		# the following lines prevent typos
		setting_keys = ['autosaveinterval', 'savedautosaves', 'savedquicksaves', 'screen_resolution', 'screen_renderer', 'screen_bpp', 'screen_fullscreen', 'sound_enable_opt', 'language']
		new_settings = {}
		for key in setting_keys:
			new_settings[key] = dlg.collectData(key)

		changes_require_restart = False

		settings.savegame.autosaveinterval = (new_settings['autosaveinterval'])*2
		settings.savegame.savedautosaves = new_settings['savedautosaves']+1
		settings.savegame.savedquicksaves = new_settings['savedquicksaves']+1
		if new_settings['screen_fullscreen'] != settings.fife.screen.fullscreen:
			settings.fife.screen.fullscreen = new_settings['screen_fullscreen']
			changes_require_restart = True
		if new_settings['sound_enable_opt'] != settings.sound.enabled:
			settings.sound.enabled = new_settings['sound_enable_opt']
			if settings.sound.enabled:
				fife.setup_sound()
			else:
				fife.disable_sound()
		settings.sound.volume_music = volume_music.getValue()
		settings.sound.volume_effects = volume_effects.getValue()
		if new_settings['screen_bpp'] != int(settings.fife.screen.bpp / 10):
			settings.fife.screen.bpp = 0 if new_settings['screen_bpp'] == 0 else ((new_settings['screen_bpp'] + 1) * 8)
			changes_require_restart = True
		if new_settings['screen_renderer'] != (0 if settings.fife.renderer.backend == 'OpenGL' else 1):
			settings.fife.renderer.backend = 'OpenGL' if new_settings['screen_renderer'] == 0 else 'SDL'
			changes_require_restart = True
		if new_settings['screen_resolution'] != resolutions.index(str(settings.fife.screen.width) + 'x' + str(settings.fife.screen.height)):
			settings.fife.screen.width = int(resolutions[new_settings['screen_resolution']].partition('x')[0])
			settings.fife.screen.height = int(resolutions[new_settings['screen_resolution']].partition('x')[2])
			changes_require_restart = True
		if languages_map.items()[new_settings['language']][0] != settings.language.name:
			import gettext
			settings.language.name, settings.language.position = languages_map.items()[new_settings['language']]
			if settings.language.name != _('System default'):
				trans = gettext.translation('unknownhorizons', settings.language.position, languages=[settings.language.name])
				trans.install(unicode=1)
			else:
				gettext.install('unknownhorizons', 'build/mo', unicode=1)
				settings.language.name = ''
			update_all_translations()

		if changes_require_restart:
			self.show_dialog(self.widgets['requirerestart'], {'okButton' : True}, onPressEscape = True)

