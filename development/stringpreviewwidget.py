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

from horizons.gui.util import load_uh_widget
from horizons.util.yamlcache import YamlCache
from horizons.savegamemanager import SavegameManager
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.widgets.logbook import LogBook
from horizons.gui.windows import Window, WindowManager
from horizons.scheduler import Scheduler


class StringPreviewWidget(Window):
	"""Widget for testing Logbook strings.
	It provides a list of scenarios, of which the user can select one and display
	its strings in a logbook"""
	def __init__(self, session):
		super().__init__()
		self._init_gui(session)
		# allow for misc delayed initialization to finish before pausing
		Scheduler().add_new_object(session.speed_pause, self, 2)

	def show(self):
		self._gui.show()

	def _init_gui(self, session):
		self._gui = load_uh_widget("stringpreviewwidget.xml")
		self._gui.mapEvents({'load': self.load})
		self.scenarios = SavegameManager.get_scenarios()
		self.listbox = self._gui.findChild(name="scenario_list")
		self.listbox.items = self.scenarios[1]
		self.listbox.distributeData({'scenario_list': 0})
		self.listbox.capture(self.update_infos)

		self.statslabel = self._gui.findChild(name="stats")

		self.windows = WindowManager()
		self.logbook = LogBook(session, self.windows)
		self.logbook._gui.mapEvents({
			OkButton.DEFAULT_NAME: self.logbook.hide,
		})
		self.update_infos()

	def update_infos(self):
		"""Updates the status label while scrolling the scenario list. No up-
		date to logbook messages. Those are loaded after Load/Reload is clicked.
		"""
		scenario_file_path = self.scenarios[0][self.listbox.selected]
		data = YamlCache.load_yaml_data(open(scenario_file_path, 'r'))

		if 'metadata' in data:
			# no stats available => empty label
			stats = data['metadata'].get('translation_status', '')
		else:
			# Old scenario syntax version without metadata
			stats = data.get('translation_status', '')
		self.statslabel.text = str(stats)

	def load(self):
		"""Load selected scenario and show strings"""
		# remember current entry
		cur_entry = self.logbook.get_cur_entry()
		cur_entry = cur_entry if cur_entry is not None else 0
		self.logbook.clear()

		# get logbook actions from scenario file and add them to our logbook
		scenario_file_path = self.scenarios[0][self.listbox.selected]
		data = YamlCache.load_yaml_data(open(scenario_file_path, 'r'))
		events = data['events']
		for event in events:
			for action in event['actions']:
				if action['type'] in ('logbook', 'logbook'):
					self.logbook.add_captainslog_entry(action['arguments'], show_logbook=False)

		try:
			self.logbook.set_cur_entry(cur_entry)
		except ValueError:
			pass  # no entries
		self.logbook._redraw_captainslog()
		self.logbook.show()
