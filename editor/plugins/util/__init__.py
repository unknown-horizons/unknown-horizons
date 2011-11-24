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

import horizons.main

import os

def getUHPath():
	"""Stores the UH path"""
	def up(path):
		return os.path.split(path)[0]
	return up(up(os.path.abspath(horizons.main.__file__)))

buildingMap = {}

BUILDING_NAMESPACE = 'building'
GROUND_NAMESPACE = 'ground'

def getBuildingName(id):
	return buildingMap[id]

def addBuilding(id, name):
	buildingMap[id] = name

