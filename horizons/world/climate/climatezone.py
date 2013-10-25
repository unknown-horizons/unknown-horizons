# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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


class ClimateZone(object):
	
	yaml_data = None

	def __init__(self, zone_type):
		self.__init_to_type(zone_type)

	def __init_to_type(self, zone_type): 
		self.zone_type = zone_type
		data = self.yaml_data[zone_type]
		self.name = _(data['name'])
		self.default_resources = data['default_resources']
		self.possible_resources = data['possible_resources']
		

	def __str__(self):
		return self.name + "\n\tDefault Res: " + \
			str(self.default_resources) + "\n\tPossible Res: " + \
			str(self.possible_resources)
	
	