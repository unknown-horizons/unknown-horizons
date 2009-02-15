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

class TradePost(object):
	"""This Class has to be inherited by every class that wishes to use BuySellWidget and trade with
	the free trader.
	"""
	def __init__(self):
		self.__init()
		
	def __init(self):
		self.buy_list = {} # dict of resources that are to be bought. { res_id: limit, .. }
		self.sell_list = {} # dict of resources that are to be sold.  { res_id: limit, .. }

	def save(self, db):
		super(TradePost, self).save(db)
		
		for resource, limit in self.buy_list.iteritems():
			assert limit is not None, "limit must not be none"
			db("INSERT INTO trade_buy(rowid, resource, trade_limit) VALUES(?, ?, ?)",
				 self.getId(), resource, limit)
			
		for resource, limit in self.sell_list.iteritems():
			assert limit is not None, "limit must not be none"
			db("INSERT INTO trade_sell(rowid, resource, trade_limit) VALUES(?, ?, ?)",
				 self.getId(), resource, limit)
	
	def load(self, db, worldid):
		super(TradePost, self).load(db, worldid)
		
		self.__init()
	
		for (res, limit) in db("SELECT resource, trade_limit FROM trade_buy WHERE rowid = ?", worldid):
			self.buy_list[res] = limit
			
		for (res, limit) in db("SELECT resource, trade_limit FROM trade_sell WHERE rowid = ?", worldid):
			self.sell_list[res] = limit
	
		