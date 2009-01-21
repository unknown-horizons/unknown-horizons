# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

from building import Building, Selectable
from game.world.consumer import Consumer
from game.gui.tabwidget import TabWidget
import game.main
from buildable import BuildableSingle
from game.util import WeakList
from random import randint

class Settler(Selectable, BuildableSingle, Consumer, Building):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	def __init__(self, x, y, owner, instance = None, level=1, **kwargs):
		self.level = level
		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, level=level, **kwargs)
		self.__init()
		self.run()

	def create_carriage(self):
		self.local_carriages.append(game.main.session.entities.units[8](self))
		## NOTE: unit 2 requires no roads, which makes testing easier. change to 8 for release.
		#self.local_carriages.append(game.main.session.entities.units[2](self))

	def __init(self):
		print self.id, "Settler debug, inhabitants_max:", self.inhabitants_max
		self.tax_income = game.main.db("SELECT tax_income FROM settler_level WHERE level=?", self.level)[0][0]
		print self.id, "Settler debug, tax_income:", self.tax_income
		self.inventory.limit = 1
		self.consumation = {}
		for (res, speed) in game.main.db("SELECT res_id, consume_speed FROM settler_consumation WHERE level = ?", self.level):
			self.consumation[res] = {'consume_speed': speed, 'consume_state': 0, 'consume_contentment': 0 , 'next_consume': game.main.session.timer.get_ticks(speed)/10}
			"""consume_speed: generel time a consumed good lasts, until a new ton has to be consumed. In seconds.
			consume_state: 0-10 state, on 10 a new good is consumed or contentment drops, if no new good is in the inventory.
			consume_contentment: 0-10 state, showing how fullfilled the wish for the specified good is.
			next_consume: nr. of ticks until the next consume state is set(speed in tps / 10)"""

	def run(self):
		game.main.session.scheduler.add_new_object(self.consume, self, loops=-1) # Check consumation every tick
		game.main.session.scheduler.add_new_object(self.pay_tax, self, runin=game.main.session.timer.get_ticks(30), loops=-1) # pay tax every 30 seconds
		game.main.session.scheduler.add_new_object(self.inhabitant_check, self, runin=game.main.session.timer.get_ticks(30), loops=-1) # Check if inhabitants in/de-crease
		self.contentment_max = len(self.consumation)*10 # TODO: different goods have to have different values

	def consume(self):
		"""Methode that handles the building's consumation. It is called every tick."""
		for (res, row) in self.consumation.iteritems():
			if row['next_consume'] > 0: # count down till next consume is scheduled
				row['next_consume'] -= 1
			else:
				if row['consume_state'] < 10:
					row['consume_state'] += 1 # count to 10 to simulate partly consuming a resource over time
				if row['consume_state'] == 10: # consume a resource if available
					if self.inventory[res] > 0:
						print self.id, 'Settler debug: consuming res:', res
						row['consume_state'] = 0
						self.inventory.alter(res, -1) # consume resource
						row['consume_contentment'] = 10
					else:
						if row['consume_contentment'] > 0:
							row['consume_contentment'] -= 1
				row['next_consume'] = game.main.session.timer.get_ticks(row["consume_speed"])/10

	def pay_tax(self):
		"""Pays the tax for this settler"""
		self.settlement.owner.inventory.alter(1,self.tax_income*self.inhabitants)
		print self.id, 'Settler debug: payed tax:', self.tax_income*self.inhabitants, 'new player gold:', self.settlement.owner.inventory[1]

	def inhabitant_check(self):
		"""Checks weather or not the population of this settler should increase or decrease or stay the same."""
		if sum([self.consumation[i]['consume_contentment'] for i in self.consumation]) == self.contentment_max:
			content = 1
		else:
			content = 0
		if self.inhabitants < self.inhabitants_max:
			addition = randint(-1,1) + content
			addition = min(self.inhabitants_max, max(1, self.inhabitants + addition)) - self.inhabitants
			self.inhabitants += addition
			self.settlement.add_inhabitants(addition)

	def _Consumer__init(self):
		"""Part of initiation that __init__() and load() share
		NOTE: This function is only for the consumer class, the settler class needs to be a consumer,
		but without production lines, which is why this has to be overwritten."""
		self._Consumer__resources = {0: []} #ugly work arround to work with current consumer implementation
		self.local_carriages = []

		from game.world.building.building import Building
		if isinstance(self, Building):
			self.radius_coords = self.position.get_radius_coordinates(self.radius)

		self._Consumer__collectors = WeakList()
		for (res,) in game.main.db("SELECT res_id FROM settler_consumation WHERE level = ?", self.level):
			print "Settler debug, res:", res
			self._Consumer__resources[0].append(res)

	def show_menu(self):
		game.main.session.ingame_gui.show_menu(TabWidget(2, object=self))

	def get_consumed_res(self):
		"""Returns list of resources, that the building uses, without
		considering, if it currently needs them
		"""
		return self._Consumer__resources[0]

	def save(self, db):
		super(Settler, self).save(db)
		db("INSERT INTO settler(rowid, level) VALUES (?, ?)", self.getId(), self.level)
		for (res, row) in self.consumation.iteritems():
			db("INSERT INTO settler_consume(settler_id, res, contentment, next_consume, consume_state) VALUES (?, ?, ?, ?, ?)", self.getId(), res, row['consume_contentment'], row['next_consume'], row['consume_state'])

	def load(self, db, building_id):
		self.level = db("SELECT level FROM settler WHERE rowid=?", building_id)[0][0]
		super(Settler, self).load(db, building_id)
		self.__init()
		for (res, contentment, next_consume, consume_state) in db("SELECT res, contentment, next_consume, consume_state FROM settler_consume WHERE settler_id=?", self.getId()):
			self.consumation[res]['consume_contentment'] = contentment
			self.consumation[res]['next_consume'] = next_consume
			self.consumation[res]['consume_state'] = consume_state
		self.run()