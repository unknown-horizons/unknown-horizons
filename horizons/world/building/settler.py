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

import logging

from horizons.scheduler import Scheduler

from horizons.gui.tabs import SettlerOverviewTab
from horizons.world.building.building import BasicBuilding, SelectableBuilding
from horizons.world.building.buildable import BuildableSingle
from horizons.constants import RES, BUILDINGS, GAME
from horizons.world.building.collectingproducerbuilding import CollectingProducerBuilding
from horizons.world.production.production import SettlerProduction, SingleUseProduction
from horizons.command.building import Build
from horizons.util import decorators
from horizons.world.pathfinding.pather import StaticPather
from horizons.constants import SETTLER

class SettlerRuin(BasicBuilding, BuildableSingle):
	"""Building that appears when a settler got unhappy. The building does nothing.

	NOTE: Inheriting from BuildableSingle is necessary, cause it's built via Build Command, which
	checks for buildability
	"""
	buildable_upon = True

class Settler(SelectableBuilding, BuildableSingle, CollectingProducerBuilding, BasicBuilding):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	log = logging.getLogger("world.building.settler")

	production_class = SettlerProduction

	tabs = (SettlerOverviewTab,)

	default_level_on_build = 0

	def __init__(self, x, y, owner, instance=None, **kwargs):
		kwargs['level'] = self.default_level_on_build # settlers always start in first level
		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, **kwargs)
		self.__init(self.__get_data("happiness_init_value"))
		self.run()
		# give the user a month (about 30 seconds) to build a market place in range
		if self.owner == self.session.world.player:
			Scheduler().add_new_object(self._check_market_place_in_range, self, Scheduler().get_ticks_of_month())

	def __init(self, happiness = None):
		self.level_max =  SETTLER.CURRENT_MAX_INCR # for now
		if happiness is not None:
			self.inventory.alter(RES.HAPPINESS_ID, happiness)
		self._update_level_data()
		self.last_tax_payed = 0

	def save(self, db):
		super(Settler, self).save(db)
		remaining_ticks = Scheduler().get_remaining_ticks(self, self._tick)
		db("INSERT INTO settler(rowid, inhabitants, remaining_ticks) VALUES (?, ?, ?)", \
		   self.worldid, self.inhabitants, remaining_ticks)

	def load(self, db, worldid):
		super(Settler, self).load(db, worldid)
		self.inhabitants, remaining_ticks = \
		    db("SELECT inhabitants, remaining_ticks FROM settler WHERE rowid=?", worldid)[0]

		self.__init()
		self.owner.notify_settler_reached_level(self)
		self.run(remaining_ticks)

	@property
	def happiness(self):
		return self.inventory[RES.HAPPINESS_ID]

	@property
	def name(self):
		level_name = self.session.db.get_settler_name(self.level)
		return (_(level_name)+' '+_(self._name)).title()

	def _update_level_data(self):
		"""Updates all settler-related data because of a level change"""
		# taxes, inhabitants
		self.tax_base = self.session.db.get_settler_tax_income(self.level)
		self.inhabitants_max = self.session.db.get_settler_inhabitants_max(self.level)
		if self.inhabitants > self.inhabitants_max: # crop settlers at level down
			self.inhabitants = self.inhabitants_max

		# consumption:
		# Settler productions are specified to be disabled by default in the db, so we can enable
		# them here per level.
		current_lines = self.get_production_lines()
		for (prod_line,) in self.session.db.get_settler_production_lines(self.level):
			if not self.has_production_line(prod_line):
				self.add_production_by_id(prod_line)
			# cross out the new lines from the current lines, so only the old ones remain
			if prod_line in current_lines:
				current_lines.remove(prod_line)
		for line in current_lines[:]: # iterate over copy for safe removal
			# all lines, that were added here but are not used due to the current level
			# NOTE: this contains the upgrade material production line
			self.remove_production_by_id(line)
		# update instance graphics
		self.update_action_set_level(self.level)

	def run(self, remaining_ticks=None):
		"""Start regular tick calls"""
		interval_in_ticks = self.session.timer.get_ticks(GAME.INGAME_TICK_INTERVAL)
		run_in = remaining_ticks if remaining_ticks is not None else interval_in_ticks
		Scheduler().add_new_object(self._tick, self, run_in=run_in, loops=-1, )

	def _tick(self):
		"""Here we collect the functions, that are called regularly (every "month")."""
		self.pay_tax()
		self.inhabitant_check()
		self.level_check()

	def pay_tax(self):
		"""Pays the tax for this settler"""
		# the money comes from nowhere, settlers seem to have an infinite amount of money.
		# see http://wiki.unknown-horizons.org/index.php/DD/Economy/Settler_taxing
		happiness_tax_modifier = (float(self.happiness)-50)/200 + 1
		taxes = self.tax_base * happiness_tax_modifier * self.inhabitants * self.settlement.tax_setting
		taxes = int(round(taxes))
		self.settlement.owner.inventory.alter(RES.GOLD_ID, taxes)
		self.last_tax_payed = taxes

		# decrease happiness
		happiness_decrease = taxes + self.tax_base + ((self.settlement.tax_setting-1)*10)
		happiness_decrease = int(round(happiness_decrease))
		self.inventory.alter(RES.HAPPINESS_ID, -happiness_decrease)
		self._changed()
		self.log.debug("%s: pays %s taxes, -happy: %s new happiness: %s", self, taxes, \
									 happiness_decrease, self.happiness)

	def inhabitant_check(self):
		"""Checks whether or not the population of this settler should increase or decrease"""
		changed = False
		if self.happiness > self.__get_data("happiness_inhabitants_increase_requirement") and \
			 self.inhabitants < self.inhabitants_max:
			self.inhabitants += 1
			changed = True
			self.log.debug("%s: inhabitants increase to %s", self, self.inhabitants)
		elif self.happiness < self.__get_data("happiness_inhabitants_decrease_limit") and \
		     self.inhabitants > 1:
			self.inhabitants -= 1
			changed = True
			self.log.debug("%s: inhabitants decrease to %s", self, self.inhabitants)

		if changed:
			# see http://wiki.unknown-horizons.org/index.php/DD/Economy/Supplying_citizens_with_resources
			self.alter_production_time( 1 + (float(self.inhabitants)/10))
			self._changed()

	def level_check(self):
		"""Checks whether we should level up or down."""
		if self.happiness > self.__get_data("happiness_level_up_requirement") and \
			 self.level < self.level_max:
			# add a production line that gets the necessary upgrade material.
			# when the production finished, it calls level_up as callback.
			upgrade_material_prodline = self.session.db.get_settler_upgrade_material_prodline(self.level+1)
			if self.has_production_line(upgrade_material_prodline):
				return # already waiting for res
			upgrade_material_production = SingleUseProduction(self.inventory, upgrade_material_prodline)
			upgrade_material_production.add_production_finished_listener(self.level_up)
			# drive the car out of the garage to make space for the building material
			for res, amount in upgrade_material_production.get_consumed_resources().iteritems():
				self.inventory.add_resource_slot(res, abs(amount))
			self.add_production(upgrade_material_production)
			self.log.debug("%s: Waiting for material to upgrade from %s", self, self.level)
		elif self.happiness < self.__get_data("happiness_level_down_limit"):
			self.level_down()
			self._changed()

	def level_up(self, production=None):
		# NOTE: production, is unused, but get's passed by the production code
		self.level += 1
		self.log.debug("%s: Leveling up to %s", self, self.level)
		self._update_level_data()
		# notify owner about new level
		self.owner.notify_settler_reached_level(self)
		# reset happiness value for new level
		self.inventory.alter(RES.HAPPINESS_ID, self.__get_data("happiness_init_value") - self.happiness)
		self._changed()

	def level_down(self):
		if self.level == 0: # can't level down any more
			# remove when this function is done
			Scheduler().add_new_object(self.remove, self, run_in=0)
			# replace this building with a ruin
			command = Build(BUILDINGS.SETTLER_RUIN_CLASS, self.position.origin.x, \
			                self.position.origin.y, island=self.island, settlement=self.settlement)
			Scheduler().add_new_object(command, command, run_in=0)

			self.log.debug("%s: Destroyed by lack of happiness", self)
			if self.owner == self.session.world.player:
				self.session.ingame_gui.message_widget.add(self.position.center().x, self.position.center().y, \
			                                           'SETTLERS_MOVED_OUT')
		else:
			self.level -= 1
			self._update_level_data()
			# reset happiness value for new level
			self.inventory.alter(RES.HAPPINESS_ID, self.__get_data("happiness_init_value") - self.happiness)
			self.log.debug("%s: Level down to %s", self, self.level)
			self._changed()

	def _check_market_place_in_range(self):
		"""Notifies the user via a message in case there is no market place in range"""
		for building in self.get_buildings_in_range():
			if building.id == BUILDINGS.MARKET_PLACE_CLASS:
				if StaticPather.get_path_on_roads(self.island, self, building) is not None:
					# a market place is in range
					return
		# no market place found
		self.session.ingame_gui.message_widget.add(self.position.origin.x, self.position.origin.y, \
		                                           'NO_MARKET_PLACE_IN_RANGE')

	def level_upgrade(self, lvl):
		"""Settlers only level up by themselves"""
		pass

	def __str__(self):
		try:
			return "%s(l:%s;ihab:%s;hap:%s)" % (super(Settler, self).__str__(), self.level, \
																				self.inhabitants, self.happiness)
		except AttributeError: # an attribute hasn't been set up
			return super(Settler, self).__str__()

	@decorators.cachedmethod
	def __get_data(self, key):
		"""Returns constant settler-related data from the db.
		The values are cached by python, so the underlying data must not change."""
		return int(
		  self.session.db("SELECT value from settler.balance_values WHERE name = ?", key)[0][0]
		  )
