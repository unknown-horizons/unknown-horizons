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

from horizons.gui.widgets.tooltip import TooltipIcon
from horizons.i18n import load_xml_translated
import horizons.main

def create_resource_icon(res_id, db):
	"""Creates a pychan icon for a resource.
	@param res_id:
	@param db: dbreader for main db"""
	return TooltipIcon(tooltip=db.get_res_name(res_id), \
	                   image=db.get_res_icon(res_id)[0])

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
	menu.position_technique="automatic" # "center:center"

def stylize_widget(widget, style=None, center_widget=False):
	"""Applies default uh style including further styling via arguments"""
	if style:
		widget.stylize(style)
	for w in widget.findChildren():
		if w.name.startswith("headline") or \
		   w.name is "name":
			w.stylize('headline')
	if center_widget:
		widget.position_technique = "automatic" # "center:center"
	return widget

class LazyWidgetsDict(dict):
	"""Dictionary for UH widgets. Loads widget on first access."""
	def __init__(self, styles, center_widgets=True, *args, **kwargs):
		"""
		@param styles: Dictionary, { 'widgetname' : 'stylename' }. parameter for stylize().
		@param center_widgets: Bool, whether to center the widgets
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
		"""
		We do styling before setting headlines to the default headline style.
		If you want your headlines to not be styled, rename them.
		"""
		widget = load_xml_translated(widgetname+'.xml')
		stylize_widget(widget, style=self.styles.get(widgetname), \
		               center_widget=self.center_widgets)
		self[widgetname] = widget

	def reload(self, widgetname):
		"""Reloads a widget"""
		if widgetname in self:
			del self[widgetname]
		# loading happens automatically on next access
