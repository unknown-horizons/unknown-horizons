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

import random
from typing import ClassVar

from fife.fife import AudioSpaceCoordinate

import horizons.globals
from horizons.component import Component
from horizons.extscheduler import ExtScheduler


class AmbientSoundComponent(Component):
	"""Support for playing ambient sounds, such as animal noise or collector sounds.
	"""
	AMBIENT_SOUND_INTERVAL: ClassVar[int] = 20 # interval between two plays
	AMBIENT_SOUND_INTERVAL_VARIANCE: ClassVar[list[int]] = [0, 15] # a number of this interval is added to the one above

	NAME: ClassVar[str] = "ambientsound"

	def __init__(self, soundfiles: list[str] | None = None) -> None:
		"""
		@param soundfiles: list of paths
		"""
		super().__init__()
		self.soundfiles: list[str] = soundfiles or []
		self.__init()

	def __init(self) -> None:
		self.__emitter = None # only create it when really needed

	def __create_emitter(self, gain: float) -> None:
		if horizons.globals.fife.get_fife_setting("PlaySounds"):
			self.__emitter = horizons.globals.fife.sound.soundmanager.createEmitter()
			self.__emitter.setGain(horizons.globals.fife.get_uh_setting("VolumeEffects") * gain)
			horizons.globals.fife.sound.emitter['ambient'].append(self.__emitter)

	def _init_playing(self) -> None:
		if hasattr(self.instance.owner, "is_local_player") and self.instance.owner.is_local_player:
			# don't use session random, this is player dependent
			play_every = self.__class__.AMBIENT_SOUND_INTERVAL + \
												random.randint(* self.__class__.AMBIENT_SOUND_INTERVAL_VARIANCE)
			for soundfile in self.soundfiles:
				#TODO remove str() -- http://github.com/fifengine/fifengine/issues/701
				self.play_ambient(str(soundfile), loop_interval=play_every,
				                  position=self.instance.position.center)

	def load(self, db, worldid: int) -> None:
		super().load(db, worldid)
		self.__init()
		# don't start playing all at once

		interval = (0, self.__class__.AMBIENT_SOUND_INTERVAL +
		            self.__class__.AMBIENT_SOUND_INTERVAL_VARIANCE[1])
		run_in = random.randint(*interval)
		ExtScheduler().add_new_object(self._init_playing, self, run_in=run_in)

	def remove(self) -> None:
		super().remove()
		self.stop_sound()
		self.__emitter = None

	def play_ambient(
	    self,
	    soundfile: str,
	    loop_interval: int | None = None,
	    position=None,
	    gain: float = 10,
	) -> None:
		"""Starts playing an ambient sound. On looping, it will also play right now.
		Default: play sound once
		@param soundfile: path to audio file
		@param loop_interval: delay between two plays, None means no looping, 0 is no pause between looping
		@param position: Point
		@param gain: float, volume of the sound, default is 10
		"""
		if horizons.globals.fife.get_fife_setting("PlaySounds"):
			if self.__emitter is None:
				self.__create_emitter(gain)

			if position is not None:
				self.__emitter.setRolloff(1.9)
				# set to current position
				self.__emitter.setPosition(AudioSpaceCoordinate(position.x, position.y, 1))
			else:
				self.__emitter.setRolloff(0) # reset to default

			#TODO remove str() -- http://github.com/fifengine/fifengine/issues/701
			self.__emitter.setSoundClip(horizons.globals.fife.sound.soundclipmanager.load(str(soundfile)))

			if loop_interval == 0:
				self.__emitter.setLooping(True)
			elif loop_interval is not None:
				duration = loop_interval + (float(self.__emitter.getDuration()) / 1000) # from millisec
				ExtScheduler().add_new_object(self.__emitter.play, self, duration, -1)

			self.__emitter.play()

	def stop_sound(self) -> None:
		"""Stops playing an ambient sound"""
		if self.__emitter:
			self.__emitter.stop()
		ExtScheduler().rem_all_classinst_calls(self)

	@classmethod
	def play_special(
	    cls,
	    sound: str,
	    position=None,
	    gain: float = 10,
	) -> None:
		"""Plays a special sound listed in the db table sounds_special
		from anywhere in the code and without an instance of AmbientSound.
		@param sound: string, key in table sounds_special
		@param position: optional, source of sound on map
		@param gain: float, volume of the sound, default is 10
		"""
		if horizons.globals.fife.get_fife_setting("PlaySounds"):
			a = AmbientSoundComponent()
			#TODO remove str() -- http://github.com/fifengine/fifengine/issues/701
			soundfile = horizons.globals.db.get_sound_file(str(sound))
			a.play_ambient(soundfile, position=position, gain=gain)
			horizons.globals.fife.sound.emitter['ambient'].remove(a.__emitter)
