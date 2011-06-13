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

import os

from fife.extensions import pychan

from horizons.i18n import translate_widget
from horizons.util.python import decorators
import horizons.main

@decorators.cachedfunction
def get_gui_files_map():
	"""Returns a dictionary { basename : full_path } for all xml gui files in content/gui"""
	xml_files = {}
	for root, dirs, files in os.walk('content/gui'):
		files = filter(lambda s : s.endswith(".xml"), files)
		if files:
			for i in files:
				if i not in xml_files:
					xml_files[i] = os.path.join(root, i)
				else:
					print 'Another file by the name %s already exists. Please use unique names!' % i
	return xml_files


def load_uh_widget(filename, style=None, center_widget=False):
	"""Loads a pychan widget from an xml file and applies uh-specific modifications
	"""
	# load widget
	try:
		widget = pychan.loadXML(get_gui_files_map()[filename])
	except (IOError, ValueError), e:
		print 'PLEASE REPORT: invalid path', filename , 'in translation!', e
		raise

	# translate
	widget = translate_widget(widget, filename)

	if style:
		widget.stylize(style)
	# format headline
	for w in widget.findChildren():
		if w.name.startswith("headline") or \
		   w.name == "name":
			w.stylize('headline')
	if center_widget:
		widget.position_technique = "automatic" # "center:center"

	return widget

def get_res_icon(res):
        """Returns icons of a resource
        @param res: resource id
        @return: tuple: (icon_50_path, icon_disabled_path, icon_24_path, icon_16_path)"""
        ICON_PATH = 'content/gui/icons/resources/'
        icon_50 = ICON_PATH + '50/%03d.png' % res
        icon_disabled = ICON_PATH + '50/greyscale/%03d.png' % res
        icon_24 = ICON_PATH + '24/%03d.png' % res
        icon_16 = ICON_PATH + '16/%03d.png' % res
        return (icon_50, icon_disabled, icon_24, icon_16)


def create_resource_icon(res_id, db, size=50):
	"""Creates a pychan icon for a resource.
	@param res_id:
	@param db: dbreader for main db"""
	from horizons.gui.widgets.tooltip import TooltipIcon
	if size == 50:
		return TooltipIcon(tooltip=db.get_res_name(res_id), \
		                   image=get_res_icon(res_id)[0])
	elif size == 24:
		return TooltipIcon(tooltip=db.get_res_name(res_id), \
		                   image=get_res_icon(res_id)[2])
	elif size == 16:
		return TooltipIcon(tooltip=db.get_res_name(res_id), \
		                   image=get_res_icon(res_id)[3])
	else:
		return None

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
	menu.position_technique = "automatic" # "center:center"

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
		self[widgetname] = load_uh_widget(widgetname+'.xml', \
		                                  style=self.styles.get(widgetname),\
		                                  center_widget=self.center_widgets)

	def reload(self, widgetname):
		"""Reloads a widget"""
		if widgetname in self:
			del self[widgetname]
		# loading happens automatically on next access
