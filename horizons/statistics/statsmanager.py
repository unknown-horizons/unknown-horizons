# -*- coding: utf-8 -*-
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

import json
from multiprocessing import Process
from urllib2 import Request, urlopen
from horizons.constants import STATISTICS
from horizons.extscheduler import ExtScheduler

class StatsManager(object):

	action = "/upload"

	def __init__(self):
		self.url = STATISTICS.SERVER_URL
		self.sent_data = {}
		self.data = {}
		ExtScheduler().add_new_object(self.upload_data, self, 60, -1)
		
	def collect_data(self, data):
		self.data.update(data)

	def upload_data(self):
		"""
		@param action: action name from action_mapping that the data is to be sent to
		@param data: dict containing data that is sent to url json encoded"""
		if len(self.data) == 0:
			return
		try:
			p = Process(target=self.__upload_data, args=(self.data.copy(),))
			p.start()
		except:
			print "Error: unable to start process"
		# TODO Not threadsafe at all 
		self.sent_data.update(self.data)
		self.data.clear()

	def __upload_data(self, data):
		req = Request(self.url + self.action)
		req.add_header('Content-Type', 'application/json')
		urlopen(req, json.dumps(data))