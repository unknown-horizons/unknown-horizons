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

import yaml

from horizons.i18n import load_xml_translated
from horizons.savegamemanager import SavegameManager
from horizons.gui.widgets.logbook import LogBook

class StringPreviewWidget(object):
	"""Widget for testing Logbook strings.
	It provides a list of scenarios, of which the user can select one and display
	its strings in a logbook"""
	def __init__(self):
		self._init_gui()

	def show(self):
		self._gui.show()

	def _init_gui(self):
		self._gui = load_xml_translated("stringpreviewwidget.xml")
		self._gui.mapEvents({ 'load' : self.load })
		self.scenarios = SavegameManager.get_scenarios()
		self.listbox = self._gui.findChild(name="scenario_list")
		self.listbox.items = self.scenarios[1]

		self.logbook = LogBook()

	def load(self):
		"""Load selected scenario and show strings"""
		if self.listbox.selected == -1:
			self._gui.findChild(name="hintlbl").text = u"you need to select sth in the list above"
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
					if action['type'] in ('logbook', 'logbook_w'):
						head= action['arguments'][0]
						msg = action['arguments'][1]
						self.logbook.add_entry(unicode(head), unicode(msg), show_logbook=False)

			self.logbook.set_cur_entry(cur_entry)
			self.logbook._redraw()
			self.logbook.show()







