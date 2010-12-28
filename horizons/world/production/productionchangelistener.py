# -*- coding: utf-8 -*-
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

from horizons.util import ChangeListener
from horizons.util.python import WeakMethodList

class ProductionFinishedListener(ChangeListener):
	"""Special ChangeListener for notifying about a production finishing
	(i.e. goods just have been produced).
	For inheriting by Production.
	Works the same way as horizons.util.ChangeListener.
	Listeners must accept the production object as parameter."""
	def _init(self):
		super(ProductionFinishedListener, self)._init()
		self.__production_finished_listeners = WeakMethodList()

	def add_production_finished_listener(self, listener):
		assert callable(listener)
		self.__production_finished_listeners.append(listener)

	def remove_production_finished_listener(self, listener):
		self.__production_finished_listeners.remove(listener)

	def on_production_finished(self):
		for f in self.__production_finished_listeners:
			f(self)



