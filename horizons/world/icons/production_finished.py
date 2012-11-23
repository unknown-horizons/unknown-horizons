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

from horizons.gui.util import get_res_icon_path

class ProductionFinishedIcon(object):
	BACKGROUND = "content/gui/images/background/produced_notification.png"

	def __init__(self, resource, amount, instance, run, animation_steps):
		self.resource = resource
		self.amount = amount
		self.instance = instance
		self.run = run
		self.animation_steps = animation_steps

	def render(self, renderer, group, loc):
		"""Renders the Icon on the specified location"""

		# run[group] is used for the moving up animation
		# use -50 here to get some more offset in height
		bg_rel = fife.Point(0, -50 - self.run[group])
		rel = fife.Point(-14, -50 - self.run[group])
		self.run[group] += self.animation_steps

		bg_node = fife.RendererNode(loc, bg_rel)
		node = fife.RendererNode(loc, rel)

		bg_image = horizons.globals.fife.imagemanager.load(self.BACKGROUND)
		res_icon = horizons.globals.fife.imagemanager.load(get_res_icon_path(self.resource))
		font = horizons.globals.fife.pychanmanager.getFont('mainmenu')

		renderer.addImage(group, bg_node, bg_image)
		renderer.resizeImage(group, node, res_icon, 24, 24)
		renderer.addText(group, node, font, ' '*9 + '{amount:>2d}'.format(amount=self.amount))