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

		if path is None:
			return False

		if not check_only:
			self.path = path
			if self.unit().is_moving():
				self.cur = 0
			else:
				self.cur = -1
			self.destination_in_building = destination_in_building

		return True

	def revert_path(self, destination_in_building):
		"""Moves back to the source of last movement, using same path"""
		self.cur = -1
		self.destination_in_building = destination_in_building
		self.path.reverse()

	def get_next_step(self):
		"""Returns the next step in the current movement
		@return: Point"""
		self.cur += 1
		if self.path is None or self.cur == len(self.path):
			self.cur = None
			return None

		if self.path[self.cur] in self.blocked_coords:
			# path is suddenly blocked, find another path
			blocked_coords = self.blocked_coords if isinstance(self.blocked_coords, list) else dict.fromkeys(self.blocked_coords, 1.0)
			self.path = findPath(self.path[self.cur-1], self.path[-1], self.path_nodes, blocked_coords, self.move_diagonal)
			if self.path is None:
				raise PathBlockedError
			self.cur = 1

		if self.destination_in_building and self.cur == len(self.path)-1:
			self.destination_in_building = False
			self.unit().hide()
		elif self.source_in_building and self.cur == 2:
			self.source_in_building = False
			self.unit().show()

		return Point(*self.path[self.cur])

	def get_move_target(self):
		"""Returns the point where the path leads
		@return: Point or None if no path has been calculated"""
		return None if self.path is None else Point(*self.path[-1])

	def end_move(self):
		"""Pretends that the path is finished in order to make the unit stop"""
		del self.path[self.cur+1:]

	def save(self, db, unitid):
		if self.path is not None:
			for step in xrange(len(self.path)):
				db("INSERT INTO unit_path(`unit`, `index`, `x`, `y`) VALUES(?, ?, ?, ?)", unitid, step, self.path[step][0], self.path[step][1])

	def load(self, db, worldid):
		"""
		@return: Bool, wether a path was loaded
		"""
		path_steps = db("SELECT x, y FROM unit_path WHERE unit = ? ORDER BY `index`", worldid)
		if len(path_steps) == 0:
			return False
		else:
			self.path = []
			for step in path_steps:
				self.path.append(step) # the sql statement orders the steps
			self.cur = self.path.index(self.unit().position.get_coordinates()[0])
			return True
