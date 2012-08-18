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

import logging
import math

from horizons.scheduler import Scheduler

from horizons.gui.tabs import SettlerOverviewTab
from horizons.world.building.building import BasicBuilding
from horizons.world.building.buildable import BuildableRect, BuildableSingle
from horizons.constants import RES, BUILDINGS, GAME, TIER
from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.world.production.production import SettlerProduction
from horizons.command.building import Build
from horizons.util import Callback
from horizons.util.pathfinding.pather import StaticPather
from horizons.command.production import ToggleActive
from horizons.component.storagecomponent import StorageComponent
from horizons.world.status import SettlerUnhappyStatus
from horizons.world.production.producer import Producer
from horizons.messaging import AddStatusIcon, RemoveStatusIcon, SettlerUpdate, SettlerInhabitantsChanged, UpgradePermissionsChanged


class SettlerRuin(BasicBuilding, BuildableSingle):
	"""Building that appears when a settler got unhappy. The building does nothing.

	NOTE: Inheriting from BuildableSingle is necessary, cause it's built via Build Command, which
	checks for buildability
	"""
	buildable_upon = True
	walkable = True


class Settler(BuildableRect, BuildingResourceHandler, BasicBuilding):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	log = logging.getLogger("world.building.settler")

	production_class = SettlerProduction

	tabs = (SettlerOverviewTab, )

	default_level_on_build = 0

	_max_increment_reached_notification_displayed = False # this could be saved

	def __init__(self, x, y, owner, instance=None, **kwargs):
		kwargs['level'] = self.__class__.default_level_on_build # settlers always start in first level
		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, **kwargs)

	def __init(self, loading=False, last_tax_payed=0):
		self.level_max = TIER.CURRENT_MAX # for now
		self._update_level_data(loading=loading, initial=True)
		self.last_tax_payed = last_tax_payed
		UpgradePermissionsChanged.subscribe(self._on_change_upgrade_permissions, sender=self.settlement)
		self._upgrade_production = None # referenced here for quick access

	def initialize(self):
		super(Settler, self).initialize()
		SettlerInhabitantsChanged.broadcast(self, self.inhabitants)
		happiness = self.__get_data("happiness_init_value")
		if happiness is not None:
			self.get_component(StorageComponent).inventory.alter(RES.HAPPINESS, happiness)
		if self.has_status_icon:
			self.get_component(StorageComponent).inventory.add_change_listener( self._update_status_icon )
		# give the user a month (about 30 seconds) to build a main square in range
		if self.owner.is_local_player:
			Scheduler().add_new_object(self._check_main_square_in_range, self, Scheduler().get_ticks_of_month())
		self.__init()
		self.run()

	def save(self, db):
		super(Settler, self).save(db)
		db("INSERT INTO settler(rowid, inhabitants, last_tax_payed) VALUES (?, ?, ?)",
		   self.worldid, self.inhabitants, self.last_tax_payed)
		remaining_ticks = Scheduler().get_remaining_ticks(self, self._tick)
		db("INSERT INTO remaining_ticks_of_month(rowid, ticks) VALUES (?, ?)",
		   self.worldid, remaining_ticks)

	def load(self, db, worldid):
		super(Settler, self).load(db, worldid)
		self.inhabitants, last_tax_payed = \
		    db("SELECT inhabitants, last_tax_payed FROM settler WHERE rowid=?", worldid)[0]
		remaining_ticks = \
		    db("SELECT ticks FROM remaining_ticks_of_month WHERE rowid=?", worldid)[0][0]
		self.__init(loading = True, last_tax_payed = last_tax_payed)
		self._load_upgrade_data(db)
		SettlerUpdate.broadcast(self, self.level, self.level)
		self.run(remaining_ticks)

	def _load_upgrade_data(self, db):
		"""Load the upgrade production and relevant stored resources"""
		upgrade_material_prodline = SettlerUpgradeData.get_production_line_id(self.level+1)
		if not self.get_component(Producer).has_production_line(upgrade_material_prodline):
			return

		self._upgrade_production = self.get_component(Producer)._get_production(upgrade_material_prodline)

		# readd the res we already had, they can't be loaded since storage slot limits for
		# the special resources aren't saved
		resources = {}
		for resource, amount in db.get_storage_rowids_by_ownerid(self.worldid):
			resources[resource] = amount

		for res, amount in self._upgrade_production.get_consumed_resources().iteritems():
			# set limits to what we need
			self.get_component(StorageComponent).inventory.add_resource_slot(res, abs(amount))
			if res in resources:
				self.get_component(StorageComponent).inventory.alter(res, resources[res])

		self._upgrade_production.add_production_finished_listener(self.level_up)
		self.log.debug("%s: Waiting for material to upgrade from %s", self, self.level)

	def _add_upgrade_production_line(self):
		"""
		Add a production line that gets the necessary upgrade material.
		When the production finishes, it calls upgrade_materials_collected.
		"""
		upgrade_material_prodline = SettlerUpgradeData.get_production_line_id(self.level+1)
		self._upgrade_production = self.get_component(Producer).add_production_by_id( upgrade_material_prodline )
		self._upgrade_production.add_production_finished_listener(self.level_up)

		# drive the car out of the garage to make space for the building material
		for res, amount in self._upgrade_production.get_consumed_resources().iteritems():
			self.get_component(StorageComponent).inventory.add_resource_slot(res, abs(amount))

		self.log.debug("%s: Waiting for material to upgrade from %s", self, self.level)



	def remove(self):
		SettlerInhabitantsChanged.broadcast(self, -self.inhabitants)

		UpgradePermissionsChanged.unsubscribe(self._on_change_upgrade_permissions, sender=self.settlement)
		super(Settler, self).remove()

	@property
	def upgrade_allowed(self):
		return self.session.world.get_settlement(self.position.origin).upgrade_permissions[self.level]

	def _on_change_upgrade_permissions(self, message):
		production = self._upgrade_production
		if production is not None:
			if production.is_paused() == self.upgrade_allowed:
				ToggleActive(self.get_component(Producer), production).execute(self.session, True)

	@property
	def happiness(self):
		difficulty = self.owner.difficulty
		result = int(round(difficulty.extra_happiness_constant + self.get_component(StorageComponent).inventory[RES.HAPPINESS] * difficulty.happiness_multiplier))
		return max(0, min(result, self.get_component(StorageComponent).inventory.get_limit(RES.HAPPINESS)))

	@property
	def capacity_utilisation(self):
		# this concept does not make sense here, so spare us the calculations
		return 1.0

	def _update_level_data(self, loading=False, initial=False):
		"""Updates all settler-related data because of a level change or as initialisation
		@param loading: whether called to set data after loading
		@param initial: whether called to set data initially
		"""
		# taxes, inhabitants
		self.tax_base = self.session.db.get_settler_tax_income(self.level)
		self.inhabitants_max = self.session.db.get_settler_inhabitants_max(self.level)
		self.inhabitants_min = self.session.db.get_settler_inhabitants_min(self.level)
		if self.inhabitants > self.inhabitants_max: # crop settlers at level down
			self.inhabitants = self.inhabitants_max

		# consumption:
		# Settler productions are specified to be disabled by default in the db, so we can enable
		# them here per level. Production data is save/loaded, so we don't need to do anything in that case
		if not loading:
			prod_comp = self.get_component(Producer)
			current_lines = prod_comp.get_production_lines()
			for prod_line in prod_comp.get_production_lines_by_level(self.level):
				if not prod_comp.has_production_line(prod_line):
					prod_comp.add_production_by_id(prod_line)
				# cross out the new lines from the current lines, so only the old ones remain
				if prod_line in current_lines:
					current_lines.remove(prod_line)
			for line in current_lines[:]: # iterate over copy for safe removal
				# all lines, that were added here but are not used due to the current level
				# NOTE: this contains the upgrade material production line
				prod_comp.remove_production_by_id(line)

		if not initial:
			# update instance graphics
			# only do it when something has actually change

			# TODO: this probably also isn't necessary on loading, but it's
			# not touched before the relase (2012.1)
			self.update_action_set_level(self.level)

	def run(self, remaining_ticks=None):
		"""Start regular tick calls"""
		interval = self.session.timer.get_ticks(GAME.INGAME_TICK_INTERVAL)
		run_in = remaining_ticks if remaining_ticks is not None else interval
		Scheduler().add_new_object(self._tick, self, run_in=run_in, loops=-1, loop_interval=interval)

	def _tick(self):
		"""Here we collect the functions, that are called regularly (every "month")."""
		self.pay_tax()
		self.inhabitant_check()
		self.level_check()

	def pay_tax(self):
		"""Pays the tax for this settler"""
		# the money comes from nowhere, settlers seem to have an infinite amount of money.
		# see http://wiki.unknown-horizons.org/index.php/DD/Economy/Settler_taxing

		# calc taxes http://wiki.unknown-horizons.org/w/Settler_taxing#Formulae
		happiness_tax_modifier = 0.5 + (float(self.happiness)/70.0)
		inhabitants_tax_modifier = float(self.inhabitants) / self.inhabitants_max
		taxes = self.tax_base * self.settlement.tax_settings[self.level] *  happiness_tax_modifier * inhabitants_tax_modifier
		real_taxes = int(round(taxes * self.owner.difficulty.tax_multiplier))

		self.settlement.owner.get_component(StorageComponent).inventory.alter(RES.GOLD, real_taxes)
		self.last_tax_payed = real_taxes

		# decrease happiness http://wiki.unknown-horizons.org/w/Settler_taxing#Formulae
		difference = 1.0 - self.settlement.tax_settings[self.level]
		happiness_decrease = 10 * difference - 6* abs(difference)
		happiness_decrease = int(round(happiness_decrease))
		# NOTE: this formula was actually designed for a different use case, where the happiness
		# is calculated from the number of available goods -/+ a certain tax factor.
		# to simulate the more dynamic, currently implemented approach (where every event changes
		# the happiness), we simulate discontent of taxes by this:
		happiness_decrease -= 6
		self.get_component(StorageComponent).inventory.alter(RES.HAPPINESS, happiness_decrease)
		self._changed()
		self.log.debug("%s: pays %s taxes, -happy: %s new happiness: %s", self, real_taxes,
									 happiness_decrease, self.happiness)

	def inhabitant_check(self):
		"""Checks whether or not the population of this settler should increase or decrease"""
		change = 0
		if self.happiness > self.session.db.get_settler_happiness_increase_requirement() and \
			 self.inhabitants < self.inhabitants_max:
			change = 1
			self.log.debug("%s: inhabitants increase to %s", self, self.inhabitants)
		elif self.happiness < self.session.db.get_settler_happiness_decrease_limit() and \
		     self.inhabitants > 1:
			change = -1
			self.log.debug("%s: inhabitants decrease to %s", self, self.inhabitants)

		if change != 0:
			# see http://wiki.unknown-horizons.org/w/Supply_citizens_with_resources
			self.get_component(Producer).alter_production_time( 6.0/7.0 * math.log( 1.5 * (self.inhabitants + 1.2) ) )
			self.inhabitants += change
			SettlerInhabitantsChanged.broadcast(self, change)
			self._changed()

	def level_check(self):
		"""Checks whether we should level up or down."""
		if self.happiness > self.__get_data("happiness_level_up_requirement") and \
		   self.inhabitants >= self.inhabitants_min:
			if self.level >= self.level_max:
				# max level reached already, can't allow an update
				if self.owner.is_local_player:
					if not self.__class__._max_increment_reached_notification_displayed:
						self.__class__._max_increment_reached_notification_displayed = True
						self.session.ingame_gui.message_widget.add(
							point=self.position.center(), string_id='MAX_INCR_REACHED')
				return
			if self._upgrade_production:
				return # already waiting for res

			self._add_upgrade_production_line()

			if not self.upgrade_allowed:
				ToggleActive(self.get_component(Producer), self._upgrade_production).execute(self.session, True)

		elif self.happiness < self.__get_data("happiness_level_down_limit") or \
		     self.inhabitants < self.inhabitants_min:
			self.level_down()
			self._changed()

	def level_up(self, production=None):
		"""Actually level up (usually called when the upgrade material has arrived)"""

		self._upgrade_production = None

		# just level up later that tick, it could disturb other code higher in the call stack

		def _do_level_up():
			self.level += 1
			self.log.debug("%s: Levelling up to %s", self, self.level)
			self._update_level_data()

			# Notify the world about the level up
			SettlerUpdate.broadcast(self, self.level, 1)

			# reset happiness value for new level
			self.get_component(StorageComponent).inventory.alter(RES.HAPPINESS, self.__get_data("happiness_init_value") - self.happiness)
			self._changed()

		Scheduler().add_new_object(_do_level_up, self, run_in=0)

	def level_down(self):
		if self.level == 0: # can't level down any more
			# replace this building with a ruin
			command = Build(BUILDINGS.SETTLER_RUIN, self.position.origin.x,
			                self.position.origin.y, island=self.island, settlement=self.settlement)

			Scheduler().add_new_object(
			  Callback.ChainedCallbacks(self.remove, Callback(command, self.owner)), # remove, then build new
			  self, run_in=0)

			self.log.debug("%s: Destroyed by lack of happiness", self)
			if self.owner.is_local_player:
				# check_duplicate: only trigger once for different settlers of a neighborhood
				self.session.ingame_gui.message_widget.add(point=self.position.center(),
			                                           string_id='SETTLERS_MOVED_OUT', check_duplicate=True)
		else:
			self.level -= 1
			self._update_level_data()
			# reset happiness value for new level
			self.get_component(StorageComponent).inventory.alter(RES.HAPPINESS, self.__get_data("happiness_init_value") - self.happiness)
			self.log.debug("%s: Level down to %s", self, self.level)
			self._changed()

			# Notify the world about the level down
			SettlerUpdate.broadcast(self, self.level, -1)

	def _check_main_square_in_range(self):
		"""Notifies the user via a message in case there is no main square in range"""
		if not self.owner.is_local_player:
			return # only check this for local player
		for building in self.get_buildings_in_range():
			if building.id == BUILDINGS.MAIN_SQUARE:
				if StaticPather.get_path_on_roads(self.island, self, building) is not None:
					# a main square is in range
					return
		# no main square found
		# check_duplicate: only trigger once for different settlers of a neighborhood
		self.session.ingame_gui.message_widget.add(point=self.position.origin,
		                                           string_id='NO_MAIN_SQUARE_IN_RANGE', check_duplicate=True)

	def level_upgrade(self, lvl):
		"""Settlers only level up by themselves"""
		pass

	def _update_status_icon(self):
		if self.has_status_icon:
			unhappy = self.happiness < self.__get_data("happiness_inhabitants_decrease_limit")
			# check for changes
			if unhappy and not hasattr(self, "_settler_status_icon"):
				self._settler_status_icon = SettlerUnhappyStatus(self) # save ref for removal later
				AddStatusIcon.broadcast(self, self._settler_status_icon)
			if not unhappy and hasattr(self, "_settler_status_icon"):
				RemoveStatusIcon.broadcast(self, self, SettlerUnhappyStatus)
				del self._settler_status_icon

	def __str__(self):
		try:
			return "%s(l:%s;ihab:%s;hap:%s)" % (super(Settler, self).__str__(), self.level,
																				self.inhabitants, self.happiness)
		except AttributeError: # an attribute hasn't been set up
			return super(Settler, self).__str__()

	#@decorators.cachedmethod TODO: replace this with a version that doesn't leak
	def __get_data(self, key):
		"""Returns constant settler-related data from the db.
		The values are cached by python, so the underlying data must not change."""
		return int(
		  self.session.db("SELECT value FROM balance_values WHERE name = ?", key)[0][0]
		  )



class SettlerUpgradeData(object):
	"""This is used as glue between the old upgrade system based on sqlite data used in a non-component environment
	and the current component version with data in yaml"""

	# basically, this is arbitrary as long as it's not the same as any of the regular
	# production lines of the settler. We reuse data that has arbitrarily been set earlier
	# to preserve savegame compatibility.
	production_line_ids = { 1 : 24, 2 : 35, 3: 23451, 4: 34512, 5: 45123 }

	def __init__(self, producer_component, upgrade_material_data):
		self.upgrade_material_data = upgrade_material_data

	def get_production_lines(self):
		d = {}
		for level, prod_line_id in self.__class__.production_line_ids.iteritems():
			d[prod_line_id] = self.get_production_line_data(level)
		return d

	def get_production_line_data(self, level):
		"""Returns production line data for the upgrade to this level"""
		prod_line_data = {
		  'time': 1,
		  'changes_animation' : 0,
		  'enabled_by_default' : False,
		  'save_statistics' : False,
		  'consumes' : self.upgrade_material_data[level]
		}
		return prod_line_data

	@classmethod
	def get_production_line_id(cls, level):
		"""Returns production line id for the upgrade to this level"""
		return cls.production_line_ids[level]

