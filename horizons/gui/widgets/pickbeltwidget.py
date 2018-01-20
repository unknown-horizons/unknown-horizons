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

from horizons.gui.style import NOTHING
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import ImageButton, OkButton
from horizons.gui.windows import Window
from horizons.util.python.callback import Callback


class PickBeltWidget:
	"""Base class for widget with sections behaving as pages"""
	sections = () # Tuple with widget name and Label
	widget_xml = '' # xml to load for the widget
	pickbelt_start_pos = (5, 150)
	page_pos = (185, 45)

	def __init__(self):
		self.page_widgets = {}
		self.widget = load_uh_widget(self.widget_xml, center_widget=True)

		# Lists holding pickbelt ImageButtons, placed to the left/right of the book
		self.buttons = {'left': [], 'right': []}

		for i, (name, text) in enumerate(self.sections):
			self.page_widgets[i] = self.widget.findChild(name=name)

		# Create the required pickbelts
		for i, (name, text) in enumerate(self.sections):
			for side in self.buttons:
				pickbelt = ImageButton(text=text)
				pickbelt.name = '{}_{}'.format(name, side)
				pickbelt.path = 'images/background/pickbelt_{}'.format(side)
				pickbelt.font = "pickbelt"

				pickbelt.capture(Callback(self.update_view, i), event_name="mouseClicked")

				start_x, start_y = self.pickbelt_start_pos
				pickbelt.position = (start_x + 5 * i, start_y + 70 * i)

				container = self.widget.findChild(name="{}_pickbelts".format(side))
				container.addChild(pickbelt)
				self.buttons[side].append(pickbelt)

		self.widget.show() # Hack to initially setup the pickbelts properly
		self.update_view()
		self.widget.hide() # Hack to initially setup the pickbelts properly

	def get_widget(self):
		return self.widget

	def update_view(self, number=0):
		for page in self.page_widgets.values():
			page.hide()
		self.page_widgets[number].show()
		# Setup the pickbelts according to selection
		for belts in self.buttons.values():
			for belt in belts:
				belt.show()
		split = number + 1
		for belt in self.buttons['left'][split:] + self.buttons['right'][:split]:
			belt.hide()


class CreditsPickbeltWidget(PickBeltWidget, Window):
	"""Widget for credits dialog with pickbelt style pages"""
	widget_xml = 'credits.xml'
	sections = (
		('credits_team_2016', 'UH-Team New'),
		('credits_team_2015', 'UH-Team Old'),
		('credits_patchers', 'Patchers'),
		('credits_translators', 'Translators'),
		('credits_packagers', 'Packagers'),
		('credits_thanks', 'Thanks'),
	)

	def __init__(self, windows):
		Window.__init__(self, windows)
		PickBeltWidget.__init__(self)

		# Overwrite a few style pieces
		for box in self.widget.findChildren(name='box'):
			box.margins = (30, 0) # to get some indentation
			box.padding = 3
		for listbox in self.widget.findChildren(name='translators'):
			listbox.background_color = NOTHING

		self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()
