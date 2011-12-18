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

# Maps from ids to building names 
buildingMap = {}
# Maps from ids to ground tile names 
# TODO (MMB) remove static creation with dynamic creation from UH code, or change Map format
groundTileMap = { 0:'ts_deep0', 1:'ts_shallow0', 2:'ts_shallow-deep0', 3:'ts_grass0', 4:'ts_grass-beach0', 5:'ts_beach-shallow0', 6:'ts_beach0'};

# Namespaces
BUILDING_NAMESPACE = 'building'
GROUND_NAMESPACE = 'ground'

# Layers
GROUND_LAYER_NAME = "ground"
BUILDING_LAYER_NAME = "buildings"

def getBuildingName(id):
	return buildingMap[id]

def getBuildingId(name):
	__getIdFromName(name, buildingMap)

def addBuilding(id, name):
	buildingMap[id] = name
	
def getGroundTileName(id):
	return groundTileMap[id]	
	
def addGroundTile(id, name):
	groundTileMap[id] = name
	
def getGroundTileId(name):
	__getIdFromName(name, groundTileMap)
		
def __getIdFromName(name, map):
	for id, value in map.iteritems():
		if value == name:
			return id
