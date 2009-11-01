# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
import getpass

import horizons.main

from horizons.util import Callback, Color, random_map
from horizons.savegamemanager import SavegameManager

class SingleplayerMenu(object):
	def show_single(self, show = 'free_maps'):
		"""
		@param show: string, which type of games to show
		"""
		assert show in ('random', 'campaign', 'free_maps')
		self.hide()
		# reload since the gui is changed at runtime
		self.widgets.reload('singleplayermenu')
		self._switch_current_widget('singleplayermenu', center=True)
		eventMap = {
			'cancel'   : self.show_main,
			'okay'     : self.start_single,
		  'showCampaign' : Callback(self.show_single, show='campaign'),
		  'showRandom' : Callback(self.show_single, show='random'),
		  'showMaps' : Callback(self.show_single, show='free_maps')
		}
		# init gui for subcategory
		if show == 'random':
			del eventMap['showRandom']
			self.current.findChild(name="showRandom").marked = True
			to_remove = self.current.findChild(name="map_list_area")
			to_remove.parent.removeChild(to_remove)
			to_remove = self.current.findChild(name="choose_map_lbl")
			to_remove.parent.removeChild(to_remove)
			self.show_popup(_('Warning'), _('The random map features is still in active development. It is to be considered a pre testing version. Problems are to be expected.'))
		else:
			if show == 'free_maps':
				del eventMap['showMaps']
				self.current.findChild(name="showMaps").marked = True
				self.current.files, maps_display = SavegameManager.get_maps()
			else: # campaign
				del eventMap['showCampaign']
				self.current.findChild(name="showCampaign").marked = True
				self.current.files, maps_display = SavegameManager.get_scenarios()

			# get the map files and their display names
			self.current.distributeInitialData({ 'maplist' : maps_display, })
			if len(maps_display) > 0:
				# select first entry
				self.current.distributeData({ 'maplist' : 0, })

				if show == 'campaign': # update description for campaign
					from horizons.campaign import CampaignEventHandler, InvalidScenarioFileFormat
					def _update_description():
						"""Fill in description of selected scenario to label"""
						try:
							desc = CampaignEventHandler.get_description_from_file( self._get_selected_map() )
						except InvalidScenarioFileFormat, e:
							self._show_invalid_scenario_file_popup(e)
							return
						self.current.findChild(name="map_description").text = unicode( desc )
						self.current.findChild(name="map_description").parent.adaptLayout()
					self.current.findChild(name="maplist").capture(_update_description)
					_update_description()


		self.current.mapEvents(eventMap)

		self.current.distributeInitialData({ 'playercolor' : [ _(color.name) for color in Color ] })
		self.current.distributeData({
		  'playername': unicode(getpass.getuser()),
		  'playercolor': 0
		})
		self.current.show()
		self.on_escape = self.show_main

	def start_single(self):
		""" Starts a single player horizons. """
		assert self.current is self.widgets['singleplayermenu']
		game_data = {}
		game_data['playername'] = self.current.collectData('playername')
		if len(game_data['playername']) == 0:
			self.show_popup(_("Invalid player name"), _("You entered an invalid playername"))
			return
		game_data['playercolor'] = Color[self.current.collectData('playercolor')+1] # +1 cause list entries start with 0, color indexes with 1

		if self.current.collectData('showRandom'):
			map_file = random_map.generate_map()
		else:
			assert self.current.collectData('maplist') != -1
			map_file = self._get_selected_map()

		game_data['is_scenario'] = bool(self.current.collectData('showCampaign'))
		self.show_loading_screen()
		from horizons.campaign import InvalidScenarioFileFormat
		try:
			horizons.main.start_singleplayer(map_file, game_data)
		except InvalidScenarioFileFormat, e:
			self._show_invalid_scenario_file_popup(e)
			self.show_single(show = 'campaign')

	def _get_selected_map(self):
		"""Returns map file, that is selected in the maplist widget"""
		return self.current.files[ self.current.collectData('maplist') ]


	def _show_invalid_scenario_file_popup(self, exception):
		"""Shows a popup complaining about invalid scenario file.
		@param exception: InvalidScenarioFile exception instance"""
		self.show_popup(_("Invalid scenario file"), \
		                _("The selected file is not a valid scenario file.\nError message:\n") + \
		                unicode(str(exception)))
