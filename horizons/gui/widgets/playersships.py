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

from horizons.constants import GAME_SPEED
from horizons.gui.widgets.statswidget import StatsWidget
from horizons.scheduler import Scheduler
from horizons.util import Callback
from horizons.util.python import decorators
from horizons.world.units.fightingship import FightingShip

class PlayersShips(StatsWidget):
	"""Widget that shows a list of the player's ships."""

	widget_file_name = 'ships_list.xml'

	def __init__(self, session):
		super(PlayersShips, self).__init__(session)
		Scheduler().add_new_object(Callback(self._refresh_tick), self, run_in = 1, loops = -1, loop_interval = GAME_SPEED.TICKS_PER_SECOND / 3)

	def refresh(self):
		super(PlayersShips, self).refresh()
		player = self.session.world.player
		self._clear_entries()
		self._gui.findChild(name = 'headline').text = _('%(player)s\'s ships') % {'player': self.session.world.player.name}

		sequence_number = 0
		events = {}
		for ship in self.session.world.ships:
			if ship.owner is player and ship.is_selectable:
				sequence_number += 1
				name_label = self._add_line_to_gui(ship, sequence_number)
				events['%s/mouseClicked' % name_label.name] = Callback(self._go_to_ship, ship)
		self._gui.mapEvents(events)
		self._content_vbox.adaptLayout()

	def _go_to_ship(self, ship):
		self.session.view.center(ship.position.x, ship.position.y)

	def _add_line_to_gui(self, ship, sequence_number):
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
		self._content_vbox.addChild(hbox)
		return ship_name

decorators.bind_all(PlayersShips)
