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

from dbreader import DbReader

########################################################################
class UhDbAccessor(DbReader):
	"""UhDbAccessor is the class that contains all the sql code. It is meant
	to keep all the sql code in a central place, to make it reusable and
	maintainable."""

	def __init__(self, dbfile):
		super(UhDbAccessor, self).__init__(dbfile=dbfile)


	# ------------------------------------------------------------------
	# Db Access Functions start here
	# ------------------------------------------------------------------

	# Resource table

	"""
	Returns the name to a specific resource id.
	@param id: int resource's id, of which the name is returned
	"""
	def get_res_name(self, id):
		return self.cached_query("SELECT name FROM resource WHERE id = ?", id)[0][0]


	# Sound table

	"""
	Returns the soundfile to the related sound name.
	@param sound: string, key in table sounds_special
	"""
	def get_sound_file(self, soundname):
		return self.cached_query("SELECT file FROM sounds INNER JOIN sounds_special ON \
			    sounds.id = sounds_special.sound AND sounds_special.type = ?", soundname)[0][0]


	def get_random_action_set(self, object_id, level):
		return self.cached_query("SELECT action_set_id, preview_action_set_id \
		FROM action_set WHERE object_id = ? and level = ? ORDER BY random()",
		                        object_id,
		                        level)

