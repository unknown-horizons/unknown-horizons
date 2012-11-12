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
from horizons.component.storagecomponent import StorageComponent

from horizons.constants import GAME_SPEED
from horizons.messaging import ResourceProduced
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.world.managers.abstracticonmanager import AbstractIconManager
from horizons.gui.icons import ProductionFinishedIcon

class ProductionFinishedIconManager(AbstractIconManager):
	"""Manager class that manages all production finished icons. It listens to
	 ResourceProduced messages on the main message bus"""

	ANIMATION_STEPS = 1 # The steps that the image makes every run
	ANIMATION_DURATION = 20 # The duration how long the image moves up

	def __init__(self, renderer, layer):
		"""
		@param renderer: Renderer used to render the icons
		@param layer: map layer, needed to place icon
		"""
		super(ProductionFinishedIconManager, self).__init__(renderer, layer)
		self.run = dict()

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
				Scheduler().add_new_object(callback.callback, self,
				                           finish_callback=callback.finish_callback,
				                           loops=callback.loops,
				                           loop_interval=interval)

	def _on_resource_produced(self, message):
		"""This is called by the message bus with ResourceProduced messages"""
		assert isinstance(message, ResourceProduced)

		# if we get an empty dictionary or if the message is not from the local player, abort
		if (not message.produced_resources or not message.produced_resources.keys()) or \
		   not message.caller.instance.owner.is_local_player:
			return

		# makes the animation independent from game speed
		cur_ticks_per_second = Scheduler().timer.ticks_per_second
		interval = self.get_interval(cur_ticks_per_second)

		display_latency = 1
		for resource_item in message.produced_resources.items():
			icon = self.create_icon(message, resource_item[0])
			if not icon.amount:
				continue # abort if amount is zero

			group = self.get_renderer_group_name(message.sender, res=icon.resource,
			                                     tick=Scheduler().cur_tick)
			self.run[group] = self.ANIMATION_STEPS

			tick_callback = Callback(self.render_icon, icon.instance, group, icon)
			finish_callback = Callback(self.remove_icon, group)

			Scheduler().add_new_object(tick_callback, self, finish_callback=finish_callback,
		                           run_in=display_latency, loops=self.ANIMATION_DURATION,
		                           loop_interval=interval)
			display_latency += (self.ANIMATION_DURATION * display_latency) * (interval if interval else 1)

	def create_icon(self, message, resource):
		amount = message.sender.get_component(StorageComponent).inventory[resource]
		return ProductionFinishedIcon(resource, amount, message.sender,
		                              self.run, self.ANIMATION_STEPS)

	def remove_icon(self, group):
		""" Remove the icon after the animation finished
		Also removes the entry in the run-dictionary.
		"""
		super(ProductionFinishedIconManager, self).remove_icon(group)
		del self.run[group]
