# -*- coding: utf-8 -*-
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

import random
import glob

from fife import fife

import horizons.main
from horizons.extscheduler import ExtScheduler

class Sound(object):
	"""Stuff related to engine & sound"""

	def __init__(self, engine):
		"""
		@param engine: fife from horizons.engine.py
		"""
		self.engine = engine
		self.emitter = {}
		self.emitter['bgsound'] = None
		self.emitter['effects'] = None
		self.emitter['speech'] = None

		#temporarily select a random music file to play. TODO: Replace with proper playlist
		self.ingame_music = glob.glob('content/audio/music/*.ogg')
		self.menu_music = glob.glob('content/audio/music/menu/*.ogg')
		self.initial_menu_music_element = None
		self.next_menu_music_element = None
		self.menu_music_played = False

		self.setup_sound()

	def setup_sound(self):
		if self.engine.get_fife_setting("PlaySounds"):
			self.enable_sound()
		else:
			self.disable_sound()

	def enable_sound(self):
		"""Enable all sound and start playing music."""
		if self.engine.get_fife_setting("PlaySounds"): # Set up sound if it is enabled
			self.soundmanager = self.engine.engine.getSoundManager()
			self.soundmanager.init()

			self.soundclipmanager = self.engine.engine.getSoundClipManager()
			self.emitter['bgsound'] = self.soundmanager.createEmitter()
			self.emitter['bgsound'].setGain(self.engine.get_uh_setting("VolumeMusic"))
			self.emitter['bgsound'].setLooping(False)
			self.emitter['effects'] = self.soundmanager.createEmitter()
			self.emitter['effects'].setGain(self.engine.get_uh_setting("VolumeEffects"))
			self.emitter['effects'].setLooping(False)
			self.emitter['speech'] = self.soundmanager.createEmitter()
			self.emitter['speech'].setGain(self.engine.get_uh_setting("VolumeEffects"))
			self.emitter['speech'].setLooping(False)
			self.emitter['ambient'] = []
			self.music_rand_element = random.randint(0, len(self.menu_music) - 1)
			self.initial_menu_music_element = self.music_rand_element

			self.check_music() # Start background music
			ExtScheduler().add_new_object(self.check_music, self, loops=-1)

	def disable_sound(self):
		"""Disable all sound outputs."""
		if self.emitter['bgsound'] is not None:
			self.emitter['bgsound'].reset()
		if self.emitter['effects'] is not None:
			self.emitter['effects'].reset()
		if self.emitter['speech'] is not None:
			self.emitter['speech'].reset()
		ExtScheduler().rem_call(self, self.check_music)


	def check_music(self):
		"""Used as callback to check if music is still running or if we have
		to load the next song."""
		if self.menu_music_played == False:
			if self.initial_menu_music_element == self.next_menu_music_element:
				self.ingame_music.extend(self.menu_music)
				self.music = self.ingame_music
				self.music_rand_element = random.randint(0, len(self.ingame_music) - 1)
				self.menu_music_played = True
			else:
				self.music = self.menu_music

		if hasattr(self, '_bgsound_old_byte_pos') and hasattr(self, '_bgsound_old_sample_pos'):
			if self._bgsound_old_byte_pos == self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS) and \
			   self._bgsound_old_sample_pos == self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS):
				# last track has finished (TODO: find cleaner way to check for this)
				skip = 0 if len(self.music) == 1 else random.randint(1, len(self.music)-1)
				self.music_rand_element = (self.music_rand_element + skip) % len(self.music)
				self.play_sound('bgsound', self.music[self.music_rand_element])
				if self.menu_music_played == False:
					self.next_menu_music_element = self.music_rand_element

		self._bgsound_old_byte_pos, self._bgsound_old_sample_pos = \
			self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS), \
			self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS)


	def play_sound(self, emitter, soundfile):
		"""Plays a soundfile on the given emitter.
		@param emitter: string with the emitters name in horizons.main.fife.sound.emitter that is to play the  sound
		@param soundfile: string containing the path to the soundfile"""
		if self.engine.get_fife_setting("PlaySounds"):
			emitter = self.emitter[emitter]
			assert emitter is not None, "You need to supply a initialised emitter"
			assert soundfile is not None, "You need to supply a soundfile"
			emitter.reset()
			#TODO remove str() -- http://fife.trac.cvsdude.com/engine/ticket/701
			emitter.setSoundClip(horizons.main.fife.sound.soundclipmanager.load(str(soundfile)))
			emitter.play()

