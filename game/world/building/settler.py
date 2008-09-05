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

from building import Building, Selectable
from game.world.production import SecondaryProducer
from game.gui.tabwidget import TabWidget
import game.main
from buildable import BuildableSingle

class Settler(SecondaryProducer, BuildableSingle, Selectable, Building):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	def __init__(self, x, y, owner, instance = None, **kwargs):
		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, **kwargs)
		self.inhabitants = 1 # TODE: read initial value from the db
		self.max_inhabitants = 4 # TODO: read from db!

	# TODO: saving and loading