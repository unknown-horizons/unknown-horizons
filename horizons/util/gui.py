# ###################################################
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

import os

from fife.extensions import pychan

from horizons.i18n import translate_widget
from horizons.util.python import decorators, Callback

@decorators.cachedfunction
def get_gui_files_map():
	"""Returns a dictionary { basename : full_path }
	for all xml gui files in content/gui
	"""
	xml_files = {}
	for root, dirs, files in os.walk('content/gui'):
		files = filter(lambda s : s.endswith(".xml"), files)
		if files:
			for i in files:
				if i not in xml_files:
					xml_files[i] = os.path.join(root, i)
				else:
					print u'Another file by the name {name} already exists. Please use unique names!'.format(name=i)
	return xml_files


def load_uh_widget(filename, style=None, center_widget=False):
	"""Loads a pychan widget from an xml file and applies uh-specific modifications
	"""
	# load widget
	try:
		widget = pychan.loadXML(get_gui_files_map()[filename])
	except (IOError, ValueError) as error:
		print u'PLEASE REPORT: invalid path {path} in translation! {error}'.format(path=filename, error=error)
		raise

	# translate
	widget = translate_widget(widget, filename)

	if style:
		widget.stylize(style)
	# format headline
	for w in widget.findChildren():
		if w.name.startswith("headline") or w.name == "name":
			w.stylize('headline')
		elif w.name.startswith("cjkv") or w.comment.startswith("cjkv"):
			w.font = '14_black_cjkv'
	if center_widget:
		widget.position_technique = "automatic" # "center:center"

	return widget

def get_res_icon(res):
	"""Returns icons of a resource
	@param res: resource id
	@return: tuple: (icon_50_path, icon_disabled_path, icon_24_path, icon_16_path, icon_32_path)
	"""
	ICON_PATH = 'content/gui/icons/resources/'
	icon_50 = ICON_PATH + '50/%03d.png' % res
	icon_disabled = ICON_PATH + '50/greyscale/%03d.png' % res
	icon_24 = ICON_PATH + '24/%03d.png' % res
	icon_16 = ICON_PATH + '16/%03d.png' % res
	icon_32 = ICON_PATH + '32/%03d.png' % res
	return (icon_50, icon_disabled, icon_24, icon_16, icon_32)


def create_resource_icon(res_id, db, size=50):
	"""Creates a pychan Icon for a resource.
	Returns None if size parameter is invalid (not in 16,24,50).
	@param res_id:
	@param db: dbreader for main db
	@param size: Size of icon in px. Valid: 16, 24, 50."""
	from fife.extensions.pychan.widgets import Icon
	if size == 50:
		return Icon(helptext=db.get_res_name(res_id),
		                   image=get_res_icon(res_id)[0])
	elif size == 24:
		return Icon(helptext=db.get_res_name(res_id),
		                   image=get_res_icon(res_id)[2])
	elif size == 16:
		return Icon(helptext=db.get_res_name(res_id),
		                   image=get_res_icon(res_id)[3])
	else:
		return None

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


def create_resource_selection_dialog(on_click, inventory, db, widget='select_trade_resource.xml', res_filter=None):
	"""Returns a container containing resource icons
	@param on_click: called with resource id as parameter on clicks
	@param inventory: to determine fill status of resource slots
	@param db: main db instance
	@param widget: which xml file to use as a template. Default: tabwidget. Required
	               since the resource bar also uses this code (no tabs there though).
	@param res_filter: callback to decide which icons to use. Default: show all
	"""
	from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
	from fife.extensions.pychan.widgets import ImageButton
	dummy_icon_path = "content/gui/icons/resources/none_gray.png"

	dlg = load_uh_widget(widget)

	button_width = ImageFillStatusButton.DEFAULT_BUTTON_SIZE[0] # used for dummy button
	vbox = dlg.findChild(name="resources")
	amount_per_line = vbox.width / button_width
	current_hbox = pychan.widgets.HBox(name="hbox_0", padding=0)
	index = 1
	resources = db.get_res(True)

	# Add the zero element to the beginning that allows to remove the currently
	# sold/bought resource
	for res_id in [0] + list(resources):
		# don't show resources that are already in the list
		if res_filter is not None and not res_filter(res_id):
			continue
		# create button (dummy one or real one)
		if res_id == 0:
			button = ImageButton( size=(button_width, button_width), name="resource_icon_00")
			button.up_image, button.down_image, button.hover_image = (dummy_icon_path,)*3
		else:
			amount = inventory[res_id]
			filled = int(float(inventory[res_id]) / float(inventory.get_limit(res_id)) * 100.0)
			button = ImageFillStatusButton.init_for_res(db, res_id,
			                                            amount=amount, filled=filled,
			                                            use_inactive_icon=False)

		# on click: add this res
		cb = Callback(on_click, res_id)
		if hasattr(button, "button"): # for imagefillstatusbuttons
			button.button.capture( cb )
		else:
			button.capture( cb )

		current_hbox.addChild(button)
		if index % amount_per_line == 0 and index is not 0:
			vbox.addChild(current_hbox)
			current_hbox = pychan.widgets.HBox(name="hbox_%s" % (index / amount_per_line),
			                                   padding=0)
		index += 1
	#	current_hbox.addSpacer(pychan.widgets.layout.Spacer) #TODO: proper alignment
	vbox.addChild(current_hbox)
	vbox.adaptLayout()

	return dlg