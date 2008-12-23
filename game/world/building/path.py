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

from building import Building
import fife
import game.main
import math
import weakref
from buildable import BuildableLine, BuildableSingle

class Path(Building, BuildableLine):
	speed = 42 # probably obsolete
	def init(self):
		"""
		"""
		super(Path, self).init()
		origin = self.position.origin
		self.island = weakref.ref(game.main.session.world.get_island(origin.x, origin.y))
		for tile in self.island().get_surrounding_tiles(origin):
			if tile is not None and isinstance(tile.object, Path):
				tile.object.recalculateOrientation()
		self.recalculateOrientation()
		self.island().registerPath(self)

	def load(self, db, worldid):
		super(Path, self).load(db, worldid)
		self.recalculateOrientation()
		self.island().registerPath(self)

	def remove(self):
		super(Path, self).remove()
		origin = self.position.origin
		self.island().unregisterPath(self)
		island = game.main.session.world.get_island(origin.x, origin.y)
		for tile in self.island().get_surrounding_tiles(origin):
			if tile is not None and isinstance(tile.object, Path):
				tile.object.recalculateOrientation()

	def recalculateOrientation(self):
		"""
		"""
		action = ''
		origin = self.position.origin
		tile = self.island().get_tile(origin.offset(0, -1))
		if tile is not None and isinstance(tile.object, (Path, Bridge)):
			action += 'a'
		tile = self.island().get_tile(origin.offset(1, 0))
		if tile is not None and isinstance(tile.object, (Path, Bridge)):
			action += 'b'
		tile = self.island().get_tile(origin.offset(0, 1))
		if tile is not None and isinstance(tile.object, (Path, Bridge)):
			action += 'c'
		tile = self.island().get_tile(origin.offset(-1, 0))
		if tile is not None and isinstance(tile.object, (Path, Bridge)):
			action += 'd'
		if action == '':
			action = 'default'
		location = self._instance.getLocation()
		location.setLayerCoordinates(fife.ModelCoordinate(int(origin.x + 1), int(origin.y), 0))
		self.act(action, location, True)

	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = 1
		return super(Path, cls).getInstance(*args, **kwargs)

class Bridge(Building, BuildableSingle):
	#@classmethod
	#def getInstance(cls, x, y, action=None, **trash):
	#	super(Bridge, cls).getInstance(x = x, y = y, action = 'default', **trash)

	def init(self):
		"""
		"""
		super(Bridge, self).init()
		origin = self.position.origin
		self.island = weakref.ref(game.main.session.world.get_island(origin.x, origin.y))
		for tile in self.island().get_surrounding_tiles(origin):
			if tile is not None and isinstance(tile.object, Path):
				tile.object.recalculateOrientation()

	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = 1
		return super(Bridge, cls).getInstance(*args, **kwargs)
