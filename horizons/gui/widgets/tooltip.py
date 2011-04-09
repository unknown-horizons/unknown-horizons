# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import textwrap
from fife import fife
from fife.extensions import pychan
import horizons.main

from horizons.extscheduler import ExtScheduler
from fife.extensions.pychan.widgets.common import UnicodeAttr
from horizons.gui.widgets import ProgressBar

class _Tooltip(object):
	"""Base class for pychan widgets overloaded with tooltip functionality"""
	def init_tooltip(self, tooltip):
		self.gui = pychan.loadXML('content/gui/xml/ingame/widgets/tooltip.xml')
		self.gui.hide()
		self.tooltip = tooltip
		self.mapEvents({
			self.name + '/mouseEntered' : self.position_tooltip,
			self.name + '/mouseExited' : self.hide_tooltip,
			self.name + '/mousePressed' : self.hide_tooltip,
			self.name + '/mouseMoved' : self.position_tooltip,
			#self.name + '/mouseReleased' : self.position_tooltip,
			self.name + '/mouseDragged' : self.hide_tooltip
			})
		self.tooltip_shown = False
		self.tooltip_items = []

	def position_tooltip(self, event):
		if (event.getButton() == fife.MouseEvent.MIDDLE):
			return
		widget_position = self.getAbsolutePos()
		screen_width = horizons.main.fife.engine_settings.getScreenWidth()
		self.gui.y = widget_position[1] + event.getY() + 5
		if (widget_position[0] + event.getX() +self.gui.size[0] + 5) <= screen_width:
			self.gui.x = widget_position[0] + event.getX() + 5
		else:
			self.gui.x = widget_position[0] + event.getX() - self.gui.size[0] - 5
		if not self.tooltip_shown:
			ExtScheduler().add_new_object(self.show_tooltip, self, run_in=0.3, loops=0)
			self.tooltip_shown = True
		else:
			self.gui.show()

	def show_tooltip(self):
		if self.tooltip != "":
			translated_tooltip = _(self.tooltip)
			#HACK this looks better than splitting into several lines & joining
			# them. works because replace_whitespace in fill defaults to True:
			tooltip = textwrap.fill(translated_tooltip.replace(r'\n', 18*' '),18)
			line_count = len(tooltip.splitlines())-1
			top_image = pychan.widgets.Icon(image='content/gui/images/background/widgets/tooltip_bg_top.png', position=(0, 0))
			self.gui.addChild(top_image)
			self.tooltip_items.append(top_image)
			for i in range(0, line_count):
				middle_image = pychan.widgets.Icon(image='content/gui/images/background/widgets/tooltip_bg_middle.png', position=(top_image.position[0], top_image.position[1] + 17 * (1 + i)))
				self.gui.addChild(middle_image)
				self.tooltip_items.append(middle_image)
			bottom_image = pychan.widgets.Icon(image='content/gui/images/background/widgets/tooltip_bg_bottom.png', position=(top_image.position[0], top_image.position[1] + 17 + 17 * (line_count)))
			self.gui.addChild(bottom_image)
			self.tooltip_items.append(bottom_image)
			label = pychan.widgets.Label(text=u"", position=(10, 3))
			label.text = tooltip
			self.gui.addChild(label)
			self.gui.stylize('tooltip')
			self.tooltip_items.append(label)
			self.gui.size = (145, 17 * (2 + line_count))
			self.gui.show()

	def hide_tooltip(self):
		self.gui.hide()
		ExtScheduler().rem_call(self, self.show_tooltip)
		for i in self.tooltip_items:
			self.gui.removeChild(i)
		self.tooltip_items = []
		self.tooltip_shown = False


class TooltipIcon(_Tooltip, pychan.widgets.Icon):
	"""The TooltipIcon is a modified icon widget. It can be used in xml files like this:
	<TooltipIcon tooltip=""/>
	Used to display tooltip on hover on icons.
	Attributes same as Icon widget with addition of tooltip="text string to display".
	Use '\n' to force newline.
	"""
	ATTRIBUTES = pychan.widgets.Icon.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, tooltip = "", **kwargs):
		super(TooltipIcon, self).__init__(**kwargs)
		self.init_tooltip(tooltip)

class TooltipButton(_Tooltip, pychan.widgets.ImageButton):
	"""The TooltipButton is a modified image button widget. It can be used in xml files like this:
	<TooltipButton tooltip=""/>
	Used to display tooltip on hover on buttons.
	Attributes same as ImageButton widget with addition of tooltip="text string to display".
	Use '\n' to force newline.
	"""
	ATTRIBUTES = pychan.widgets.ImageButton.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, tooltip = "", **kwargs):
		super(TooltipButton, self).__init__(**kwargs)
		self.init_tooltip(tooltip)

class TooltipLabel(_Tooltip, pychan.widgets.Label):
	"""The TooltipButton is a modified label widget. It can be used in xml files like this:
	<TooltipLabel tooltip=""/>
	Used to display tooltip on hover on buttons.
	Attributes same as Label widget with addition of tooltip="text string to display".
	Use '\n' to force newline.
	"""
	ATTRIBUTES = pychan.widgets.Label.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, tooltip="", **kwargs):
		super(TooltipLabel, self).__init__(**kwargs)
		self.init_tooltip(tooltip)

class TooltipProgressBar(_Tooltip, ProgressBar):
	"""The TooltipProgressBar is a modified progress bar widget. It can be used in xml files like this:
	<TooltipProgressbar tooltip=""/>
	Used to display tooltip on hover on buttons.
	Attributes same as Label widget with addition of tooltip="text string to display".
	Use '\n' to force newline.
	"""
	ATTRIBUTES = pychan.widgets.Label.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, tooltip="", **kwargs):
		super(TooltipProgressBar, self).__init__(**kwargs)
		self.init_tooltip(tooltip)
