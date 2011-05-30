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
from horizons.util.python import decorators

class Mission(object):
	"""
	This class describes a general mission that an AI seeks to fulfil.
	"""

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, success_callback, failure_callback, session):
		super(Mission, self).__init__()
		self.success_callback = success_callback
		self.failure_callback = failure_callback
		self.session = session

	def report_success(self, msg):
		self.log.info('Mission success: ' + msg)
		self.success_callback(self, msg)

	def report_failure(self, msg):
		self.log.debug('Mission failure: ' + msg)
		self.failure_callback(self, msg)

decorators.bind_all(Mission)
