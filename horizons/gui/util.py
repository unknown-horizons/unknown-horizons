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

from fife.extensions.pychan import loadXML
from fife.extensions.pychan.widgets import Icon, ImageButton, HBox

from horizons.i18n import translate_widget
from horizons.util.python import decorators
from horizons.util.python.callback import Callback

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

def get_happiness_icon_and_helptext(value, session):
	happiness_icon_path = "content/gui/icons/templates/happiness/"
	happiness_helptext = _("satisfied")
	sad = session.db.get_settler_happiness_decrease_limit()
	happy = session.db.get_settler_happiness_increase_requirement()
	if value <= sad:
		happiness_icon_path += "sad.png"
		happiness_helptext = _("sad")
	elif sad < value < happy:
		happiness_icon_path += "average.png"
	elif value >= happy:
		happiness_icon_path += "happy.png"
		happiness_helptext = _("happy")

	return happiness_icon_path, happiness_helptext

def load_uh_widget(filename, style=None, center_widget=False):
	"""Loads a pychan widget from an xml file and applies uh-specific modifications
	"""
	# load widget
	try:
		widget = loadXML(get_gui_files_map()[filename])
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
		elif w.name.startswith("uni_") or w.comment.startswith("uni_"):
			w.font = '16_black_unifont'
	if center_widget:
		widget.position_technique = "automatic" # "center:center"

	return widget

def get_res_icon_path(res, size=32, greyscale=False):
	"""Returns path of a resource icon or placeholder path, if icon does not exist.
	@param res: resource id. Pass 'placeholder' to get placeholder path.
	"""
	icon_path = 'content/gui/icons/resources/{size}/'.format(size=size)
	if greyscale:
		icon_path = icon_path + 'greyscale/'
	if res == 'placeholder':
		icon_path = icon_path + 'placeholder.png'
	else:
		icon_path = icon_path + '{res:03d}.png'.format(res=res)
	try:
		Icon(image=icon_path)
	except RuntimeError: # ImageManager: image not found, use placeholder or die
		if res == 'placeholder':
			raise Exception('Image not found: {icon_path}'.format(icon_path=icon_path))
		else:
			print '[WW] Image not found: {icon_path}'.format(icon_path=icon_path)
			icon_path = get_res_icon_path('placeholder', size)
	return icon_path

def create_resource_icon(res_id, db):
	"""Creates a pychan Icon for a resource. Helptext is set to name of *res_id*.
	@param res_id: resource id
	@param db: dbreader for main db"""
	widget = Icon(image=get_res_icon_path(res_id))
	widget.helptext = db.get_res_name(res_id)
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
		self[widgetname] = load_uh_widget(widgetname+'.xml',
		                                  style=self.styles.get(widgetname),
		                                  center_widget=self.center_widgets)

	def reload(self, widgetname):
		"""Reloads a widget"""
		if widgetname in self:
			del self[widgetname]
		# loading happens automatically on next access


def create_resource_selection_dialog(on_click, inventory, db,
		widget='select_trade_resource.xml', res_filter=None, amount_per_line=None):
	"""Returns a container containing resource icons.
	@param on_click: called with resource id as parameter on clicks
	@param inventory: to determine fill status of resource slots
	@param db: main db instance
	@param widget: which xml file to use as a template. Default: tabwidget. Required
	               since the resource bar also uses this code (no tabs there though).
	@param res_filter: callback to decide which icons to use. Default: show all
	@param amount_per_line: how many resource icons per line. Default: try to fit layout
	"""
	from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
	dummy_icon_path = "content/gui/icons/resources/none_gray.png"

	dlg = load_uh_widget(widget)

	button_width = ImageFillStatusButton.CELL_SIZE[0] # used for dummy button
	vbox = dlg.findChild(name="resources")
	amount_per_line = amount_per_line or vbox.width // button_width
	# Add the zero element to the beginning that allows to remove the currently
	# sold/bought resource:
	resources = [0] + db.get_res(only_tradeable=True)
	current_hbox = HBox(name="hbox_0", padding=0)
	index = 1
	for res_id in resources:
		# don't show resources that are already in the list
		if res_filter is not None and not res_filter(res_id):
			continue
		# create button (dummy one or real one)
		if res_id == 0 or inventory is None:
			button = ImageButton( size=(button_width, button_width), name="resource_icon_00")
			button.up_image, button.down_image, button.hover_image = (dummy_icon_path,)*3
		else:
			amount = inventory[res_id]
			filled = int(float(inventory[res_id]) / float(inventory.get_limit(res_id)) * 100.0)
			button = ImageFillStatusButton.init_for_res(db, res_id,
			                                            amount=amount, filled=filled, uncached=True,
			                                            use_inactive_icon=False)
		# on click: add this res
		cb = Callback(on_click, res_id)
		if hasattr(button, "button"): # for imagefillstatusbuttons
			button.button.capture( cb )
		else:
			button.capture( cb )

		current_hbox.addChild(button)
		if index % amount_per_line == 0:
			vbox.addChild(current_hbox)
			box_id = index // amount_per_line
			current_hbox = HBox(name="hbox_%s" % box_id, padding=0)
		index += 1
	vbox.addChild(current_hbox)
	vbox.adaptLayout()

	return dlg
