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

from horizons.util import WorldObject

class NamedObject(WorldObject):
	"""An object that has a name."""
	def __init__(self, name=None, **kwargs):
		super(NamedObject, self).__init__(**kwargs)
		self.set_name(name)

	def set_name(self, name=None):
		"""Actually sets the name."""
		if name is None:
			name = self.get_default_name()
		self.name = name
		self._changed()

	def get_default_name(self):
		return 'object_%s' % self.getId()

	def save(self, db):
		super(NamedObject, self).save(db)
		db("INSERT INTO name (rowid, name) VALUES(?, ?)", self.getId(), self.name)

	def load(self, db, worldid):
		super(NamedObject, self).load(db, worldid)
		self.name = db("SELECT name FROM name WHERE rowid = ?", worldid)[0][0]

