# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import logging
from collections import defaultdict

import horizons.globals
from horizons.component import Component
from horizons.messaging import InstanceInventoryUpdated
from horizons.scheduler import Scheduler
from horizons.util.loaders.actionsetloader import ActionSetLoader


class InventoryOverlayComponent(Component):
	"""Display different additional graphics ("animation overlays" in FIFE terminology)
	depending on inventory status of a building or unit.
	"""
	NAME = "inventoryoverlay"
	DEPENDENCIES = ['StorageComponent']
	log = logging.getLogger('component.overlays')

	def __init__(self, overlays=None):
		super().__init__()
		self.overlays = overlays or {}

		# Stores {resource_id: amount that is currently used as overlay, or None if no overlay}
		self.current_overlays = defaultdict(lambda: None)

	@property
	def action_set(self):
		"""E.g. 'as_lumberjack_barrack0' """
		return self.instance._action_set_id

	@property
	def fife_instance(self):
		return self.instance._instance

	@property
	def identifier(self):
		"""E.g. 'idle_as_lumberjack_barrack0' """
		return self.fife_instance.getCurrentAction().getId()

	def initialize(self):
		super().initialize()
		InstanceInventoryUpdated.subscribe(self.inventory_changed, sender=self.instance)

	def add_overlay(self, overlay_set, z_order=10):
		"""Creates animation overlay from action set *overlay_set* and adds it to fife instance.

		@param overlay_set: action set with images to be used as animation overlay
		@param z_order: the (numerical) drawing order identifier. Usually res_id.
		"""
		if not self.fife_instance.isAnimationOverlay(self.identifier):
			# parameter True: also convert color overlays attached to base frame(s) into animation
			self.fife_instance.convertToOverlays(self.identifier, True)

		animationmanager = horizons.globals.fife.animationmanager
		for rotation, frames in overlay_set.items():
			id = '{}+{}'.format(self.identifier, rotation)
			if animationmanager.exists(id):
				ov_anim = animationmanager.getPtr(id)
			else:
				ov_anim = animationmanager.create(id)
				for frame_img, frame_data in frames.items():
					try:
						frame_length = frame_data[0]
					except TypeError:
						# not using atlases
						frame_length = frame_data
					pic = horizons.globals.fife.imagemanager.load(frame_img)
					frame_milliseconds = int(frame_length * 1000)
					ov_anim.addFrame(pic, frame_milliseconds)
			self.fife_instance.addAnimationOverlay(self.identifier, rotation, z_order, ov_anim)

	def remove_overlay(self, res_id):
		"""Removes animation overlay associated with resource *res_id* from fife instance.

		We use *res_id* as z-order identifier, which removeAnimationOverlay actually asks for.
		"""
		self.current_overlays[res_id] = None
		#TODO remove hardcoded rotations, use action set keys (of which set?)
		for rotation in range(45, 360, 90):
			self.fife_instance.removeAnimationOverlay(self.identifier, rotation, res_id)

	def inventory_changed(self, message):
		"""A changelistener notified the StorageComponent of this instance.

		Because it did not tell us which resources were added or removed, we
		need to check everything in the inventory for possible updates.
		"""
		for res_id, new_amount in message.inventory.items():
			self.update_overlay(res_id, new_amount)

	def update_overlay(self, res_id, new_amount):
		"""Called when inventory amount of one resource changes.

		Looks for a fitting animation overlay based on the new inventory amount for that resource.
		If that overlay is different from the currently displayed one, removes the old overlay for
		that resource and adds a new one based on what fits *new_amount* best.
		"""
		try:
			overlay_order = self.overlays[self.action_set][self.instance._action][res_id]
		except KeyError:
			self.log.warning(
				'No overlays defined for resource `%s`, action `%s` and action set `%s`. '
				'Consider using `null` overlays for amount 0 in this action set.',
				res_id, self.instance._action, self.action_set)
			self.current_overlays[res_id] = None
			return

		# We use max(0, new_amount) restricted to what exists in overlay_order.
		# E.g. for
		#   new_amount = 3
		#   overlay_order = [[0, None],  [2, 'as_2'],  [5, 'as_full']]
		# we drop 5 (because it is defined but too large),
		# ignore 4 and 3 (because they are not defined in overlay_order),
		# and find 'as_2' as our new overlay for the amount 2.

		for (amount, overlay_name) in sorted(overlay_order, reverse=True):

			if amount > new_amount:
				# This `if` drops defined-but-too-large candidates (i.e. case `5` in above example).
				continue

			if amount == self.current_overlays[res_id]:
				# Nothing to do, continue using the same overlay
				return

			if overlay_name is None:
				# Empty overlay, only display base action set (i.e. case `0` in above example)
				self.remove_overlay(res_id)
				return

			try:
				overlay_set = ActionSetLoader.get_set(self.action_set)[overlay_name]
			except KeyError:
				self.log.warning(
					'Could not find overlay action set defined for object '
					'`%s` with id `%s` for resource `%s` and amount `%s`. '
					'Falling back to next lower overlay.',
					self.instance, self.identifier, res_id, amount)
				continue
			self.remove_overlay(res_id)
			self.add_overlay(overlay_set, z_order=res_id)
			self.current_overlays[res_id] = amount
			return

	def load(self, db, worldid):
		super().load(db, worldid)
		Scheduler().add_new_object(self.initialize, self, run_in=0)

	def remove(self):
		"""Removes all animation overlays from the fife instance.

		Also converts the animation overlay on drawing order 0 (i.e. the old base image)
		back to a plain "action set" in UH terminology.
		"""
		InstanceInventoryUpdated.unsubscribe(self.inventory_changed, sender=self.instance)

		for (res_id, overlay) in self.current_overlays.items():
			if overlay is not None:
				self.remove_overlay(res_id)

		# remove base image "overlay" that we did `convertToOverlays` in `initialize`
		# Note that this gets us back the actual base image as not-an-overlay.
		# In particular, no animation overlays can be added unless `convertToOverlays`
		# is called again.
		self.remove_overlay(0)

		super().remove()
