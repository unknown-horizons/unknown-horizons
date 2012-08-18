# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.

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

from fife import fife

import horizons.main
from horizons.gui.util import get_res_icon_path
from horizons.messaging import ResourceProduced
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback

class ProductionFinishedIconManager(object):
	"""Manager class that manages all production finished icons. It listenes to
	 ResourceProduced messages on the main message bus"""

	def __init__(self, renderer, layer):
		"""
		@param renderer: Renderer used to render the icons
		@param layer: map layer, needed to place icon
		"""
		self.layer = layer
		self.renderer = renderer
		self.run = dict()
		self.animation_steps = 15

		ResourceProduced.subscribe(self._on_resource_produced)

	def end(self):
		self.renderer = None

		ResourceProduced.unsubscribe(self._on_resource_produced)

	def _on_resource_produced(self, message):
		"""This is called by the message bus with ResourceProduced messages"""
		assert isinstance(message, ResourceProduced)

		res = message.produced_resources.keys()[0]
		group = self.get_resource_string(message.sender, res)
		self.run[group] = 1

		tick_callback = Callback(self.__render_icon, message.sender, group, res)
		finish_callback = Callback(self.remove_icon, group)
		Scheduler().add_new_object(tick_callback, self, finish_callback=finish_callback, run_in=1, loops=self.animation_steps)

	def __render_icon(self, instance, group, res):
		""" This renders the icon. It calculates the position of the icon.
		Most parts of this were copied from horizons/world/managers/statusiconmanager.py
		"""
		# TODO: Try to unify the __render methods of this class and statusiconmanager.py!
		self.renderer.removeAll(group)

		# self.run[group] is used for the moving up animation
		rel = fife.Point(0, -35 - self.run[group])
		self.run[group] += 2

		pos = instance.position

		loc = fife.Location(self.layer)
		loc.setExactLayerCoordinates(
		  fife.ExactModelCoordinate(
		    pos.origin.x + float(pos.width) / 4,
		    pos.origin.y + float(pos.height) / 4,
		  )
		)

		node = fife.RendererNode(loc, rel)

		bg_image = horizons.main.fife.imagemanager.load("content/gui/images/background/sq.png")
		res_icon = horizons.main.fife.imagemanager.load(get_res_icon_path(res, 32, False))
		self.renderer.addImage(group, node, bg_image)
		self.renderer.resizeImage(group, node, res_icon, 23, 23)

	def remove_icon(self, group):
		""" Remove the icon after the animation finished
		Also removes the entry in the run-dictionary.
		"""
		self.renderer.removeAll(group)
		del self.run[group]

	def get_resource_string(self, instance, res):
		"""Returns the render name for resource icons of this instance"""
		resource_string = "produced_resource_" + str(res) + "_" + str(instance.position.origin)
		return resource_string
