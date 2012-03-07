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

from tabinterface import TabInterface
from horizons.util import Callback
from horizons.util.gui import load_uh_widget
from horizons.scheduler import Scheduler
from horizons.command.unit import SetStance
from horizons.world.component.healthcomponent import HealthComponent
from horizons.world.component.stancecomponent import *
from horizons.world.component.selectablecomponent import SelectableComponent

class SelectMultiTab(TabInterface):
	"""
	Tab shown when multiple units are selected
	"""
	max_row_entry_number = 3
	max_column_entry_number = 4
	def __init__(self, session = None, widget = 'overview_select_multi.xml', \
	             icon_path='content/gui/icons/tabwidget/common/inventory_%s.png'):
		super(SelectMultiTab, self).__init__(widget = widget)
		self.session = session
		self.init_values()

		self.button_up_image = icon_path % 'u'
		self.button_active_image = icon_path % 'a'
		self.button_down_image = icon_path % 'd'
		self.button_hover_image = icon_path % 'h'

		# keep track of units that have stance
		self.stance_unit_number = 0

		# keep local track of selected instances
		self.instances = []
		# keep track of number of instances per type
		self.type_number = {}

		self.helptext = _("Selected Units")
		for i in self.session.selected_instances:
			if hasattr(i, 'stance'):
				self.stance_unit_number += 1
			self.instances.append(i)
			if not i.has_remove_listener(Callback(self.on_instance_removed, i)):
				i.add_remove_listener(Callback(self.on_instance_removed, i))
			if not i.id in self.type_number:
				self.type_number[i.id] = 1
			else:
				self.type_number[i.id] += 1

		if self.stance_unit_number != 0:
			self.show_stance_widget()

		self._scheduled_refresh = False
		self.draw_selected_units_widget()

	def add_entry(self, entry):
		if self.column_number > self.max_column_entry_number - 1:
			self.column_number = 0
			self.row_number += 1
		if self.row_number >= 3:
			# TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
			# This crashes when more than 2 rows are needed.
			# There just aren't any hboxes in the xml.
			# TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
			self.row_number = 2
			return
		self.column_number += 1
		self.widget.findChild(name="hbox_%s" % self.row_number).addChild(entry.widget)
		self.entries.append(entry)

	def draw_selected_units_widget(self):
		self.entries = []
		self.row_number = 0
		self.column_number = 0
		# if only one type of units is selected draw individual widgets for selected units
		if len(self.type_number) == 1:
			for instance in self.instances:
				self.add_entry(UnitEntry([instance], False))
		else:
			entry_instances = {}
			for instance in self.instances:
				if instance.id not in entry_instances:
					entry_instances[instance.id] = [instance]
				else:
					entry_instances[instance.id].append(instance)
			for instances in entry_instances.values():
				self.add_entry(UnitEntry(instances))

	def hide_selected_units_widget(self):
		for entry in self.entries:
			entry.remove()
		for i in xrange(0, self.max_row_entry_number):
			self.widget.findChild(name="hbox_%s" % i).removeAllChildren()

	def schedule_unit_widget_refresh(self):
		if not self._scheduled_refresh:
			self._scheduled_refresh = True
			Scheduler().add_new_object(self.refresh_unit_widget, self, run_in = 0)

	def refresh_unit_widget(self):
		if self.instances:
			self._scheduled_refresh = False
			self.hide_selected_units_widget()
			self.draw_selected_units_widget()
			self.toggle_stance()
			self.widget.adaptLayout()
		else:
			# all units were destroyed
			self.hide_selected_units_widget()

	def on_instance_removed(self, instance):
		if hasattr(instance, 'stance'):
			self.stance_unit_number -= 1

		self.instances.remove(instance)
		if instance.has_remove_listener(Callback(self.on_instance_removed, instance)):
			instance.remove_remove_listener(Callback(self.on_instance_removed, instance))

		if self.widget.isVisible():
			# if all units die, hide the tab
			if not self.instances:
				self.session.ingame_gui.hide_menu()
				return

			# if one unit remains, show its menu
			if len(self.instances) == 1:
				self.session.ingame_gui.hide_menu()
				self.instances[0].get_component(SelectableComponent).show_menu()
				return

		self.type_number[instance.id] -= 1
		if self.type_number[instance.id] == 0:
			del self.type_number[instance.id]
			# if one type of units dies, schedule refresh
			self.schedule_unit_widget_refresh()

		# if one type of units is left, any removal would mean refresh
		if len(self.type_number) == 1:
			self.schedule_unit_widget_refresh()

		if self.stance_unit_number == 0:
			self.hide_stance_widget()

	def show_stance_widget(self):
		stance_widget = load_uh_widget('stancewidget.xml')
		self.widget.findChild(name='stance').addChild(stance_widget)
		self.toggle_stance()
		events = dict( (i.NAME, Callback(self.set_stance, i) ) for i in DEFAULT_STANCES )
		self.widget.mapEvents( events )

	def hide_stance_widget(self):
		self.widget.findChild(name='stance').removeAllChildren()

	def set_stance(self, stance):
		for i in self.instances:
			if hasattr(i, 'stance'):
				SetStance(i, stance).execute(i.session)
		self.toggle_stance()

	def toggle_stance(self):
		"""
		Toggles the stance, Assumes at least one stance unit is selected
		"""
		for stance in DEFAULT_STANCES:
			self.widget.findChild(name=stance.NAME).set_inactive()
		# get first unit stance
		stance_units = [u for u in self.instances if hasattr(u, "stance")]
		stance = stance_units[0].stance
		for unit in stance_units[1:]:
			if unit.stance != stance:
				# not all have the same stance, toggle none
				return
		self.widget.findChild(name = stance.NAME).set_active()

class UnitEntry(object):
	def __init__(self, instances, show_number = True):
		self.instances = instances
		self.widget = load_uh_widget("unit_entry_widget.xml")
		# get the icon of the first instance
		self.widget.findChild(name="unit_button").up_image = self.get_thumbnail_icon(instances[0].id)
		if show_number:
			self.widget.findChild(name="instance_number").text = unicode(str(len(self.instances)))
		# only two callbacks are needed so drop unwanted changelistener inheritance
		for i in instances:
			if not i.has_remove_listener(Callback(self.on_instance_removed, i)):
				i.add_remove_listener(Callback(self.on_instance_removed, i))
			health_component = i.get_component(HealthComponent)
			if not health_component.has_damage_dealt_listener(self.draw_health):
				health_component.add_damage_dealt_listener(self.draw_health)
		self.draw_health()

	def get_thumbnail_icon(self, id):
		"""
		Returns the name of the Thumbnail Icon for unit with id
		"""
		#TODO get a system for loading thumbnail by id
		return "content/gui/icons/unit_thumbnails/"+str(id)+".png"

	def on_instance_removed(self, instance):
		self.instances.remove(instance)
		if instance.has_remove_listener(Callback(self.on_instance_removed, instance)):
			instance.remove_remove_listener(Callback(self.on_instance_removed, instance))
		health_component = instance.get_component(HealthComponent)
		if health_component.has_damage_dealt_listener(self.draw_health):
			health_component.remove_damage_dealt_listener(self.draw_health)

		if self.instances:
			self.widget.findChild(name = "instance_number").text = unicode(len(self.instances))

	def draw_health(self, caller = None):
		health = 0
		max_health = 0
		for instance in self.instances:
			health_component = instance.get_component(HealthComponent)
			health += health_component.health
			max_health += health_component.max_health
		health_ratio = float(health) / max_health
		container = self.widget.findChild(name="main_container")
		health_bar = self.widget.findChild(name="health")
		health_bar.position = (health_bar.position[0], int((1 - health_ratio) * container.height))

	def remove(self):
		"""
		Clears all the listeners in instances
		"""
		for instance in self.instances:
			if instance.has_remove_listener(Callback(self.on_instance_removed, instance)):
				instance.remove_remove_listener(Callback(self.on_instance_removed, instance))
			health_component = instance.get_component(HealthComponent)
			if health_component.has_damage_dealt_listener(self.draw_health):
				health_component.remove_damage_dealt_listener(self.draw_health)

