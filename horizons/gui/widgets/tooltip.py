# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

import re


from fife import fife
from fife.extensions.pychan.widgets import HBox, Icon, Label

import horizons.globals

from horizons.extscheduler import ExtScheduler
from horizons.gui.util import get_res_icon_path
from horizons.gui.widgets.container import AutoResizeContainer
from horizons.gui.widgets.icongroup import TooltipBG

class _Tooltip(object):
	"""Base class for pychan widgets overloaded with tooltip functionality"""

	LABEL_LEFT_RIGHT_MARGIN = 10
	# Left and right margin for the tooltips text, otherwise the text is over the border of the icon
	LABEL_TOP_BOTTOM_MARGIN = 5
	# Top and bottom margin for the tooltips text, otherwise the text is over the border of the icon
	MAX_LABEL_WIDTH = 145  # Width of the tooltip text before the text wraps
	# Find and replace horribly complicated elements that allow simple icons.
	icon_regexp = re.compile(r'\[\[Buildmenu((?: \d+\:\d+)+)\]\]')

	def init_tooltip(self):
		# the widget's parent's parent's ..... until the topmost
		self.topmost_widget = None
		self.gui = None
		self.bg = None
		self.label = None
		self.mapEvents({
			self.name + '/mouseEntered/tooltip' : self.position_tooltip,
			self.name + '/mouseExited/tooltip' : self.hide_tooltip,
			self.name + '/mouseMoved/tooltip' : self.position_tooltip,
			# TIP: the mousePressed event is especially useful when such as click
			# will trigger this tooltip's parent widget to be hidden (or destroyed), 
			# which hides this tooltip first before hides the parent widget. 
			# Otherwise the tooltip will show forever.
			self.name + '/mousePressed/tooltip' : self.hide_tooltip,

			# TODO: not sure if below are useful or not
			# self.name + '/mouseReleased/tooltip' : self.position_tooltip,
			# self.name + '/mouseDragged/tooltip' : self.hide_tooltip
			})
		self.tooltip_shown = False

	def __init_gui(self):
		self.gui = AutoResizeContainer()
		self.label = Label(position=(self.LABEL_LEFT_RIGHT_MARGIN, self.LABEL_TOP_BOTTOM_MARGIN))
		self.bg = TooltipBG()
		self.gui.addChildren(self.bg, self.label)

	def position_tooltip(self, event):
		if not self.helptext:
			return
		"""Calculates a nice position for the tooltip.
		@param event: mouse event from fife or tuple screenpoint
		"""
		# TODO: think about nicer way of handling the polymorphism here,
		# e.g. a position_tooltip_event and a position_tooltip_tuple
		where = event # fife forces this to be called event, but here it can also be a tuple
		if isinstance(where, tuple):
			x, y = where
		else:
			if where.getButton() == fife.MouseEvent.MIDDLE:
				return

			x, y = where.getX(), where.getY()

		if self.gui is None:
			self.__init_gui()

		widget_position = self.getAbsolutePos()

		# Sometimes, we get invalid events from pychan, it is probably related to changing the
		# gui when the mouse hovers on gui elements.
		# Random tests have given evidence to believe that pychan indicates invalid events
		# by setting the top container's position to 0, 0.
		# Since this position is currently unused, it can serve as invalid flag,
		# and dropping these events seems to lead to the desired placements
		def get_top(w):
			return get_top(w.parent) if w.parent else w
		top_pos = get_top(self).position
		if top_pos == (0, 0):
			return

		screen_width = horizons.globals.fife.engine_settings.getScreenWidth()
		self.gui.y = widget_position[1] + y + 5
		offset = x + 10
		# Hack to fix the problem with persistent tooltips. When the mouse is in the center of the button,
		# the tooltip will display, else it will disappear after 0.5 seconds
		# The bug is caused by pychan not capturing the mouseExited event
		if 10 < x and (self.width - 10) > x and 10 < y and (self.height - 10) > y:
			print x
			ExtScheduler().rem_all_classinst_calls(self)
		else:
			ExtScheduler().add_new_object(self.hide_tooltip, self, run_in=0.5, loops=-1)

		if (widget_position[0] + self.gui.size[0] + offset) > (screen_width / 2):
			# right screen edge, position to the left of cursor instead
			offset = x - self.gui.size[0] - 5
		self.gui.x = widget_position[0] + offset
		if not self.tooltip_shown:
			self.show_tooltip()
			self.tooltip_shown = True

	def show_tooltip(self):
		self.label.max_width = self.MAX_LABEL_WIDTH
		if not self.helptext:
			return
		if self.gui is None:
			self.__init_gui()

		# Specification looks like [[Buildmenu icon_index:amount (1:250 4:2 6:2)]]
		buildmenu_icons = self.icon_regexp.findall(unicode(self.helptext))
		# Remove the weird stuff before displaying text.
		tooltip_text = self.icon_regexp.sub('', unicode(self.helptext))

		if buildmenu_icons:
			self.populate_tooltip_icons(buildmenu_icons)
		# enable Textwrapping
		self.label.wrap_text = True
		# Finish up the actual tooltip (text, background panel amount, layout).
		# To display build menu icons, we need another empty (first) line.

		self.label.text = bool(buildmenu_icons) * '\n' + tooltip_text
		self.gui.adaptLayout()
		# self.bg.amount should be renamed to self.bg.y_tile_amount or something similar.
		# unfortunately there are several xml files that us amount and it would be a lot of work to fix is
		self.bg.amount = ((self.label.height / 18) - 1)
		# set the width of the icon to the textlabel width plus the margin
		self.bg.x_width_amount = (self.label.width + self.LABEL_LEFT_RIGHT_MARGIN * 2)
		self.gui.show()

		# add an event to constantly check whether the hovered widget is still there
		# if this is no longer there, dismiss the tooltip widget
		ExtScheduler().add_new_object(self.hide_tooltip, self, run_in=0.5, loops=-1)

	def populate_tooltip_icons(self, buildmenu_icons):
		hbox = HBox(position=(7, 5), padding=0)
		for spec in buildmenu_icons[0].split():
			(res_id, amount) = spec.split(':')
			resource_amount_label = Label(text=amount+'  ')
			icon = Icon(image=get_res_icon_path(int(res_id)), size=(16, 16))
			# For compatibility with FIFE 0.3.5 and older, also set min/max.
			icon.max_size = icon.min_size = (16, 16)
			hbox.addChildren(icon, resource_amount_label)
		hbox.adaptLayout()
		if hbox.width >= self.MAX_LABEL_WIDTH:
			self.label.max_width = hbox.width + 9
		return self.gui.addChild(hbox)

	def hide_tooltip(self, event=None):
		if self.gui is not None:
			self.gui.hide()
		# tooltip is hidden, no need to check any more
		ExtScheduler().rem_call(self, self.hide_tooltip)
		self.topmost_widget = None
		self.tooltip_shown = False
