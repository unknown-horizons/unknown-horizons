# Copyright (C) 2012 The Unknown Horizons Team
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

from fife.extensions.pychan.widgets import ImageButton

from horizons.util import Callback
from horizons.util.gui import load_uh_widget

class PickBeltWidget(object):
	"""Base class for widget with sections behaving as pages"""
	sections = () # Tuple with widget name and Label
	widget_xml = '' # xml to load for the widget
	style = 'book'
	pickbelt_start_pos = (5, 150)
	page_pos = (185, 45)

	def __init__(self):
		self.page_widgets = {}
		self.dict_lt = {}
		self.dict_rt = {}
		self.widget = load_uh_widget(self.widget_xml, style=self.style)

		self.pickbelts_container_lt = self.widget.findChild(name="left_pickbelts")
		self.pickbelts_container_rt = self.widget.findChild(name="right_pickbelts")

		for i in range(len(self.sections)):
			self.page_widgets[i] = self.widget.findChild(name=self.sections[i][0])

		# Create the required pickbelts
		for side in ('lt', 'rt'):
			for i in range(len(self.sections)):
				pickbelt = ImageButton(is_focusable=False)
				pickbelt.name = self.sections[i][0] + '_' + side
				pickbelt.text = self.sections[i][1]
				pickbelt.font = "small_tooltip"
				pickbelt.position = (self.pickbelt_start_pos[0]+5*i, self.pickbelt_start_pos[1]+70*i)
				pickbelt.capture(Callback(self.update_view, i), event_name="mouseClicked")
				if side == 'lt':
					pickbelt.up_image='content/gui/images/background/pickbelt_l.png'
					self.pickbelts_container_lt.addChild(pickbelt)
					self.dict_lt[i] = pickbelt
				else:
					pickbelt.up_image='content/gui/images/background/pickbelt_r.png'
					self.pickbelts_container_rt.addChild(pickbelt)
					self.dict_rt[i] = pickbelt
		self.widget.show() # Hack to initially setup the pickbelts properly
		self.update_view()
		self.widget.hide() # Hack to initially setup the pickbelts properly

	def get_widget(self):
		return self.widget

	def update_view(self, number=0):
		for i in range(len(self.sections)):
			self.page_widgets[i].position = self.widget.size # Hack hide by position out of view
		self.page_widgets[number].position = self.page_pos # Show the selected page

		# Setup the pickbelts according to selection
		for i in range(len(self.sections)):
			self.pickbelts_container_lt.showChild(self.dict_lt[i])
			self.pickbelts_container_rt.showChild(self.dict_rt[i])

		for i in range(number+1, len(self.dict_lt)):
			if self.dict_lt[i].isVisible():
				self.pickbelts_container_lt.hideChild(self.dict_lt[i])

		for i in range(0, number+1):
			if self.dict_rt[i].isVisible():
				self.pickbelts_container_rt.hideChild(self.dict_rt[i])

class OptionsPickbeltWidget(PickBeltWidget):
	"""Widget for Options dialog with pickbelt style pages"""
	widget_xml = 'settings.xml'
	sections = (('graphics_settings', _(u'Graphics')), \
							('sound_settings', _(u'Sound')), \
							('game_settings', _(u'Game')))
