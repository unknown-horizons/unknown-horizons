# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

import horizons.main
from fife.extensions.fife_timer import repeatCall

class AmbientSound(object):
	"""Support for playing ambient sounds, such as animal noise.
	It relies on the subclass having an attribute "position", which must be either a Point or Rect.
	"""
	def __init__(self, positioning=True, **kwargs):
		"""
		@param positioning: bool, whether sound should play from a certain position.
		"""
		super(AmbientSound, self).__init__(**kwargs)
		self.__init(positioning)

	def __init(self, positioning):
		self.__positioning = positioning
		self.__emitter = None
		self.__timer = None

	def create_emitter(self):
		if horizons.main.fife.get_fife_setting("PlaySounds"):
			self.__emitter = horizons.main.fife.soundmanager.createEmitter()
			self.__emitter.setGain(horizons.main.fife.get_uh_setting("VolumeEffects")*10)
			if self.__positioning:
				self.__emitter.setRolloff(1.9)
			horizons.main.fife.emitter['ambient'].append(self.__emitter)

	def load(self, db, worldid):
		super(AmbientSound, self).load(db, worldid)
		# set positioning per default to true, since only special sounds have this
		# set to false, which are nonrecurring
		self.__init(positioning=True)

	def __del__(self):
		self.__emitter = None
		self.__positioning = None
		self.__timer = None

	def play_ambient(self, soundfile, looping, play_every=None):
		"""Starts playing an ambient sound
		@param soundfile: path to audio file
		@param looping: bool, whether sound should loop for forever
		@param play_every: play the sound every x seconds if looping is true
		"""
		if horizons.main.fife.get_fife_setting("PlaySounds"):
			if self.__emitter is None:
				self.create_emitter()
			# set to current position
			if(hasattr(self, 'position') and self.position != None and self.__positioning):
				self.__emitter.setPosition(self.position.center().x, self.position.center().y, 1)
			self.__emitter.setSoundClip(horizons.main.fife.soundclippool.addResourceFromFile(soundfile))
			if play_every is None:
				self.__emitter.setLooping(looping)
			elif looping and play_every is not None:
				duration = play_every + self.__emitter.getDuration()*1000
				self.__timer = repeatCall(duration, self.__emitter.play)
			self.__emitter.play()

	def stop_sound(self):
		"""Stops playing an ambient sound"""
		if self.__emitter:
			self.__emitter.stop()

	@classmethod
	def play_special(cls, sound, position = None):
		"""Plays a special sound listed in the db table sounds_special
		from anywhere in the code and without an instance of AmbientSound.
		@param sound: string, key in table sounds_special
		@param position: optional, source of sound on map
		"""
		if horizons.main.fife.get_fife_setting("PlaySounds"):
			if position is None:
				a = AmbientSound(positioning=False)
			else:
				a = AmbientSound()
				a.position = position
			soundfile = horizons.main.db.get_sound_file(sound)
			a.play_ambient(soundfile, looping = False)
			horizons.main.fife.emitter['ambient'].remove(a.__emitter)
