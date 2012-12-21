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
import thread
from urllib2 import Request, urlopen
from horizons.constants import STATISTICS

class StatsManager(object):

	action_mapping = { 'gamestart': "/data/gamestart" }

	def __init__(self):
		self.url = STATISTICS.SERVER_URL


	def upload_data(self, action, data):
		"""
		@param action: action name from action_mapping that the data is to be sent to
		@param data: dict containing data that is sent to url json encoded"""
		# Create two threads as follows
		try:
			thread.start_new_thread( self.__upload_data, (action, data) )
		except:
			print "Error: unable to start thread"

	def __upload_data(self, action, data):
		req = Request(self.url + self.action_mapping[action])
		req.add_header('Content-Type', 'application/json')
		urlopen(req, json.dumps(data))