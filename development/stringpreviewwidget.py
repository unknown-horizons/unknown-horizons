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

import yaml

from horizons.util.gui import load_uh_widget
from horizons.savegamemanager import SavegameManager
from horizons.gui.widgets.logbook import LogBook
from horizons.scheduler import Scheduler

class StringPreviewWidget(object):
	"""Widget for testing Logbook strings.
	It provides a list of scenarios, of which the user can select one and display
	its strings in a logbook"""
	def __init__(self, session):
		self._init_gui(session)
		# allow for misc delayed initialisation to finish before pausing
		Scheduler().add_new_object(session.speed_pause, self, 2)

	def show(self):
		self._gui.show()

	def _init_gui(self, session):
		self._gui = load_uh_widget("stringpreviewwidget.xml")
		self._gui.mapEvents({ 'load' : self.load })
		self.scenarios = SavegameManager.get_scenarios()
		self.listbox = self._gui.findChild(name="scenario_list")
		self.listbox.items = self.scenarios[1]
		self.listbox.capture(self.update_infos)

		self.statslabel = self._gui.findChild(name="stats")

		self.logbook = LogBook(session)

	def update_infos(self):
		"""Updates the status label while scrolling the scenario list. No up-
		date to logbook messages. Those are loaded after Load/Reload is clicked.
		"""
		scenario_file_path = self.scenarios[0][self.listbox.selected]
		data = yaml.load(open(scenario_file_path, 'r'))
		try:
			stats = data['translation_status']
		except KeyError as err:
			stats = '' # no translation stats available, display empty label
		self.statslabel.text = unicode(stats)

	def load(self):
		"""Load selected scenario and show strings"""
		if self.listbox.selected == -1:
			self._gui.findChild(name="hintlbl").text = u"Select a scenario first."
		else:
			self._gui.findChild(name="hintlbl").text = u""

			# remember current entry
			cur_entry = self.logbook.get_cur_entry()
			cur_entry = cur_entry if cur_entry is not None else 0
			self.logbook.clear()

			# get logbook actions from scenario file and add them to our logbook
			scenario_file_path = self.scenarios[0][self.listbox.selected]
			data = yaml.load(open(scenario_file_path, 'r'))
			events = data['events']
			for event in events:
				for action in event['actions']:
					if action['type'] in ('logbook', 'logbook'):
						self.logbook.add_captainslog_entry(action['arguments'], show_logbook=False)

			try:
				self.logbook.set_cur_entry(cur_entry)
			except ValueError:
				pass # no entries
			self.logbook._redraw_captainslog()
			self.logbook.show()







