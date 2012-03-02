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

from collections import defaultdict

class ProviderHandler(list):
	"""Class to keep track of providers of an area, especially an island.
	It acts as a data structure for quick retrieval of special properties, that only resource
	providers have.

	Precondition: Provider never change their provided resources."""

	def __init__(self):
		super(ProviderHandler, self).__init__()
		self.provider_by_resources = defaultdict(list)

	def append(self, provider):
		# NOTE: appended elements need to be removed, else there will be a memory leak
		for res in provider.provided_resources:
			self.provider_by_resources[res].append(provider)
		super(ProviderHandler, self).append(provider)

	def remove(self, provider):
		for res in provider.provided_resources:
			self.provider_by_resources[res].remove(provider)
		super(ProviderHandler, self).remove(provider)




