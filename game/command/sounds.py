# ###################################################
# Copyright (C) 2008 The OpenAnno Team
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
from game.world.ambientsound import AmbientSound
from game.util import Point

class PlaySound(object):
	"""Command class that plays the build sound. This has been moved to a seperate
	class, inorder to be able to play only one sound for 20 buildings(like a group of
	trees)
	@param x,y: int coordinates where the sound is to be played."""

	def __init__(self, sound ,x, y, **trash):
		self.sound = sound
		self.x = x
		self.y = y

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		AmbientSound.play_special(self.sound, Point(self.x, self.y))