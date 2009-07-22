# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import pychan
import horizons.main

from pychan.widgets.common import UnicodeAttr
from horizons.i18n import load_xml_translated

class TooltipIcon(pychan.widgets.Icon):
	ATTRIBUTES = pychan.widgets.Icon.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, **kwargs):
		super(TooltipIcon, self).__init__(**kwargs)
		self.gui = load_xml_translated('tooltip.xml')
		self.gui.stylize('tooltip')
		self.gui.hide()
		self.mapEvents({
			self.name + '/mouseEntered' : pychan.tools.callbackWithArguments(horizons.main.ext_scheduler.add_new_object, self.show_tooltip, self, runin=0.5, loops=0),
			self.name + '/mouseExited' : self.hide_tooltip
			})

	def show_tooltip(self):
		if hasattr(self, 'tooltip'):
			self.label = self.gui.findChild(name='tooltip')
			self.label.text = self.tooltip.replace(r'\n', '\n')
			self.gui.position = (self._getParent().position[0] + self.position[0], self._getParent().position[1] + self._getParent().size[1])
			self.gui.show()
		else:
			pass

	def hide_tooltip(self):
		self.gui.hide()
		horizons.main.ext_scheduler.rem_call(self, self.show_tooltip)

class TooltipButton(pychan.widgets.ImageButton):
	ATTRIBUTES = pychan.widgets.ImageButton.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, **kwargs):
		super(TooltipButton, self).__init__(**kwargs)
		self.gui = load_xml_translated('tooltip.xml')
		self.gui.stylize('tooltip')
		self.gui.hide()
		self.mapEvents({
			self.name + '/mouseEntered' : pychan.tools.callbackWithArguments(horizons.main.ext_scheduler.add_new_object, self.show_tooltip, self, runin=0.5, loops=0),
			self.name + '/mouseExited' : self.hide_tooltip
			})

	def show_tooltip(self):
		if hasattr(self, 'tooltip'):
			self.label = self.gui.findChild(name='tooltip')
			self.label.text = self.tooltip.replace(r'\n', '\n')
			self.gui.position = (self._getParent().position[0] + self.position[0], self._getParent().position[1] + self.position[1] + self.size[1] + 15)
			self.gui.show()
		else:
			pass

	def hide_tooltip(self):
		self.gui.hide()
		horizons.main.ext_scheduler.rem_call(self, self.show_tooltip)

