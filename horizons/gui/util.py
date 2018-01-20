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

import logging
import os
from io import BytesIO

from fife import fife
from fife.extensions.pychan import loadXML
from fife.extensions.pychan.widgets import Container, HBox, Icon

from horizons.gui.i18n import translate_widget
from horizons.gui.widgets.imagebutton import ImageButton
from horizons.i18n import gettext as T
from horizons.util.python import decorators
from horizons.util.python.callback import Callback


@decorators.cachedfunction
def get_gui_files_map():
	"""Returns a dictionary { basename : full_path }
	for all xml gui files in content/gui
	"""
	xml_files = {}
	for root, dirs, files in os.walk('content/gui/xml'):
		for f in files:
			if not f.endswith('.xml'):
				continue
			if f in xml_files:
				raise Exception('Another file by the name {name} already exists. '
								'Please use unique names!'.format(name=f))
			xml_files[f] = os.path.join(root, f)
	return xml_files


def get_happiness_icon_and_helptext(value, session):
	happiness_icon_path = "content/gui/icons/templates/happiness/"
	sad = session.db.get_lower_happiness_limit()
	happy = session.db.get_upper_happiness_limit()
	if value <= sad:
		happiness_icon_path += "sad.png"
		happiness_helptext = T("sad")
	elif sad < value < happy:
		happiness_icon_path += "average.png"
		happiness_helptext = T("satisfied")
	elif value >= happy:
		happiness_icon_path += "happy.png"
		happiness_helptext = T("happy")

	return happiness_icon_path, happiness_helptext


@decorators.cachedfunction
def get_widget_xml(filename):
	"""
	This function reads the given widget file's content and returns the XML.
	It is cached to avoid useless IO.
	"""
	with open(get_gui_files_map()[filename], 'rb') as open_file:
		return open_file.read()


def load_uh_widget(filename, style=None, center_widget=False):
	"""Loads a pychan widget from an xml file and applies uh-specific modifications
	"""
	# load widget
	try:
		widget = loadXML(BytesIO(get_widget_xml(filename)))
	except (IOError, ValueError) as error:
		log = logging.getLogger('gui')
		log.error('PLEASE REPORT: invalid path %s in translation!\n> %s', filename, error)
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
			w.font = 'unifont'
		elif w.name.startswith("transparent_"):
			w.stylize('transparent')
	if center_widget:
		widget.position_technique = "center:center"

	return widget


@decorators.cachedfunction
def get_res_icon_path(res, size=32, greyscale=False, full_path=True):
	"""Returns path of a resource icon or placeholder path, if icon does not exist.
	@param res: resource id. Pass 'placeholder' to get placeholder path.
	@param full_path: whether to return full icon path or a stub path suitable for ImageButton path=
	"""
	icon_path = 'content/gui/icons/resources/{size}/'.format(size=size)
	if greyscale:
		icon_path = icon_path + 'greyscale/'
	if res == 'placeholder':
		icon_path = icon_path + 'placeholder.png'
	else:
		icon_path = icon_path + '{res:03d}.png'.format(res=res)

	try:
		Icon(image=icon_path).hide()
	except fife.NotFound: # ImageManager: image not found, use placeholder or die
		if res == 'placeholder':
			raise Exception('Image not found: {icon_path}'.format(icon_path=icon_path))
		else:
			log = logging.getLogger('gui')
			log.warning('Image not found: %s', icon_path)
			icon_path = get_res_icon_path('placeholder', size)

	if full_path:
		return icon_path
	else:
		# remove 'content/gui/' and '.png'
		return icon_path[12:][:-4]


def create_resource_icon(res_id, db):
	"""Creates a pychan Icon for a resource. Helptext is set to name of *res_id*.
	@param res_id: resource id
	@param db: dbreader for main db"""
	widget = Icon(image=get_res_icon_path(res_id))
	widget.helptext = db.get_res_name(res_id)
	widget.scale = True
	return widget


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
	dummy_icon_path = "icons/resources/none_gray"

	dlg = load_uh_widget(widget)

	icon_size = ImageFillStatusButton.ICON_SIZE # used for dummy button
	cell_size = ImageFillStatusButton.CELL_SIZE
	button_width = cell_size[0]
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

		# on click: add this res
		cb = Callback(on_click, res_id)

		# create button (dummy one or real one)
		if res_id == 0 or inventory is None:
			reset_button = ImageButton(max_size=icon_size, name="resource_icon_00")
			reset_button.path = dummy_icon_path

			button = Container(size=cell_size)
			# add the "No Resource" image to the container, positioned in the top left
			button.addChild(reset_button)
			# capture a mouse click on the container. It's possible to click on the
			# image itself or into the empty area (below or to the right of the image)
			button.capture(cb, event_name="mouseClicked")
			button.name = "resource_{:d}".format(res_id)
		else:
			amount = inventory[res_id]
			filled = int(inventory[res_id] / inventory.get_limit(res_id) * 100)
			button = ImageFillStatusButton.init_for_res(db, res_id,
						                                amount=amount, filled=filled, uncached=True,
						                                use_inactive_icon=False, showprice=True)
			button.capture(cb, event_name="mouseClicked")
			button.name = "resource_{:d}".format(res_id)

		current_hbox.addChild(button)
		if index % amount_per_line == 0:
			vbox.addChild(current_hbox)
			box_id = index // amount_per_line
			current_hbox = HBox(name="hbox_{}".format(box_id), padding=0)
		index += 1
	vbox.addChild(current_hbox)
	vbox.adaptLayout()

	return dlg
