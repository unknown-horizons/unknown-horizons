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

from horizons.world.component.storagecomponent import StorageComponent
from horizons.util.gui import load_uh_widget

class ResourceOverviewBar(object):
	"""The thing on the top left.

	http://wiki.unknown-horizons.org/w/HUD

	Features:
	- display contents of currently relevant inventory (settlement/ship) [ ]
	- always show gold of local player [ ]
	- show costs of current build [ ]
	- configure the resources to show [ ]
		- per settlement [ ]
		- switch displayed resources to construction relevant res on build [ ]
		- res selection consistent with other res selection dlgs [ ]
			- goody: show available res

	Invariants:
	- it should be obvious that the res bar can be configured
	- it should be obvious that the res bar can be set per settlement
	"""

	def __init__(self, session):
		self.session = session

	def load(self):
		# called when any game (also new ones) start
		# register at player inventory for gold updates
		# TODO
		pass

	def set_inventory_instance(self, instance):
		"""Display different inventory. May change resources that are displayed"""
		print 'set instance: ', instance
		# TODO

	def set_construction_mode(self, resource_source_instance, build_costs):
		"""Show resources relevant to construction and build costs
		@param resource_source_instance: object with StorageComponent
		@param build_costs: dict, { res : amount }
		"""
		print 'set construction mode'
		#TODO
		pass

	def close_construction_mode(self):
		"""Return to normal configuration"""
		print 'close construction mode'
		# TODO
		pass

	def _update_gold(self):
		# TODO
		# display self.session.world.player.get_component(StorageComponent).inventory gold
		pass
