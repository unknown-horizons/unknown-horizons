# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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
from operator import attrgetter

from fife import fife

import horizons.globals

from horizons.component import Component
from horizons.ext.dummy import Dummy
from horizons.scheduler import Scheduler
from horizons.util.color import Color as UtilColor
from horizons.util.loaders.actionsetloader import ActionSetLoader


class ColorOverlayComponent(Component):
	"""Change parts of graphics dynamically on runtime ("color overlays" in FIFE terminology)."""
	#TODO Support more than one color overlay simultaneously (needs optional z-order parameters)
	NAME = "coloroverlay"
	log = logging.getLogger('component.overlays')

	def __init__(self, overlays=None):
		super(ColorOverlayComponent, self).__init__()
		self.overlays = overlays or {}
		# action set dict of currently displayed overlay, stored so we can iterate over its keys
		self.overlay_set = None

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
		super(ColorOverlayComponent, self).initialize()

		try:
			overlays = self.overlays[self.action_set][self.instance._action]
		except KeyError:
			self.log.warning(
				'No color overlay defined for action set `%s` and action `%s`. '
				'Consider using `null` overlays for this action.',
				self.action_set, self.instance._action)
			return

		for (overlay_name, (from_color, to_color)) in overlays.iteritems():
			self.add_overlay(overlay_name)
			fife_from = fife.Color(*from_color)
			try:
				fife_to = fife.Color(*to_color)
			except TypeError:
				color = attrgetter(to_color)(self.instance)
				if isinstance(color, UtilColor):
					fife_to = fife.Color(color.r, color.g, color.b, 255 - color.a)
				elif isinstance(color, fife.Color):
					fife_to = color
				else:
					raise TypeError('Unknown color `%s` as attribute `%s`: '
						'Expected either fife.Color or horizons.util.Color.'
						% (color, to_color))
			self.change_color(fife_from, fife_to)

	def add_overlay(self, overlay_name):
		"""Creates color overlay recoloring the area defined in *overlay_set*

		and adds it to fife instance.
		"""
		all_action_sets = ActionSetLoader.get_sets()
		try:
			self.overlay_set = all_action_sets[self.action_set][overlay_name]
		except KeyError:
			self.log.warning(
				'Could not find overlay action set `%s` defined for object '
				'`%s` with id `%s`. Not adding overlay for this action.',
				overlay_name, self.instance, self.identifier)
			return

		if self.fife_instance.isColorOverlay(self.identifier):
			self.remove_overlay()

		for rotation, frames in self.overlay_set.iteritems():
			ov_anim = fife.Animation.createAnimation()
			for frame_img, frame_length in frames.iteritems():
				pic = horizons.globals.fife.imagemanager.load(frame_img)
				frame_milliseconds = int(frame_length * 1000)
				ov_anim.addFrame(pic, frame_milliseconds)
			overlay = fife.OverlayColors(ov_anim)
			self.fife_instance.addColorOverlay(self.identifier, rotation, overlay)

	def change_color(self, from_color, to_color):
		"""Changes color of *from_color*ed area to *to_color*.

		color parameters: fife.Color objects
		"""
		for rotation in self.overlay_set:
			overlay = self.fife_instance.getColorOverlay(self.identifier, rotation)
			overlay.changeColor(from_color, to_color)

	def remove_overlay(self):
		"""Removes color overlay recoloring the *color*-colored area from fife instance.
		"""
		for rotation in self.overlay_set:
			self.fife_instance.removeColorOverlay(self.identifier, rotation)

	def load(self, db, worldid):
		super(ColorOverlayComponent, self).load(db, worldid)
		Scheduler().add_new_object(self.initialize, self, run_in=0)

	def remove(self):
		"""Removes all color overlays from the fife instance. """
		self.remove_overlay()
		super(ColorOverlayComponent, self).remove()


# If "old" FIFE version is detected (i.e. one without overlay support), silently disable.
if not hasattr(fife, 'OverlayColors'):
	class ColorOverlayComponent(Dummy):
		pass
