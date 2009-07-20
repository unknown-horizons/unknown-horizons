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

import horizons.main

from abstractconsumer import AbstractConsumer

class Consumer(AbstractConsumer):
	"""Class used for buildings that need resources. A branch office is a Consumer, it collects
	resources and provides them to other classes(this is done by the Provider class).

	Has to be inherited by a building that also inherits from producer
	This includes e.g. lumberjack, weaver, storage

	TUTORIAL:
	Check out the __init() function now.
	"""
	def __init__(self, **kwargs):
		"""
		"""
		super(Consumer, self).__init__(**kwargs)
		self.__init()
		self.active_production_line = None if len(self._resources) == 0 else min(self._resources)

	def __init(self):
		"""Part of initiation that __init__() and load() share"""
		#Select all production lines for this building from the databas
		for (production_line,) in \
				horizons.main.db("SELECT rowid FROM data.production_line where %(type)s = ?" % \
										 {'type' : 'building' if self.object_type == 0 else 'unit'}, self.id):
			self._resources[production_line] = []
			# Now only add ressources whos value is <= 0 (keep or consume)
			for (res,) in \
					horizons.main.db("SELECT resource FROM data.production WHERE \
					production_line = ? AND amount <= 0 GROUP BY resource", production_line):
				self._resources[production_line].append(res)
		"""TUTORIAL:
		Check out the PrimaryProduction class now in horizons/world/production.py for further digging
		"""



	def save(self, db):
		super(Consumer, self).save(db)
		# insert active prodline if it isn't in the db
		if len(db("SELECT active_production_line FROM production WHERE rowid = ?", \
							self.getId())) == 0:
			db("INSERT INTO production(rowid, active_production_line) VALUES(?, ?)", \
				 self.getId(), self.active_production_line)

	def load(self, db, worldid):
		super(Consumer, self).load(db, worldid)
		self.__init()
		self.active_production_line = \
				db("SELECT active_production_line FROM production WHERE rowid = ?", worldid)[0][0]

	def get_consumed_res(self):
		"""Returns list of resources, that the consumer uses, without
		considering, if it currently needs them
		"""
		return [] if self.active_production_line is None else \
					 self._resources[self.active_production_line]
