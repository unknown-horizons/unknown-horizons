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
	"""The TooltipIcon is a modified icon widget. It can be used in xml files like this:
	<TooltipIcon tooltip=""/>
	Used to display tooltip on hover on icons.
	Attributes same as Icon widget with addition of tooltip="text string to display"
	Use \\n for newline.
	"""
	ATTRIBUTES = pychan.widgets.Icon.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, tooltip = "", **kwargs):
		super(TooltipIcon, self).__init__(**kwargs)
		self.gui = horizons.main.gui.widgets['tooltip'] if hasattr(horizons.main, 'gui') else \
		    load_xml_translated('tooltip.xml') #HACK for display in main menu
		self.gui.hide()
		if tooltip != "":
			self.tooltip = unicode(tooltip)
		self.mapEvents({
			self.name + '/mouseEntered' : self.position_tooltip,
			self.name + '/mouseExited' : self.hide_tooltip,
			self.name + '/mousePressed' : self.hide_tooltip,
		  self.name + '/mouseMoved' : self.position_tooltip,
			self.name + '/mouseReleased' : self.position_tooltip,
			self.name + '/mouseDragged' : self.position_tooltip
			})
		self.tooltip_shown = False
		self.tooltip_items = []

	def position_tooltip(self, event):
		widget_position = self.getAbsolutePos()
		self.gui.position = (widget_position[0] + event.getX() + 5, widget_position[1] + event.getY() + 5) if (widget_position[0] + event.getX() +self.gui.size[0] + 5) <= horizons.main.settings.fife.screen.width else (widget_position[0] + event.getX() - self.gui.size[0] - 5, widget_position[1] + event.getY() + 5)
		if not self.tooltip_shown:
			horizons.main.ext_scheduler.add_new_object(self.show_tooltip, self, runin=0.3, loops=0)
			self.tooltip_shown = True
		else:
			self.gui.show()

	def show_tooltip(self):
		if hasattr(self, 'tooltip'):
			line_count = self.tooltip.count(r'\n')
			top_image = pychan.widgets.Icon(image='content/gui/images/background/tooltip_bg_top.png', position=(0, 0))
			self.gui.addChild(top_image)
			self.tooltip_items.append(top_image)
			for i in range(0, line_count):
				middle_image = pychan.widgets.Icon(image='content/gui/images/background/tooltip_bg_middle.png', position=(top_image.position[0], top_image.position[1] + 17 * (1 + i)))
				self.gui.addChild(middle_image)
				self.tooltip_items.append(middle_image)
			bottom_image = pychan.widgets.Icon(image='content/gui/images/background/tooltip_bg_bottom.png', position=(top_image.position[0], top_image.position[1] + 17 + 17 * (line_count)))
			self.gui.addChild(bottom_image)
			self.tooltip_items.append(bottom_image)
			label = pychan.widgets.Label(text=u"", position=(16, 8))
			label.text = self.tooltip.replace(r'\n', '\n')
			self.gui.addChild(label)
			self.gui.stylize('tooltip')
			self.tooltip_items.append(label)
			self.gui.size = (140, 17 * (2 + line_count))
			self.gui.show()
		else:
			pass

	def hide_tooltip(self):
		self.gui.hide()
		horizons.main.ext_scheduler.rem_call(self, self.show_tooltip)
		for i in self.tooltip_items:
			self.gui.removeChild(i)
		self.tooltip_items = []
		self.tooltip_shown = False

class TooltipButton(pychan.widgets.ImageButton):
	"""The TooltipButton is a modified image button widget. It can be used in xml files like this:
	<TooltipButton tooltip=""/>
	Used to display tooltip on hover on buttons.
	Attributes same as ImageButton widget with addition of tooltip="text string to display"
	Use \\n for newline.
	"""
	ATTRIBUTES = pychan.widgets.ImageButton.ATTRIBUTES + [UnicodeAttr('tooltip')]
	def __init__(self, tooltip = "", **kwargs):
		super(TooltipButton, self).__init__(**kwargs)
		self.gui = horizons.main.gui.widgets['tooltip'] if hasattr(horizons.main, 'gui') else load_xml_translated('tooltip.xml') #HACK for display in main menu
		self.gui.hide()
		if tooltip != "":
			self.tooltip = unicode(tooltip)
		self.mapEvents({
			self.name + '/mouseEntered' : self.position_tooltip,
			self.name + '/mouseExited' : self.hide_tooltip,
			self.name + '/mouseMoved' : self.position_tooltip,
			self.name + '/mousePressed' : self.hide_tooltip,
			self.name + '/mouseReleased' : self.position_tooltip,
			self.name + '/mouseDragged' : self.position_tooltip
			})
		self.tooltip_shown = False
		self.tooltip_items = []

	def position_tooltip(self, event=0):
		widget_position = self.getAbsolutePos()
		self.gui.position = (widget_position[0] + event.getX() + 5, widget_position[1] + event.getY() + 5) if (widget_position[0] + event.getX() +self.gui.size[0] + 5) <= horizons.main.settings.fife.screen.width else (widget_position[0] + event.getX() - self.gui.size[0] - 5, widget_position[1] + event.getY() + 5)
		if not self.tooltip_shown:
			horizons.main.ext_scheduler.add_new_object(self.show_tooltip, self, runin=0.3, loops=0)
			self.tooltip_shown = True
		else:
			self.gui.hide()
			self.gui.show()

	def show_tooltip(self):
		if hasattr(self, 'tooltip'):
			line_count = self.tooltip.count(r'\n')
			top_image = pychan.widgets.Icon(image='content/gui/images/background/tooltip_bg_top.png', position=(0, 0))
			self.gui.addChild(top_image)
			self.tooltip_items.append(top_image)
			for i in range(0, line_count):
				middle_image = pychan.widgets.Icon(image='content/gui/images/background/tooltip_bg_middle.png', position=(top_image.position[0], top_image.position[1] + 17*(1+i)))
				self.gui.addChild(middle_image)
				self.tooltip_items.append(middle_image)
			bottom_image = pychan.widgets.Icon(image='content/gui/images/background/tooltip_bg_bottom.png', position=(top_image.position[0], top_image.position[1] + 17 + 17*(line_count)))
			self.gui.addChild(bottom_image)
			self.tooltip_items.append(bottom_image)
			label = pychan.widgets.Label(text=u"", position=(16, 8))
			label.text = self.tooltip.replace(r'\n', '\n')
			self.gui.addChild(label)
			self.gui.stylize('tooltip')
			self.tooltip_items.append(label)
			self.gui.size = (140, 17 * (2 + line_count))
			self.gui.show()
		else:
			pass

	def hide_tooltip(self):
		self.gui.hide()
		horizons.main.ext_scheduler.rem_call(self, self.show_tooltip)
		for i in self.tooltip_items:
			self.gui.removeChild(i)
		self.tooltip_items = []
		self.tooltip_shown = False

