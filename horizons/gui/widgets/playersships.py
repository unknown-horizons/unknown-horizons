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

from fife.extensions.pychan import widgets

from horizons.gui.widgets.statswidget import StatsWidget
from fife.extensions.pychan.widgets import ImageButton
from horizons.util import Callback
from horizons.util.python import decorators
from horizons.world.units.fightingship import FightingShip
from horizons.component.healthcomponent import HealthComponent
from horizons.component.namedcomponent import NamedComponent
from horizons.component.selectablecomponent import SelectableComponent

class PlayersShips(StatsWidget):
	"""Widget that shows a list of the player's ships."""

	widget_file_name = 'ships_list.xml'

	def __init__(self, session):
		super(PlayersShips, self).__init__(session)

	def refresh(self):
		super(PlayersShips, self).refresh()
		player = self.session.world.player
		self._clear_entries()
		#xgettext:python-format
		self._gui.findChild(name = 'headline').text = _("Ships of {player}").format(player=self.session.world.player.name)

		sequence_number = 0
		events = {}
		for ship in sorted(self.session.world.ships, key = lambda ship: (ship.get_component(NamedComponent).name, ship.worldid)):
			if ship.owner is player and ship.has_component(SelectableComponent):
				sequence_number += 1
				name_label, rename_icon, status_label, status_position = \
				          self._add_line_to_gui(ship, sequence_number)
				events['%s/mouseClicked' % name_label.name] = Callback(self._go_to_ship, ship)
				cb = Callback(self.session.ingame_gui.show_change_name_dialog, ship)
				events['%s/mouseClicked' % rename_icon.name] = cb
				events['%s/mouseClicked' % status_label.name] = Callback(self._go_to_point, status_position)
		self._gui.mapEvents(events)
		self._content_vbox.adaptLayout()

	def _go_to_ship(self, ship):
		self._go_to_point(ship.position)

	def _go_to_point(self, point):
		self.session.view.center(point.x, point.y)

	def _add_line_to_gui(self, ship, sequence_number):
		sequence_number_label = widgets.Label(name = 'sequence_number_%d' % ship.worldid)
		sequence_number_label.text = unicode(sequence_number)
		sequence_number_label.min_size = sequence_number_label.max_size = (15, 20)

		ship_name = widgets.Label(name = 'ship_name_%d' % ship.worldid)
		ship_name.text = ship.get_component(NamedComponent).name
		ship_name.min_size = ship_name.max_size = (100, 20)

		from horizons.engine.pychan_util import RenameImageButton
		rename_icon = RenameImageButton(name = 'rename_%d' % ship.worldid)
		rename_icon.up_image = "content/gui/images/background/rename_feather_20.png"
		rename_icon.hover_image = "content/gui/images/background/rename_feather_20_h.png"
		rename_icon.helptext = _("Click to change the name of this ship")
		rename_icon.max_size = (20, 20) # (width, height)

		ship_type = widgets.Label(name = 'ship_type_%d' % ship.worldid)
		ship_type.text = ship.classname
		ship_type.min_size = ship_type.max_size = (60, 20)

		weapons = widgets.Label(name = 'weapons_%d' % ship.worldid)
		if isinstance(ship, FightingShip):
			weapon_list = []
			for weapon_id, amount in sorted(ship.get_weapon_storage()):
				weapon_list.append('%d %s' % (amount, self.session.db.get_res_name(weapon_id)))
			if weapon_list:
				weapons.text = u', '.join(weapon_list)
			else:
				#i18n There are no weapons equipped at the moment.
				weapons.text = _('None')
		else:
			weapons.text = _('N/A')
		weapons.min_size = weapons.max_size = (60, 20)

		health = widgets.Label(name = 'health_%d' % ship.worldid)
		health_component = ship.get_component(HealthComponent)
		health.text = u'%d/%d' % (health_component.health, health_component.max_health)
		health.min_size = health.max_size = (65, 20)

		status = widgets.Label(name = 'status_%d' % ship.worldid)
		status.text, status_position = ship.get_status()
		status.min_size = status.max_size = (320, 20)

		hbox = widgets.HBox()
		hbox.addChild(sequence_number_label)
		hbox.addChild(ship_name)
		hbox.addChild(rename_icon)
		hbox.addChild(ship_type)
		hbox.addChild(weapons)
		hbox.addChild(health)
		hbox.addChild(status)
		self._content_vbox.addChild(hbox)
		return (ship_name, rename_icon, status, status_position)

decorators.bind_all(PlayersShips)
