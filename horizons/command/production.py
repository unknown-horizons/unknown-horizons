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

from horizons.command import GenericCommand
from horizons.util import WorldObject

class ToggleActive(GenericCommand):
	"""Sets a production to active/inactive."""
	def __init__(self, obj, production=None):
		super(ToggleActive, self).__init__(obj, "toggle_active")
		self._production = None if production is None else production.worldid

	def __call__(self, issuer):
		# NOTE: special call method, cause production must be saved as id, not as Production obj
		getattr(self._get_object(), self.method)( None if self._production is None else \
		                                          WorldObject.get_object_by_id(self._production) )


class AddProduction(GenericCommand):
	"""Add a production to a producer"""
	def __init__(self, obj, production_line_id):
		super(AddProduction, self).__init__(obj, "add_production_by_id", production_line_id)
