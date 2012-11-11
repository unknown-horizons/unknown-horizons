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

import horizons.globals

from fife import fife

from horizons.component.storagecomponent import StorageComponent
from horizons.constants import GAME_SPEED
from horizons.gui.util import get_res_icon_path
from horizons.messaging import ResourceProduced
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.world.managers.abstracticonmanager import AbstractIconManager

class ProductionFinishedIconManager(AbstractIconManager):
	"""Manager class that manages all production finished icons. It listens to
	 ResourceProduced messages on the main message bus"""

	def __init__(self, renderer, layer):
		"""
		@param renderer: Renderer used to render the icons
		@param layer: map layer, needed to place icon
		"""
		super(ProductionFinishedIconManager, self).__init__(renderer, layer)
		self.run = dict()
		self.animation_duration = 20 # The duration how long the image moves up
		self.animation_steps = 1 # The steps that the image makes every run
		self.background = "content/gui/images/background/produced_notification.png"

		ResourceProduced.subscribe(self._on_resource_produced)

	def end(self):
		Scheduler().rem_all_classinst_calls(self)
		for group in self.run.keys():
			self.renderer.removeAll(group)
		self.run = None
		super(ProductionFinishedIconManager, self).end()
		ResourceProduced.unsubscribe(self._on_resource_produced)

	def get_interval(self, ticks):
		interval = None
		if ticks > GAME_SPEED.TICKS_PER_SECOND:
			interval = (ticks // GAME_SPEED.TICKS_PER_SECOND) - 1

		return interval

	def speed_changed(self, new_ticks):
		active_calls = Scheduler().get_classinst_calls(self)
		interval = self.get_interval(new_ticks)

		for callback in active_calls.keys():
			if callback.loops > 0:
				Scheduler().rem_object(callback)
				Scheduler().add_new_object(callback.callback, self, finish_callback=callback.finish_callback,
				                           run_in=1, loops=callback.loops,
				                           loop_interval=interval)

	def _on_resource_produced(self, message):
		"""This is called by the message bus with ResourceProduced messages"""
		assert isinstance(message, ResourceProduced)

		# if we get an empty dictionary, abort
		if (not message.produced_resources or not message.produced_resources.keys()) or \
			not message.caller.instance.owner.is_local_player:
			return

		# makes the animation independent from game speed
		cur_ticks_per_second = Scheduler().timer.ticks_per_second
		interval = self.get_interval(cur_ticks_per_second)

		display_latency = 1
		for resource_item in message.produced_resources.items():
			res = resource_item[0] # TODO multiple resources
			amount = message.sender.get_component(StorageComponent).inventory[res]

			# abort if amount is zero
			if not amount:
				continue

			group = self.get_resource_string(message.sender, res)
			self.run[group] = self.animation_steps

			tick_callback = Callback(self.__render_icon, message.sender, group, res, amount)
			finish_callback = Callback(self.remove_icon, group)

			Scheduler().add_new_object(tick_callback, self, finish_callback=finish_callback,
		                           run_in=display_latency, loops=self.animation_duration,
		                           loop_interval=interval)
			display_latency += (self.animation_duration * display_latency) * (interval if interval else 1)

	def __render_icon(self, instance, group, res, amount):
		""" This renders the icon and calculates its position
		"""
		loc = super(ProductionFinishedIconManager, self).pre_render_icon(instance, group)

		# self.run[group] is used for the moving up animation
		# use -50 here to get some more offset in height
		bg_rel = fife.Point(0, -50 - self.run[group])
		rel = fife.Point(-14, -50 - self.run[group])
		self.run[group] += self.animation_steps

		bg_node = fife.RendererNode(loc, bg_rel)
		node = fife.RendererNode(loc, rel)

		bg_image = horizons.globals.fife.imagemanager.load(self.background)
		res_icon = horizons.globals.fife.imagemanager.load(get_res_icon_path(res))
		font = horizons.globals.fife.pychanmanager.getFont('mainmenu')

		self.renderer.addImage(group, bg_node, bg_image)
		self.renderer.resizeImage(group, node, res_icon, 24, 24)
		self.renderer.addText(group, node, font, ' '*9 + '{amount:>2d}'.format(amount=amount))

	def remove_icon(self, group):
		""" Remove the icon after the animation finished
		Also removes the entry in the run-dictionary.
		"""
		self.renderer.removeAll(group)
		del self.run[group]

	def get_resource_string(self, instance, res):
		"""Returns the render name for resource icons of this instance
		This key MUST be unique!
		"""
		return "produced_resource_" + str(res) + "_" + str(instance.position.origin)\
		       + "_" + str(Scheduler().cur_tick)
