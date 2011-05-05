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
from fife.extensions.pychan import widgets

class RouteConfig(object):
	"""
	Widget that allows configurating a ship's trading route 
	"""
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
		#self._gui.findChild(name='start_route').set_active()

	def stop_route(self):
		self.instance.route.disable()
		#self._gui.findChild(name='start_route').set_inactive()

	def toggle_route(self):
		if not self.instance.route.enabled:
			self.start_route()
		else:
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

	def remove_entry(self, entry):
		self.instance.route.disable()
		vbox = self._gui.findChild(name="left_vbox")
		position = self.widgets.index(entry)
		self.widgets.pop(position)
		self.instance.route.waypoints.pop(position)
		vbox.removeChild(entry)
		self.instance.route.enable()
		self.hide()
		self.show()
	
	def add_gui_entry(self, branch_office):
		vbox = self._gui.findChild(name="left_vbox")
		entry = load_xml_translated("route_entry.xml")

		label = entry.findChild(name="bo_name")
		label.text = unicode(branch_office.settlement.name)
		entry.mapEvents({
		  'delete_bo/mouseClicked' : Callback(self.remove_entry, entry)
		  })
		vbox.addChild(entry)
		self.widgets.append(entry)

	def append_bo(self):
		selected = self.listbox._getSelectedItem()
		if selected == None:
			return

		try:
			self.instance.route.append(self.branch_offices[selected], {4:-1})
			self.add_gui_entry(self.branch_offices[selected])
		except Exception:
			pass
		
		self.hide()
		self.show()

	def _init_gui(self):
		"""Initial init of gui."""
		self._gui = load_xml_translated("configure_route.xml")
		self.listbox = self._gui.findChild(name="branch_office_list")
		self.listbox._setItems(list(self.branch_offices))

		self.widgets=[]
		for entry in self.instance.route.waypoints:
			self.add_gui_entry(entry['branch_office'])
		# we want escape key to close the widget, what needs to be fixed here?
		#self._gui.on_escape = self.hide
		# needs to check the current state and set the button state afterwards
		if not self.instance.route.enabled:
			self._gui.findChild(name='start_route').set_inactive()

		self._gui.mapEvents({
		  'cancelButton' : self.hide,
		  'add_bo/mouseClicked' : self.append_bo,
		  'start_route/mouseClicked' : self.toggle_route
		  })
		self._gui.position_technique = "automatic" # "center:center"

