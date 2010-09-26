# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

from horizons.gui.widgets.tooltip import TooltipIcon
from horizons.i18n import load_xml_translated
import horizons.main

def create_resource_icon(res_id, db):
	"""Creates a pychan icon for a resource.
	@param res_id:
	@param db: dbreader for main db"""
	return TooltipIcon(tooltip=db.get_res_name(res_id).capitalize(), \
	                   image=db.get_res_icon(res_id)[0])

def center_widget(widget):
	"""Centers the widget in the parameter
	@param widget: Widget with properties width, height, x and y
	"""
	widget.x = int((horizons.main.fife.engine_settings.getScreenWidth() - widget.width) / 2)
	widget.y = int((horizons.main.fife.engine_settings.getScreenHeight() - widget.height) / 2)

def adjust_widget_black_background(widget):
	"""Resizes the black background container and centers the menu
	@param widget: Widget with black_underlay and menu containers
	"""
	black_underlay = widget.findChild(name='black_underlay')
	black_underlay.position = (0, 0)
	black_underlay.size = (horizons.main.fife.engine_settings.getScreenWidth(), horizons.main.fife.engine_settings.getScreenHeight())

	black_underlay_background = widget.findChild(name='black_underlay_background')
	black_underlay_background.size = (horizons.main.fife.engine_settings.getScreenWidth(), horizons.main.fife.engine_settings.getScreenHeight())

	menu = widget.findChild(name='menu')
	center_widget(menu)


class LazyWidgetsDict(dict):
	"""Dictionary for UH widgets. Loads widget on first access."""
	def __init__(self, styles, center_widgets=True, *args, **kwargs):
		"""
		@param styles: Dictionary, { 'widgetname' : 'stylename' }. parameter for stylize().
		@param center_widgets: wheter to center the widgets via center_widget()
		"""
		super(LazyWidgetsDict, self).__init__(*args, **kwargs)
		self.styles = styles
		self.center_widgets = center_widgets

	def __getitem__(self, widgetname):
		try:
			return dict.__getitem__(self, widgetname)
		except KeyError:
			self._load_widget(widgetname)
			return dict.__getitem__(self, widgetname)

	def _load_widget(self, widgetname):
		widget = load_xml_translated(widgetname+'.xml')
		if self.center_widgets:
			center_widget(widget)
		headline = widget.findChild(name='headline')
		if headline:
			headline.stylize('headline')
		if widgetname in self.styles:
			widget.stylize(self.styles[widgetname])
		self[widgetname] = widget

	def reload(self, widgetname):
		"""Reloads a widget"""
		if widgetname in self:
			del self[widgetname]
		# loading happens automatically on next access