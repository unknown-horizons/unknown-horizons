# ###################################################
# Copyright (C) 2009 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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
import game.main

class AmbientSound(object):
	"""Support for playing ambient sounds, such as animal noise.
	It relies on the subclass having an attribute "position", which must be either a
	game.util.Point or game.util.Rect.
	"""
	def __init__(self, **kwargs):
		"""
		"""
		super(AmbientSound, self).__init__(**kwargs)
		if game.main.settings.sound.enabled:
			self.emitter = game.main.fife.soundmanager.createEmitter()
			self.emitter.setGain(game.main.settings.sound.volume_effects)
			self.emitter.setRolloff(1.9)
			game.main.fife.emitter['ambient'].append(self.emitter)

	def play_ambient(self, soundfile, looping):
		"""Starts playing an ambient sound
		@param soundfile: path to audio file
		@param looping: bool, wether sound should loop for forever
		"""
		if game.main.settings.sound.enabled:
			# set to current position
			if(hasattr(self, 'position') and self.position != None):
				self.emitter.setPosition(self.position.center().x, self.position.center().y, 1)
			self.emitter.setLooping(looping)
			self.emitter.setSoundClip(game.main.fife.soundclippool.addResourceFromFile(soundfile))
			self.emitter.play()

	@classmethod
	def play_special(cls, sound, position = None):
		"""Plays a special sound listed in the db table sounds_special
		from anywhere in the code and without an instance of AmbientSound.
		@param sound: string, key in table sounds_special
		@param position: optional, source of sound on map
		"""
		a = AmbientSound()
		a.position = position
		soundfile = game.main.db("SELECT file FROM sounds INNER JOIN sounds_special ON sounds.rowid = sounds_special.sound AND sounds_special.type = ?", sound)[0][0]
		a.play_ambient(soundfile, looping = False)


