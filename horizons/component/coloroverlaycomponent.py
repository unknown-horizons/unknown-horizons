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
from operator import attrgetter

from fife import fife

import horizons.globals
from horizons.component import Component
from horizons.messaging import ActionChanged
from horizons.scheduler import Scheduler
from horizons.util.color import Color as UtilColor
from horizons.util.loaders.actionsetloader import ActionSetLoader


class ColorOverlayComponent(Component):
	"""Change parts of graphics dynamically on runtime ("color overlays" in FIFE terminology).

	Supports multiple overlay sets for the same instance, and also
	supports changing more than one color in the same overlay set.

	While technically possible, it is not recommended to use the former:
	You will need to make sure animation overlays exist for that z_order,
	else a color overlay cannot be visible.

	Because there usually is no way to guarantee this, it is **very much**
	recommended to use one overlay on z_order `0` featuring multiple areas
	with different colors instead, and to then replace those colors one by one.
	We can guarantee that z_order of 0 works because `convertToOverlays` is
	called when adding new color overlays, which converts the base image of
	the current action to an animation overlay at precisely depth 0.

	Directives to change colors look like this (for every action):
	- [z_order, overlay action name, color to be replaced, target color to draw]

	When in doubt, use 0 as z_order.
	The overlay action name is the folder located next to other actions (e.g. idle).
	Color to be replaced: List with three (rgb) or four (rgba) int elements.
		In particular, [80, 0, 0] and [80, 0, 0, 128] are different colors!
	Target color to draw: As above, or string interpreted as attribute of instance.
		To access player colors, you can usually employ "owner.color".

	All in all, a multi-color replacement could look like this example:

		idle:
		# color_idle: action set with three differently colored areas
			# color red area in player color (alpha is set to 128 here)
			- [0, color_idle, [255, 0, 0], [owner.color, 128]]
			# also color green area *in the same images* in blue
			- [0, color_idle, [0, 255, 0], [0, 0, 255, 128]]
			# hide third (blue) area by setting alpha value to 0
			- [0, color_idle, [0, 0, 255], [0, 0, 0, 0]]

	# multiple single-overlay example (usually not what you want):
	#	idle:
	#		# color magenta area in player color (needs animation overlay at order 1)
	#		- [1, color1_idle, [255, 0, 255], [owner.color, 64]]
	#		# also color some other teal area in blue (needs animation overlay at order 2)
	#		- [2, color2_idle, [0, 255, 255], [0, 0, 255, 128]]
	"""
	NAME = "coloroverlay"
	log = logging.getLogger('component.overlays')

	def __init__(self, overlays=None):
		super().__init__()
		self.overlays = overlays or {}
		self.current_overlays = defaultdict(dict)

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
		ActionChanged.subscribe(self.update_overlay, self.instance)
		ActionChanged.broadcast(self.instance, self.instance._action)

	def update_overlay(self, message):
		#TODO Tracking is broken: remove all data stored for old action
		# Ultimately it would be great to have current_overlays working...
		self.current_overlays.clear()
		try:
			overlays = self.overlays[self.action_set][message.action]
		except KeyError:
			self.log.warning(
				'No color overlay defined for action set `%s` and action `%s`. '
				'Consider using `null` overlays for this action.',
				self.action_set, message.action)
			return

		for (z_order, overlay_name, from_color, to_color) in overlays:
			if not self.current_overlays[z_order]:
				self.add_overlay(overlay_name, z_order)
			fife_from = fife.Color(*from_color)
			try:
				fife_to = fife.Color(*to_color)
			except (TypeError, NotImplementedError):
				color_attribute, alpha = to_color
				color = attrgetter(color_attribute)(self.instance)
				if isinstance(color, UtilColor) or isinstance(color, fife.Color):
					fife_to = fife.Color(color.r, color.g, color.b, alpha)
				else:
					raise TypeError('Unknown color `{}` as attribute `{}`: '
						'Expected either fife.Color or horizons.util.Color.'
						.format(color, to_color))
			self.change_color(z_order, fife_from, fife_to)

	def add_overlay(self, overlay_name, z_order):
		"""Creates color overlay recoloring the area defined in *overlay_set*

		and adds it to fife instance. Note that a color overlay on *z_order*
		can only be visible if an animation overlay with that specific order
		exists as well. For order 0, `convertToOverlays()` makes sure they do.
		"""
		if not self.fife_instance.isAnimationOverlay(self.identifier):
			# parameter False: do not convert color overlays attached to base
			self.fife_instance.convertToOverlays(self.identifier, False)

		try:
			overlay_set = ActionSetLoader.get_set(self.action_set)[overlay_name]
		except KeyError:
			self.log.warning(
				'Could not find overlay action set `%s` defined for object '
				'`%s` with id `%s`. Not adding overlay for this action.',
				overlay_name, self.instance, self.identifier)
			return

		animationmanager = horizons.globals.fife.animationmanager
		self.current_overlays[z_order] = overlay_set
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
					pic = horizons.globals.fife.animationloader.load_image(frame_img, self.action_set, overlay_name, rotation)
					frame_milliseconds = int(frame_length * 1000)
					ov_anim.addFrame(pic, frame_milliseconds)
			overlay = fife.OverlayColors(ov_anim)
			self.fife_instance.addColorOverlay(self.identifier, rotation, z_order, overlay)

	def change_color(self, z_order, from_color, to_color):
		"""Changes color of *from_color*ed area to *to_color*.

		color parameters: fife.Color objects
		"""
		for rotation in self.current_overlays[z_order]:
			overlay = self.fife_instance.getColorOverlay(self.identifier, rotation, z_order)
			overlay.changeColor(from_color, to_color)

	def remove_overlay(self):
		"""Removes color overlay recoloring the *color*-colored area from fife instance.
		"""
		for z_order, overlay_set in self.current_overlays.items():
			for rotation in overlay_set:
				self.fife_instance.removeColorOverlay(self.identifier, rotation, z_order)

	def load(self, db, worldid):
		super().load(db, worldid)
		Scheduler().add_new_object(self.initialize, self, run_in=0)

	def remove(self):
		"""Removes all color overlays from the fife instance. """
		self.remove_overlay()
		super().remove()
