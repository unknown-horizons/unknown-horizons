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
from game.world.building.consumer import Consumer
from game.world.building.producer import Producer
from game.world.storage import Storage

class DummyProducer(Building, Producer):
	""" Class for internal use in this file only. """
	def __init__(self, x, y, owner, instance = None):
		self.local_carriages = []
		self.inventory = Storage()
		Building.__init__(self, x, y, owner, instance)
		Producer.__init__(self)
		
class PrimaryProducer(DummyProducer):
	"""Class used for primary production buildings, e.g. tree
	
	These object produce something out of nothing, without
	requiring any raw material
	"""

class SecondaryProducer(DummyProducer, Consumer):
	"""Class used for secondary production buildings, e.g. lumberjack, weaver
	
	These object turn resources into something else
	"""
	def __init__(self, x, y, owner, instance = None):
		DummyProducer.__init__(self, x, y, owner, instance)
		Consumer.__init__(self)
		