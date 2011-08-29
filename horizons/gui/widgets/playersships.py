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

from fife.extensions.pychan import widgets

from horizons.util.gui import load_uh_widget
from horizons.scheduler import Scheduler
from horizons.util import Callback
from horizons.constants import GAME_SPEED
from horizons.util.python import decorators
from horizons.world.units.fightingship import FightingShip

class PlayersShips(object):
	"""
	Widget that shows a list of the player's ships.
	"""

	def __init__(self, session):
		super(PlayersShips, self).__init__()
		self.session = session
		self.player = None # fill this in on the first tick real refresh tick because it hasn't been initialised yet
		self._initialised = False
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in = 1)

	def _refresh_tick(self):
		if self.player is None:
			self.player = self.session.world.player
		if self._initialised:
			self.refresh()
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in = GAME_SPEED.TICKS_PER_SECOND / 3)

	def show(self):
		self._gui.show()

	def hide(self):
		self._gui.hide()

	def refresh(self):
		self._clear_entries()
		self._gui.findChild(name = 'headline').text = self.player.name + _('\'s ships')

		sequence_number = 0
		events = {}
		for ship in self.player.session.world.ships:
			if ship.owner is self.player and ship.is_selectable:
				sequence_number += 1
				name_label = self._add_ship_line_to_gui(self._gui.findChild(name = 'ships_vbox'), ship, sequence_number)
				events['%s/mouseClicked' % name_label.name] = Callback(self._go_to_ship, ship)
		self._gui.mapEvents(events)

	def _go_to_ship(self, ship):
		self.session.view.center(ship.position.x, ship.position.y)

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if not self._initialised:
			self._initialised = True
			self._init_gui()
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def _add_ship_line_to_gui(self, gui, ship, sequence_number):
		sequence_number_label = widgets.Label(name = 'sequence_number_%d' % ship.worldid)
		sequence_number_label.text = unicode(sequence_number)
		sequence_number_label.min_size = sequence_number_label.max_size = (15, 20)

		ship_name = widgets.Label(name = 'ship_name_%d' % ship.worldid)
		ship_name.text = unicode(ship.name)
		ship_name.min_size = ship_name.max_size = (110, 20)

		ship_type = widgets.Label(name = 'ship_type_%d' % ship.worldid)
		ship_type.text = unicode(ship.classname)
		ship_type.min_size = ship_type.max_size = (60, 20)

		weapons = widgets.Label(name = 'weapons_%d' % ship.worldid)
		if isinstance(ship, FightingShip):
			weapon_list = []
			for weapon_id, amount in sorted(ship.get_weapon_storage()):
				weapon_list.append('%d %s' % (amount, self.session.db.get_res_name(weapon_id)))
			if weapon_list:
				weapons.text = unicode(', '.join(weapon_list))
			else:
				weapons.text = _('None')
		else:
			weapons.text = _('N/A')
		weapons.min_size = weapons.max_size = (60, 20)

		health = widgets.Label(name = 'health_%d' % ship.worldid)
		health.text = unicode('%d/%d' % (ship.get_component('health').health, ship.get_component('health').max_health))
		health.min_size = health.max_size = (70, 20)

		status = widgets.Label(name = 'status_%d' % ship.worldid)
		status.text = ship.get_status()
		status.min_size = status.max_size = (320, 20)

		hbox = widgets.HBox()
		hbox.addChild(sequence_number_label)
		hbox.addChild(ship_name)
		hbox.addChild(ship_type)
		hbox.addChild(weapons)
		hbox.addChild(health)
		hbox.addChild(status)
		gui.addChild(hbox)
		gui.adaptLayout()
		return ship_name

	def _init_gui(self):
		self._gui = load_uh_widget("ships_list.xml")
		self._gui.mapEvents({
		  'cancelButton' : self.hide,
		  })
		self._gui.position_technique = "automatic"
		self.refresh()

	def _clear_entries(self):
		self._gui.findChild(name='ships_vbox').removeAllChildren()

decorators.bind_all(PlayersShips)
