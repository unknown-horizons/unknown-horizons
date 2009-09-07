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

import logging

import horizons.main
from horizons.scheduler import Scheduler

from horizons.gui.tabs import TabWidget, SettlerOverviewTab, InventoryTab
from building import BasicBuilding, SelectableBuilding
from buildable import BuildableSingle
from horizons.constants import RES, SETTLER, BUILDINGS
from horizons.world.building.collectingproducerbuilding import CollectingProducerBuilding
from horizons.world.production.production import SettlerProduction, SingleUseProduction
from horizons.command.building import Build

class SettlerRuin(BasicBuilding):
	"""Building that appears when a settler got unhappy. The building does nothing."""
	buildable_upon = True

class Settler(SelectableBuilding, BuildableSingle, CollectingProducerBuilding, BasicBuilding):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	log = logging.getLogger("world.building.settler")

	production_class = SettlerProduction

	tabs = (SettlerOverviewTab, InventoryTab)

	def __init__(self, x, y, owner, instance = None, level=0, **kwargs):
		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, level=level, **kwargs)
		self.__init(level, SETTLER.HAPPINESS_INIT_VALUE)
		self.run()

	def __init(self, level, happiness = None):
		self.level = level
		self.level_max = 1 # for now
		if happiness is not None:
			self.inventory.alter(RES.HAPPINESS_ID, happiness)
		self._update_level_data()
		self.last_tax_payed = 0

	@property
	def happiness(self):
		return self.inventory[RES.HAPPINESS_ID]

	def _update_level_data(self):
		"""Updates all settler-related data because of a level change"""
		# taxes, inhabitants
		self.tax_base, self.inhabitants_max = \
		    horizons.main.db("SELECT tax_income, inhabitants_max FROM settler.settler_level \
		   									 WHERE level=?", self.level)[0]
		if self.inhabitants > self.inhabitants_max: # crop settlers at level down
			self.inhabitants = self.inhabitants_max

		# consumption:
		# Settler productions are specified to be disabled by default in the db, so we can enable
		# them here per level.
		current_lines = self.get_production_lines()
		for (prod_line,) in horizons.main.db.cached_query("SELECT production_line \
							FROM settler.settler_production_line WHERE level = ?", self.level):
			if not self.has_production_line(prod_line):
				self.add_production_by_id(prod_line)
			# cross out the new lines from the current lines, so only the old ones remain
			if prod_line in current_lines:
				current_lines.remove(prod_line)
		for line in current_lines:
			# all lines, that were added here but are not used due to the current level
			self.remove_production_by_id(line)

	def run(self):
		"""Start regular tick calls"""
		interval_in_ticks = horizons.main.session.timer.get_ticks(SETTLER.TICK_INTERVAL)
		Scheduler().add_new_object(self.tick, self, runin=interval_in_ticks, \
																									 loops=-1)

	def tick(self):
		"""Here we collect the functions, that are called regularly."""
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
		if self.happiness > SETTLER.HAPPINESS_INHABITANTS_INCREASE_REQUIREMENT and \
			 self.inhabitants < self.inhabitants_max:
			self.inhabitants += 1
			changed = True
			self.log.debug("%s: inhabitants increase to %s", self, self.inhabitants)
		elif self.happiness < SETTLER.HAPPINESS_INHABITANTS_DECREASE_LIMIT and self.inhabitants > 1:
			self.inhabitants -= 1
			changed = True
			self.log.debug("%s: inhabitants decrease to %s", self, self.inhabitants)

		if changed:
			# see http://wiki.unknown-horizons.org/index.php/DD/Economy/Supplying_citizens_with_resources
			self.alter_production_time( 1 + (float(self.inhabitants)/10))
			self._changed()

	def level_check(self):
		"""Checks whether we should level up or down."""
		if self.happiness > SETTLER.HAPPINESS_LEVEL_UP_REQUIREMENT and \
			 self.level < self.level_max:
			# add a production line that gets the necessary upgrade material.
			# when the production finished, it calls level_up as callback.
			upgrade_material_prodline = horizons.main.db("SELECT production_line FROM upgrade_material \
																									 WHERE level = ?", self.level+1)[0][0]
			if self.has_production_line(upgrade_material_prodline):
				return # already waiting for res
			upgrade_material_production = SingleUseProduction(self.inventory, upgrade_material_prodline,
																							callback = self.level_up)
			# drive the car out of the garage to make space for the building material
			for res, amount in upgrade_material_production.get_consumed_resources().iteritems():
				self.inventory.add_resource_slot(res, abs(amount))
			self.add_production(upgrade_material_production)
			self.log.debug("%s: Waiting for material to upgrade from %s", self, self.level)
		elif self.happiness < SETTLER.HAPPINESS_LEVEL_DOWN_LIMIT:
			self.level_down()
			self._changed()

	def level_up(self):
		self.level += 1
		self.log.debug("%s: Leveling up to %s", self, self.level)
		self._update_level_data()
		# notify owner about new level
		self.owner.notify_settler_reached_level(self)
		# reset happiness value for new level
		self.inventory.alter(RES.HAPPINESS_ID, SETTLER.HAPPINESS_INIT_VALUE - self.happiness)

	def level_down(self):
		if self.level == 0: # can't level down any more
			# remove when this function is done
			Scheduler().add_new_object(self.remove, self)
			# replace this building with a ruin
			command = Build(BUILDINGS.SETTLER_RUIN_CLASS, self.position.origin.x, \
			                self.position.origin.y, island=self.island, settlement=self.settlement)
			Scheduler().add_new_object(command.execute, command, 2)

			self.log.debug("%s: Destroyed by lack of happiness", self)
		else:
			self.level -= 1
			self._update_level_data()
			# reset happiness value for new level
			self.inventory.alter(RES.HAPPINESS_ID, SETTLER.HAPPINESS_INIT_VALUE - self.happiness)
			self.log.debug("%s: Level down to %s", self, self.level)

	def save(self, db):
		super(Settler, self).save(db)
		db("INSERT INTO settler(rowid, level, inhabitants) VALUES (?, ?, ?)", self.getId(), \
			 self.level, self.inhabitants)

	def load(self, db, building_id):
		super(Settler, self).load(db, building_id)
		level, self.inhabitants = \
				db("SELECT level, inhabitants FROM settler WHERE rowid=?", building_id)[0]
		self.__init(level)
		self.run()

	def __str__(self):
		return "%s(l:%s;ihab:%s;hap:%s)" % (super(Settler, self).__str__(), self.level, \
																				self.inhabitants, self.happiness)
