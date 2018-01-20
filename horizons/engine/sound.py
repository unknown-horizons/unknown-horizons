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

import glob
import random
from collections import deque

from fife import fife

from horizons.extscheduler import ExtScheduler


class Sound:
	"""Stuff related to engine & sound"""

	def __init__(self, engine):
		"""
		@param engine: Fife from horizons.engine.engine
		"""
		self.engine = engine
		self.emitter = {}
		self.emitter['bgsound'] = None
		self.emitter['effects'] = None
		self.emitter['speech'] = None
		self.emitter['ambient'] = []

		# Temporarily select a random music file to play.
		# TODO: Replace with proper playlist.
		self.ingame_music = glob.glob('content/audio/music/*.ogg')
		self.menu_music = glob.glob('content/audio/music/menu/*.ogg')

		# Store the three most recently played files to avoid repetition.
		# If we don't have three files available, reduce accordingly:
		# At least one track not in last_tracks always needs to exist.
		available = max(0, len(self.ingame_music) - 1)
		sample_size = min(3, available)
		self.last_tracks = deque(maxlen=sample_size)
		if len(self.menu_music) <= 1:
			# Sad stuff: we only have few menu tracks available right now.
			# Also play some ingame_tracks after the dedicated menu music
			# is exhausted, but make sure to start with these menu tracks.
			ingame_tracks = random.sample(self.ingame_music, sample_size)
			self.menu_music.extend(ingame_tracks)
			self.last_tracks.extend(ingame_tracks)

		self.setup_sound()

	def end(self):
		if self.engine.get_fife_setting("PlaySounds"):
			for emitter in self.emitter['ambient'][:]:
				emitter.stop()
				self.emitter['ambient'].remove(emitter)
			self.emitter['effects'].stop()
			self.emitter['speech'].stop()

	def setup_sound(self):
		if self.engine.get_fife_setting("PlaySounds"):
			self.enable_sound()
		else:
			self.disable_sound()

	def enable_sound(self):
		"""Enable all sound and start playing music."""
		# Set up sound if it is enabled
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

		# Start background music:
		self._old_byte_pos = 0.0
		self._old_smpl_pos = 0.0
		self.check_music(refresh_playlist=True, play_menu_tracks=True)
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

	def check_music(self, refresh_playlist=False, play_menu_tracks=False):
		"""Used as callback to check if music is still running or if we have
		to load the next song.
		@param refresh_playlist: Whether to update the playlist type (menu, ingame).
		refresh_playlist should e.g. be set when loading happens, after which we no longer want to play menu music.
		The current track, however, will still finish playing before choosing a new track.
		@param play_menu_tracks: Whether to start the playlist with menu music. Only works with refresh_playlist=True.
		"""
		if refresh_playlist:
			if play_menu_tracks and self.menu_music:
				self.music = self.menu_music
			elif self.ingame_music:
				self.music = self.ingame_music
			else:
				self.music = None  # Cannot play any tracks if there are none

		self._new_byte_pos = self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS)
		self._new_smpl_pos = self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS)
		#TODO find cleaner way to check for this:
		# check whether last track has finished:
		if (self.music is not None
		    and self._new_byte_pos == self._old_byte_pos
		    and self._new_smpl_pos == self._old_smpl_pos):
			# choose random new track, but not one we played very recently
			track = random.choice([m for m in self.music if m not in self.last_tracks])
			self.play_sound('bgsound', track)
			self.last_tracks.append(track)

		self._old_byte_pos = self.emitter['bgsound'].getCursor(fife.SD_BYTE_POS)
		self._old_smpl_pos = self.emitter['bgsound'].getCursor(fife.SD_SAMPLE_POS)

	def play_sound(self, emitter, soundfile):
		"""Plays a soundfile on the given emitter.
		@param emitter: string: name of emitter that is to play the sound
		@param soundfile: string: path to the sound file we want to play
		"""
		if not self.engine.get_fife_setting("PlaySounds"):
			return
		emitter = self.emitter[emitter]
		#TODO what do we need those two asserts for...
		assert emitter is not None, "You need to supply an initialized emitter"
		assert soundfile is not None, "You need to supply a soundfile"
		emitter.reset()
		#TODO remove str() -- http://github.com/fifengine/fifengine/issues/449
		emitter.setSoundClip(self.soundclipmanager.load(str(soundfile)))
		emitter.play()

	def set_volume_emitter(self, emitter, volume):
		"""Sets the volume on the emitter specified by emitter_name.
		@param emitter: string with the emitters name, used as key for the self.emitter dict
		@param volume: double which volume the emitter is to be set to range[0, 1]
		"""
		if self.engine.get_fife_setting("PlaySounds"):
			self.emitter[emitter].setGain(volume)

	def set_volume_bgmusic(self, volume):
		"""Sets the volume for the backgroundmusic.
		@param volume: double which volume the emitter is to be set to range[0, 1]
		"""
		self.set_volume_emitter('bgsound', volume)

	def set_volume_effects(self, volume):
		"""Sets the volume for the effects, speech and ambient sounds.
		@param volume: double which volume the emitter is to be set to range[0, 1]
		"""
		self.set_volume_emitter('effects', volume)
		self.set_volume_emitter('speech', volume)
		for emitter in self.emitter['ambient']:
			emitter.setGain(volume * 2)
