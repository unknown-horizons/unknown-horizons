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

###############################################################################
#
# == I18N DEV USE CASES: CHEATSHEET ==
#
# ** Refer to  development/copy_pofiles.sh  for help with building or updating
#    the translation files for Unknown Horizons.
#
###############################################################################
#
# WARNING: This file is generated automagically.
#          You need to update it to see changes to strings in-game.
#          DO NOT MANUALLY UPDATE THIS FILE (by editing strings).
#          The script to generate .pot templates calls the following:
# ./development/extract_strings_from_objects.py  horizons/i18n/objecttranslations.py
#
# NOTE: In string-freeze mode (shortly before releases, usually
#       announced in a meeting), updates to this file must not happen
#       without permission of the responsible translation admin!
#
###############################################################################

from horizons.constants import VERSION

object_translations = dict()

def set_translations():
	global object_translations
	object_translations = {

	"content/objects/buildings/alvearies.yaml" : {
		# name of buildings:alvearies
		"name"                        : _("Alvearies"),
		# tooltip_text of buildings:alvearies
		"tooltip_text"                : _("Keeps bees. Produces honeycombs used for confectionery. Needs a farm."),
		},

	"content/objects/buildings/bakery.yaml" : {
		# name of buildings:bakery
		"name"                        : _("Bakery"),
		# tooltip_text of buildings:bakery
		"tooltip_text"                : _("Consumes flour. Produces food."),
		},

	"content/objects/buildings/barracks.yaml" : {
		# name of buildings:barracks
		"name"                        : _("Barracks"),
		# tooltip_text of buildings:barracks
		"tooltip_text"                : _("Recruits units suitable for ground combat."),
		},

	"content/objects/buildings/blender.yaml" : {
		# name of buildings:blender
		"name"                        : _("Blender"),
		# tooltip_text of buildings:blender
		"tooltip_text"                : _("Produces condiments out of spices."),
		},

	"content/objects/buildings/boatbuilder.yaml" : {
		# name of buildings:boatbuilder
		"name"                        : _("Boat Builder"),
		# tooltip_text of buildings:boatbuilder
		"tooltip_text"                : _("Builds boats and small ships. Built on coast."),
		},

	"content/objects/buildings/brickyard.yaml" : {
		# name of buildings:brickyard
		"name"                        : _("Brickyard"),
		# tooltip_text of buildings:brickyard
		"tooltip_text"                : _("Turns clay into bricks."),
		},

	"content/objects/buildings/butchery.yaml" : {
		# name of buildings:butchery
		"name"                        : _("Butchery"),
		# tooltip_text of buildings:butchery
		"tooltip_text"                : _("Needs pigs or cattle. Produces food."),
		},

	"content/objects/buildings/cattlerun.yaml" : {
		# name of buildings:cattlerun
		"name"                        : _("Cattle Run"),
		# tooltip_text of buildings:cattlerun
		"tooltip_text"                : _("Raises cattle. Needs a farm."),
		},

	"content/objects/buildings/charcoalburning.yaml" : {
		# name of buildings:charcoalburning
		"name"                        : _("Charcoal Burning"),
		# tooltip_text of buildings:charcoalburning
		"tooltip_text"                : _("Burns a lot of boards."),
		},

	"content/objects/buildings/claydeposit.yaml" : {
		# name of buildings:claydeposit
		"name"                        : _("Clay Deposit"),
		},

	"content/objects/buildings/claypit.yaml" : {
		# name of buildings:claypit
		"name"                        : _("Clay Pit"),
		# tooltip_text of buildings:claypit
		"tooltip_text"                : _("Gets clay from deposit."),
		},

	"content/objects/buildings/cocoafield.yaml" : {
		# name of buildings:cocoafield
		"name"                        : _("Cocoa Field"),
		# tooltip_text of buildings:cocoafield
		"tooltip_text"                : _("Produces cocoa beans used for confectionery. Needs a farm."),
		},

	"content/objects/buildings/cornfield.yaml" : {
		# name of buildings:cornfield
		"name"                        : _("Corn Field"),
		# tooltip_text of buildings:cornfield
		"tooltip_text"                : _("Yields corn. Needs a farm."),
		},

	"content/objects/buildings/distillery.yaml" : {
		# name of buildings:distillery
		"name"                        : _("Distillery"),
		# tooltip_text of buildings:distillery
		"tooltip_text"                : _("Turns sugar into liquor."),
		},

	"content/objects/buildings/doctor.yaml" : {
		# name of buildings:doctor
		"name"                        : _("Doctor"),
		# tooltip_text of buildings:doctor
		"tooltip_text"                : _("Treats diseases. Consumes herbs."),
		},

	"content/objects/buildings/farm.yaml" : {
		# name of buildings:farm
		"name"                        : _("Farm"),
		# tooltip_text of buildings:farm
		"tooltip_text"                : _("Grows field crops and raises livestock."),
		},

	"content/objects/buildings/fireservice.yaml" : {
		# name of buildings:fireservice
		"name"                        : _("Fire Station"),
		# tooltip_text of buildings:fireservice
		"tooltip_text"                : _("Extinguishes fires."),
		},

	"content/objects/buildings/fishdeposit.yaml" : {
		# name of buildings:fishdeposit
		"name"                        : _("Fish Deposit"),
		},

	"content/objects/buildings/fishermanstent.yaml" : {
		# name of buildings:fishermanstent
		"name"                        : _("Fisherman's Tent"),
		# tooltip_text of buildings:fishermanstent
		"tooltip_text"                : _("Fishes the sea, produces food."),
		},

	"content/objects/buildings/herbary.yaml" : {
		# name of buildings:herbary
		"name"                        : _("Herbary"),
		# tooltip_text of buildings:herbary
		"tooltip_text"                : _("Produces herbs. Needs a farm."),
		},

	"content/objects/buildings/hunterstent.yaml" : {
		# name of buildings:hunterstent
		"name"                        : _("Hunter's Tent"),
		# tooltip_text of buildings:hunterstent
		"tooltip_text"                : _("Hunts wild forest animals, produces food."),
		},

	"content/objects/buildings/ironmine.yaml" : {
		# name of buildings:ironmine
		"name"                        : _("Iron Mine"),
		# tooltip_text of buildings:ironmine
		"tooltip_text"                : _("Gets iron ore from deposit."),
		},

	"content/objects/buildings/lookout.yaml" : {
		# name of buildings:lookout
		"name"                        : _("Lookout"),
		# tooltip_text of buildings:lookout
		"tooltip_text"                : _("Increases the player's sight."),
		},

	"content/objects/buildings/lumberjackcamp.yaml" : {
		# name_0 of buildings:lumberjackcamp
		"name_0"                      : _("Lumberjack Tent"),
		# name_1 of buildings:lumberjackcamp
		"name_1"                      : _("Lumberjack Hut"),
		# tooltip_text of buildings:lumberjackcamp
		"tooltip_text"                : _("Chops down trees and turns them into boards."),
		},

	"content/objects/buildings/mainsquare.yaml" : {
		# name of buildings:mainsquare
		"name"                        : _("Main Square"),
		# tooltip_text of buildings:mainsquare
		"tooltip_text"                : _("Supplies citizens with goods."),
		},

	"content/objects/buildings/mountain.yaml" : {
		# name of buildings:mountain
		"name"                        : _("Mountain"),
		},

	"content/objects/buildings/pastryshop.yaml" : {
		# name of buildings:pastryshop
		"name"                        : _("Pastry Shop"),
		# tooltip_text of buildings:pastryshop
		"tooltip_text"                : _("Produces all kinds of confectionery."),
		},

	"content/objects/buildings/pasture.yaml" : {
		# name of buildings:pasture
		"name"                        : _("Pasture"),
		# tooltip_text of buildings:pasture
		"tooltip_text"                : _("Raises sheep. Produces wool. Needs a farm."),
		},

	"content/objects/buildings/pavilion.yaml" : {
		# name of buildings:pavilion
		"name"                        : _("Pavilion"),
		# tooltip_text of buildings:pavilion
		"tooltip_text"                : _("Fulfills religious needs of sailors."),
		},

	"content/objects/buildings/pigsty.yaml" : {
		# name of buildings:pigsty
		"name"                        : _("Pigsty"),
		# tooltip_text of buildings:pigsty
		"tooltip_text"                : _("Raises pigs. Needs a farm."),
		},

	"content/objects/buildings/potatofield.yaml" : {
		# name of buildings:potatofield
		"name"                        : _("Potato Field"),
		# tooltip_text of buildings:potatofield
		"tooltip_text"                : _("Yields food. Needs a farm."),
		},

	"content/objects/buildings/ruinedtent.yaml" : {
		# name of buildings:ruinedtent
		"name"                        : _("Ruined Tent"),
		},

	"content/objects/buildings/saltponds.yaml" : {
		# name of buildings:saltponds
		"name"                        : _("Salt Ponds"),
		# tooltip_text of buildings:saltponds
		"tooltip_text"                : _("Evaporates salt. Built on sea coast."),
		},

	"content/objects/buildings/signalfire.yaml" : {
		# name of buildings:signalfire
		"name"                        : _("Signal Fire"),
		# tooltip_text of buildings:signalfire
		"tooltip_text"                : _("Allows the player to trade with the free trader."),
		},

	"content/objects/buildings/smeltery.yaml" : {
		# name of buildings:smeltery
		"name"                        : _("Smeltery"),
		# tooltip_text of buildings:smeltery
		"tooltip_text"                : _("Refines all kind of ores."),
		},

	"content/objects/buildings/spicefield.yaml" : {
		# name of buildings:spicefield
		"name"                        : _("Spice Field"),
		# tooltip_text of buildings:spicefield
		"tooltip_text"                : _("Grows spices. Needs a farm."),
		},

	"content/objects/buildings/stonemason.yaml" : {
		# name_2 of buildings:stonemason
		"name_2"                      : _("Stonemason"),
		# name_4 of buildings:stonemason
		"name_4"                      : _("Carver"),
		# tooltip_text of buildings:stonemason
		"tooltip_text"                : _("Carves stone tops into bricks."),
		},

	"content/objects/buildings/stonepit.yaml" : {
		# name of buildings:stonepit
		"name"                        : _("Stone Pit"),
		# tooltip_text of buildings:stonepit
		"tooltip_text"                : _("Gets stone from a mountain."),
		},

	"content/objects/buildings/storagetent.yaml" : {
		# name_0 of buildings:storagetent
		"name_0"                      : _("Storage Tent"),
		# name_1 of buildings:storagetent
		"name_1"                      : _("Storage Hut"),
		# tooltip_text of buildings:storagetent
		"tooltip_text"                : _("Extends stock and provides collectors."),
		},

	"content/objects/buildings/sugarfield.yaml" : {
		# name of buildings:sugarfield
		"name"                        : _("Sugar Field"),
		# tooltip_text of buildings:sugarfield
		"tooltip_text"                : _("Used in liquor production. Needs a farm."),
		},

	"content/objects/buildings/tavern.yaml" : {
		# name of buildings:tavern
		"name"                        : _("Tavern"),
		# tooltip_text of buildings:tavern
		"tooltip_text"                : _("Provides get-together."),
		},

	"content/objects/buildings/tent.yaml" : {
		# name_0 of buildings:tent
		"name_0"                      : _("Tent"),
		# name_1 of buildings:tent
		"name_1"                      : _("Hut"),
		# name_2 of buildings:tent
		"name_2"                      : _("House"),
		# name_3 of buildings:tent
		"name_3"                      : _("Stone house"),
		# name_4 of buildings:tent
		"name_4"                      : _("Estate"),
		# name_5 of buildings:tent
		"name_5"                      : _("Manor"),
		# tooltip_text of buildings:tent
		"tooltip_text"                : _("Houses your inhabitants."),
		},

	"content/objects/buildings/tobaccofield.yaml" : {
		# name of buildings:tobaccofield
		"name"                        : _("Tobacco Field"),
		# tooltip_text of buildings:tobaccofield
		"tooltip_text"                : _("Produces tobacco. Needs a farm."),
		},

	"content/objects/buildings/tobacconist.yaml" : {
		# name of buildings:tobacconist
		"name"                        : _("Tobacconist"),
		# tooltip_text of buildings:tobacconist
		"tooltip_text"                : _("Produces tobaccos out of tobacco."),
		},

	"content/objects/buildings/toolmaker.yaml" : {
		# name of buildings:toolmaker
		"name"                        : _("Toolmaker"),
		# tooltip_text of buildings:toolmaker
		"tooltip_text"                : _("Produces tools out of iron."),
		},

	"content/objects/buildings/trail.yaml" : {
		# name_0 of buildings:trail
		"name_0"                      : _("Trail"),
		# name_1 of buildings:trail
		"name_1"                      : _("Gravel Path"),
		# name_3 of buildings:trail
		"name_3"                      : _("Cobblestone Street"),
		# tooltip_text of buildings:trail
		"tooltip_text"                : _("Needed for collecting goods."),
		},

	"content/objects/buildings/tree.yaml" : {
		# name of buildings:tree
		"name"                        : _("Tree"),
		# tooltip_text of buildings:tree
		"tooltip_text"                : _("Provides lumber. Chopped down by lumberjacks."),
		},

	"content/objects/buildings/villageschool.yaml" : {
		# name of buildings:villageschool
		"name"                        : _("Village school"),
		# tooltip_text of buildings:villageschool
		"tooltip_text"                : _("Provides education."),
		},

	"content/objects/buildings/vineyard.yaml" : {
		# name of buildings:vineyard
		"name"                        : _("Vineyard"),
		# tooltip_text of buildings:vineyard
		"tooltip_text"                : _("Produces grapes for use in wine and confectionery. Needs a farm."),
		},

	"content/objects/buildings/vintner.yaml" : {
		# name of buildings:vintner
		"name"                        : _("Vintner"),
		# tooltip_text of buildings:vintner
		"tooltip_text"                : _("Produces wine out of grapes."),
		},

	"content/objects/buildings/warehouse.yaml" : {
		# name of buildings:warehouse
		"name"                        : _("Warehouse"),
		},

	"content/objects/buildings/weaverstent.yaml" : {
		# name of buildings:weaverstent
		"name"                        : _("Weaver's Hut"),
		# tooltip_text of buildings:weaverstent
		"tooltip_text"                : _("Turns lamb wool into cloth."),
		},

	"content/objects/buildings/windmill.yaml" : {
		# name of buildings:windmill
		"name"                        : _("Windmill"),
		# tooltip_text of buildings:windmill
		"tooltip_text"                : _("Grinds corn into flour."),
		},

	"content/objects/buildings/woodentower.yaml" : {
		# name of buildings:woodentower
		"name"                        : _("Wooden Tower"),
		# tooltip_text of buildings:woodentower
		"tooltip_text"                : _("Defends your settlement."),
		},

	"content/objects/gui_buildmenu/build_menu_per_increment.yaml" : {
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Companies"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Companies"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Companies"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Companies"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Fields"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Fields"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Fields"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Military"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Mining"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Residents and infrastructure"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Services"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Services"),
		# headline of gui_buildmenu:build_menu_per_increment
		"headline"                    : _("Services"),
		},

	"content/objects/gui_buildmenu/build_menu_per_type.yaml" : {
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Citizens"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Food"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Fortifications"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Infrastructure"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Military Service"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Mining"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Pioneers"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Residential"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Sea"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Services"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : _("Settlers"),
		# tab1_helptext of gui_buildmenu:build_menu_per_type
		"tab1_helptext"               : _("Residents and infrastructure"),
		# tab2_headline of gui_buildmenu:build_menu_per_type
		"tab2_headline"               : _("Fields"),
		# tab4_headline of gui_buildmenu:build_menu_per_type
		"tab4_headline"               : _("Companies"),
		# tab5_headline of gui_buildmenu:build_menu_per_type
		"tab5_headline"               : _("Military"),
		# tab6_headline of gui_buildmenu:build_menu_per_type
		"tab6_headline"               : _("Aesthetics"),
		},
	}
