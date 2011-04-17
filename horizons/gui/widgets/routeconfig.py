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

from horizons.i18n import load_xml_translated
from horizons.util import Callback
from horizons.gui.utility import center_widget
from fife.extensions.pychan import widgets

class RouteConfig(object):

	def __init__(self, instance):
		self.instance = instance

		offices = instance.session.world.get_branch_offices()
		self.branch_offices = dict([ (bo.settlement.name, bo) for bo in offices ])
		if not hasattr(instance, 'route'):
			instance.create_route()

		self._init_gui()

	def show(self):
		self._gui.show()

	def hide(self):
		self._gui.hide()

#############################
	def start_route(self):
		self.instance.route.enable()
		self._gui.findChild(name='start_route').set_active()

	def stop_route(self):
		self.instance.route.disable()
		self._gui.findChild(name='start_route').set_inactive()

	def toggle_route(self):
		if True:
			self.start_route()
		if False:
			self.stop_route()
	# these three need to be fixed and expanded.
	# toggle* is planned to serve as callback, see _init_gui below
##############################

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def append_bo(self):
		selected = self.listbox._getSelectedItem()
		if selected == None:
			return
		vbox = self._gui.findChild(name="left_vbox")

		hbox = widgets.HBox()
		label = widgets.Label()
		label.text = selected
		hbox.addChild(label)

		self.instance.route.append(self.branch_offices[selected], {4:-1})

		vbox.addChild(hbox);
		self.hide()
		self.show()

	def _init_gui(self):
		"""Initial init of gui."""
		self._gui = load_xml_translated("configure_route.xml")
		self.listbox = self._gui.findChild(name="branch_office_list")
		self.listbox._setItems(list(self.branch_offices))

		vbox = self._gui.findChild(name="left_vbox")
		for entry in self.instance.route.waypoints:
			hbox = widgets.HBox()
			label = widgets.Label()
			label.text = unicode(entry['branch_office'].settlement.name)
			hbox.addChild(label)
			vbox.addChild(hbox)

		# we want escape key to close the widget, what needs to be fixed here?
		self._gui.on_escape = self.hide
		# needs to check the current state and set the button state afterwards
#		self._gui.findChild(name='start_route').set_inactive()
		self._gui.mapEvents({
		  'cancelButton' : self.hide,
		  'add_bo/mouseClicked' : self.append_bo,
		  'start_route/mouseClicked' : self.instance.route.enable,
#		  'start_route/mouseClicked' : self.toggle_route
		  })
		center_widget(self._gui)

