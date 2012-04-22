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

from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.util import Point
from horizons.command import Command

class PlaySound(Command):
	"""Command class that plays the build sound. This has been moved to a separate
	class, in order to be able to play only one sound for 20 buildings(like a group of
	trees)
	@param sound: sound id that is to be played
	@param position: tuple of int coordinates where the sound is to be played."""

	def __init__(self, sound, position=None, **trash):
		self.sound = sound
		self.position = position

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		if self.position is None:
			AmbientSoundComponent.play_special(self.sound)
		else:
			AmbientSoundComponent.play_special(self.sound, Point(self.position[0], self.position[1]))

Command.allow_network(PlaySound)
