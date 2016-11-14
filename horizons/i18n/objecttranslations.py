# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
# ** Refer to  development/create_pot.sh  for help with building or updating
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

T = lambda s: s








object_translations = {

	"content/objects/buildings/bakery.yaml" : {
		# name of buildings:bakery
		"name"                        : T("Bakery"),
		# tooltip_text of buildings:bakery
		"tooltip_text"                : T("Consumes flour. Produces food."),
		},

	"content/objects/buildings/barracks.yaml" : {
		# name of buildings:barracks
		"name"                        : T("Barracks"),
		# tooltip_text of buildings:barracks
		"tooltip_text"                : T("Recruits units suitable for ground combat."),
		},

	"content/objects/buildings/barrier.yaml" : {
		# name_0 of buildings:barrier
		"name_0"                      : T("Wooden barrier"),
		# name_1 of buildings:barrier
		"name_1"                      : T("Clay wall"),
		# tooltip_text of buildings:barrier
		"tooltip_text"                : T("Provides security."),
		},

	"content/objects/buildings/blender.yaml" : {
		# name of buildings:blender
		"name"                        : T("Blender"),
		# tooltip_text of buildings:blender
		"tooltip_text"                : T("Produces condiments out of spices."),
		},

	"content/objects/buildings/boatbuilder.yaml" : {
		# name of buildings:boatbuilder
		"name"                        : T("Boat Builder"),
		# tooltip_text of buildings:boatbuilder
		"tooltip_text"                : T("Builds boats and small ships. Built on coast."),
		},

	"content/objects/buildings/brewery.yaml" : {
		# name of buildings:brewery
		"name"                        : T("Brewery"),
		# tooltip_text of buildings:brewery
		"tooltip_text"                : T("Consumes hops. Produces Beer."),
		},

	"content/objects/buildings/brickyard.yaml" : {
		# name of buildings:brickyard
		"name"                        : T("Brickyard"),
		# tooltip_text of buildings:brickyard
		"tooltip_text"                : T("Turns clay into bricks."),
		},

	"content/objects/buildings/butchery.yaml" : {
		# name of buildings:butchery
		"name"                        : T("Butchery"),
		# tooltip_text of buildings:butchery
		"tooltip_text"                : T("Needs pigs or cattle. Produces food."),
		},

	"content/objects/buildings/cannonfoundry.yaml" : {
		# name of buildings:cannonfoundry
		"name"                        : T("Cannon Foundry"),
		# tooltip_text of buildings:cannonfoundry
		"tooltip_text"                : T("Produces Cannons."),
		},

	"content/objects/buildings/charcoalburning.yaml" : {
		# name of buildings:charcoalburning
		"name"                        : T("Charcoal Burning"),
		# tooltip_text of buildings:charcoalburning
		"tooltip_text"                : T("Burns a lot of boards."),
		},

	"content/objects/buildings/claydeposit.yaml" : {
		# name of buildings:claydeposit
		"name"                        : T("Clay Deposit"),
		},

	"content/objects/buildings/claypit.yaml" : {
		# name of buildings:claypit
		"name"                        : T("Clay Pit"),
		# tooltip_text of buildings:claypit
		"tooltip_text"                : T("Gets clay from deposit."),
		},

	"content/objects/buildings/distillery.yaml" : {
		# name of buildings:distillery
		"name"                        : T("Distillery"),
		# tooltip_text of buildings:distillery
		"tooltip_text"                : T("Turns sugar into liquor."),
		},

	"content/objects/buildings/doctor.yaml" : {
		# name of buildings:doctor
		"name"                        : T("Doctor"),
		# tooltip_text of buildings:doctor
		"tooltip_text"                : T("Treats diseases. Consumes herbs."),
		},

	"content/objects/buildings/farm.yaml" : {
		# name of buildings:farm
		"name"                        : T("Farm"),
		# tooltip_text of buildings:farm
		"tooltip_text"                : T("Grows field crops and raises livestock."),
		},

	"content/objects/buildings/fields/alvearies.yaml" : {
		# name of buildings:fields:alvearies
		"name"                        : T("Alvearies"),
		# tooltip_text of buildings:fields:alvearies
		"tooltip_text"                : T("Keeps bees. Produces honeycombs used for confectionery. Needs a farm."),
		},

	"content/objects/buildings/fields/cattlerun.yaml" : {
		# name of buildings:fields:cattlerun
		"name"                        : T("Cattle Run"),
		# tooltip_text of buildings:fields:cattlerun
		"tooltip_text"                : T("Raises cattle. Needs a farm."),
		},

	"content/objects/buildings/fields/cocoafield.yaml" : {
		# name of buildings:fields:cocoafield
		"name"                        : T("Cocoa Field"),
		# tooltip_text of buildings:fields:cocoafield
		"tooltip_text"                : T("Produces cocoa beans used for confectionery. Needs a farm."),
		},

	"content/objects/buildings/fields/cornfield.yaml" : {
		# name of buildings:fields:cornfield
		"name"                        : T("Corn Field"),
		# tooltip_text of buildings:fields:cornfield
		"tooltip_text"                : T("Yields corn. Needs a farm."),
		},

	"content/objects/buildings/fields/herbary.yaml" : {
		# name of buildings:fields:herbary
		"name"                        : T("Herbary"),
		# tooltip_text of buildings:fields:herbary
		"tooltip_text"                : T("Produces herbs. Needs a farm."),
		},

	"content/objects/buildings/fields/hopfield.yaml" : {
		# name of buildings:fields:hopfield
		"name"                        : T("Hop Field"),
		# tooltip_text of buildings:fields:hopfield
		"tooltip_text"                : T("Yields hop. Needs a farm."),
		},

	"content/objects/buildings/fields/pasture.yaml" : {
		# name of buildings:fields:pasture
		"name"                        : T("Pasture"),
		# tooltip_text of buildings:fields:pasture
		"tooltip_text"                : T("Raises sheep. Produces wool. Needs a farm."),
		},

	"content/objects/buildings/fields/pigsty.yaml" : {
		# name of buildings:fields:pigsty
		"name"                        : T("Pigsty"),
		# tooltip_text of buildings:fields:pigsty
		"tooltip_text"                : T("Raises pigs. Needs a farm."),
		},

	"content/objects/buildings/fields/potatofield.yaml" : {
		# name of buildings:fields:potatofield
		"name"                        : T("Potato Field"),
		# tooltip_text of buildings:fields:potatofield
		"tooltip_text"                : T("Yields food. Needs a farm."),
		},

	"content/objects/buildings/fields/spicefield.yaml" : {
		# name of buildings:fields:spicefield
		"name"                        : T("Spice Field"),
		# tooltip_text of buildings:fields:spicefield
		"tooltip_text"                : T("Grows spices. Needs a farm."),
		},

	"content/objects/buildings/fields/sugarfield.yaml" : {
		# name of buildings:fields:sugarfield
		"name"                        : T("Sugar Field"),
		# tooltip_text of buildings:fields:sugarfield
		"tooltip_text"                : T("Used in liquor production. Needs a farm."),
		},

	"content/objects/buildings/fields/tobaccofield.yaml" : {
		# name of buildings:fields:tobaccofield
		"name"                        : T("Tobacco Field"),
		# tooltip_text of buildings:fields:tobaccofield
		"tooltip_text"                : T("Produces tobacco. Needs a farm."),
		},

	"content/objects/buildings/fields/vineyard.yaml" : {
		# name of buildings:fields:vineyard
		"name"                        : T("Vineyard"),
		# tooltip_text of buildings:fields:vineyard
		"tooltip_text"                : T("Produces grapes for use in wine and confectionery. Needs a farm."),
		},

	"content/objects/buildings/fireservice.yaml" : {
		# name of buildings:fireservice
		"name"                        : T("Fire Station"),
		# tooltip_text of buildings:fireservice
		"tooltip_text"                : T("Extinguishes fires."),
		},

	"content/objects/buildings/fishdeposit.yaml" : {
		# name of buildings:fishdeposit
		"name"                        : T("Fish Deposit"),
		},

	"content/objects/buildings/fishermanstent.yaml" : {
		# name of buildings:fishermanstent
		"name"                        : T("Fisherman's Tent"),
		# tooltip_text of buildings:fishermanstent
		"tooltip_text"                : T("Fishes the sea, produces food."),
		},

	"content/objects/buildings/hunterstent.yaml" : {
		# name of buildings:hunterstent
		"name"                        : T("Hunter's Tent"),
		# tooltip_text of buildings:hunterstent
		"tooltip_text"                : T("Hunts wild forest animals, produces food."),
		},

	"content/objects/buildings/lookout.yaml" : {
		# name of buildings:lookout
		"name"                        : T("Lookout"),
		# tooltip_text of buildings:lookout
		"tooltip_text"                : T("Expands settlement range."),
		},

	"content/objects/buildings/lumberjackcamp.yaml" : {
		# name_0 of buildings:lumberjackcamp
		"name_0"                      : T("Lumberjack Tent"),
		# name_1 of buildings:lumberjackcamp
		"name_1"                      : T("Lumberjack Hut"),
		# tooltip_text of buildings:lumberjackcamp
		"tooltip_text"                : T("Chops down trees and turns them into boards."),
		},

	"content/objects/buildings/mainsquare.yaml" : {
		# name of buildings:mainsquare
		"name"                        : T("Main Square"),
		# tooltip_text of buildings:mainsquare
		"tooltip_text"                : T("Supplies citizens with goods. Provides community."),
		},

	"content/objects/buildings/mine.yaml" : {
		# name of buildings:mine
		"name"                        : T("Mine"),
		# tooltip_text of buildings:mine
		"tooltip_text"                : T("Gets iron ore from deposit."),
		},

	"content/objects/buildings/mountain.yaml" : {
		# name of buildings:mountain
		"name"                        : T("Mountain"),
		},

	"content/objects/buildings/pastryshop.yaml" : {
		# name of buildings:pastryshop
		"name"                        : T("Pastry Shop"),
		# tooltip_text of buildings:pastryshop
		"tooltip_text"                : T("Produces all kinds of confectionery."),
		},

	"content/objects/buildings/pavilion.yaml" : {
		# name of buildings:pavilion
		"name"                        : T("Pavilion"),
		# tooltip_text of buildings:pavilion
		"tooltip_text"                : T("Fulfills religious needs of sailors."),
		},

	"content/objects/buildings/ruinedtent.yaml" : {
		# name of buildings:ruinedtent
		"name"                        : T("Ruined Tent"),
		},

	"content/objects/buildings/saltponds.yaml" : {
		# name of buildings:saltponds
		"name"                        : T("Salt Ponds"),
		# tooltip_text of buildings:saltponds
		"tooltip_text"                : T("Evaporates salt. Built on sea coast."),
		},

	"content/objects/buildings/signalfire.yaml" : {
		# name of buildings:signalfire
		"name"                        : T("Signal Fire"),
		# tooltip_text of buildings:signalfire
		"tooltip_text"                : T("Allows the player to trade with the free trader."),
		},

	"content/objects/buildings/smeltery.yaml" : {
		# name of buildings:smeltery
		"name"                        : T("Smeltery"),
		# tooltip_text of buildings:smeltery
		"tooltip_text"                : T("Refines all kind of ores."),
		},

	"content/objects/buildings/stonedeposit.yaml" : {
		# name of buildings:stonedeposit
		"name"                        : T("Stone Deposit"),
		},

	"content/objects/buildings/stonemason.yaml" : {
		# name_3 of buildings:stonemason
		"name_3"                      : T("Stonemason"),
		# name_4 of buildings:stonemason
		"name_4"                      : T("Carver"),
		# tooltip_text of buildings:stonemason
		"tooltip_text"                : T("Carves stone tops into bricks."),
		},

	"content/objects/buildings/stonepit.yaml" : {
		# name of buildings:stonepit
		"name"                        : T("Stone Pit"),
		# tooltip_text of buildings:stonepit
		"tooltip_text"                : T("Gets stone from a mountain."),
		},

	"content/objects/buildings/storagetent.yaml" : {
		# name_0 of buildings:storagetent
		"name_0"                      : T("Storage Tent"),
		# name_1 of buildings:storagetent
		"name_1"                      : T("Storage Hut"),
		# tooltip_text of buildings:storagetent
		"tooltip_text"                : T("Extends stock, expands settlement range and provides collectors."),
		},

	"content/objects/buildings/tavern.yaml" : {
		# name of buildings:tavern
		"name"                        : T("Tavern"),
		# tooltip_text of buildings:tavern
		"tooltip_text"                : T("Provides get-together."),
		},

	"content/objects/buildings/tent.yaml" : {
		# name_0 of buildings:tent
		"name_0"                      : T("Tent"),
		# name_1 of buildings:tent
		"name_1"                      : T("Hut"),
		# name_2 of buildings:tent
		"name_2"                      : T("House"),
		# name_3 of buildings:tent
		"name_3"                      : T("Stone house"),
		# name_4 of buildings:tent
		"name_4"                      : T("Estate"),
		# name_5 of buildings:tent
		"name_5"                      : T("Manor"),
		# tooltip_text of buildings:tent
		"tooltip_text"                : T("Houses your inhabitants."),
		},

	"content/objects/buildings/tobacconist.yaml" : {
		# name of buildings:tobacconist
		"name"                        : T("Tobacconist"),
		# tooltip_text of buildings:tobacconist
		"tooltip_text"                : T("Produces tobaccos out of tobacco."),
		},

	"content/objects/buildings/toolmaker.yaml" : {
		# name of buildings:toolmaker
		"name"                        : T("Toolmaker"),
		# tooltip_text of buildings:toolmaker
		"tooltip_text"                : T("Produces tools out of iron."),
		},

	"content/objects/buildings/trail.yaml" : {
		# name_0 of buildings:trail
		"name_0"                      : T("Trail"),
		# name_1 of buildings:trail
		"name_1"                      : T("Gravel Path"),
		# name_3 of buildings:trail
		"name_3"                      : T("Cobblestone Street"),
		# tooltip_text of buildings:trail
		"tooltip_text"                : T("Needed for collecting goods."),
		},

	"content/objects/buildings/tree.yaml" : {
		# name of buildings:tree
		"name"                        : T("Tree"),
		# tooltip_text of buildings:tree
		"tooltip_text"                : T("Provides lumber. Chopped down by lumberjacks."),
		},

	"content/objects/buildings/villageschool.yaml" : {
		# name of buildings:villageschool
		"name"                        : T("Village School"),
		# tooltip_text of buildings:villageschool
		"tooltip_text"                : T("Provides education."),
		},

	"content/objects/buildings/warehouse.yaml" : {
		# name of buildings:warehouse
		"name"                        : T("Warehouse"),
		},

	"content/objects/buildings/weaponsmith.yaml" : {
		# name of buildings:weaponsmith
		"name"                        : T("Weaponsmith"),
		# tooltip_text of buildings:weaponsmith
		"tooltip_text"                : T("Produces weapons out of iron."),
		},

	"content/objects/buildings/weaverstent.yaml" : {
		# name of buildings:weaverstent
		"name"                        : T("Weaver's Hut"),
		# tooltip_text of buildings:weaverstent
		"tooltip_text"                : T("Turns lamb wool into cloth."),
		},

	"content/objects/buildings/windmill.yaml" : {
		# name of buildings:windmill
		"name"                        : T("Windmill"),
		# tooltip_text of buildings:windmill
		"tooltip_text"                : T("Grinds corn into flour."),
		},

	"content/objects/buildings/winery.yaml" : {
		# name of buildings:winery
		"name"                        : T("Winery"),
		# tooltip_text of buildings:winery
		"tooltip_text"                : T("Produces wine out of grapes."),
		},

	"content/objects/buildings/woodentower.yaml" : {
		# name of buildings:woodentower
		"name"                        : T("Wooden Tower"),
		# tooltip_text of buildings:woodentower
		"tooltip_text"                : T("Defends your settlement."),
		},

	"content/objects/gui_buildmenu/build_menu_per_tier.yaml" : {
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Companies"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Companies"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Companies"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Companies"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Fields"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Fields"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Fields"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Fields"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Military"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Military"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Mining"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Residents and infrastructure"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Services"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Services"),
		# headline of gui_buildmenu:build_menu_per_tier
		"headline"                    : T("Services"),
		},

	"content/objects/gui_buildmenu/build_menu_per_type.yaml" : {
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Citizens"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Citizens"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Food"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Fortifications"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Infrastructure"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Infrastructure"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Military Service"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Mining"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Pioneers"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Precaution"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Residential"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Sea"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Services"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Settlers"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Wood"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Workshops"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Workshops"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Workshops"),
		# headline of gui_buildmenu:build_menu_per_type
		"headline"                    : T("Workshops"),
		# tab1_headline of gui_buildmenu:build_menu_per_type
		"tab1_headline"               : T("Settlement"),
		# tab1_helptext of gui_buildmenu:build_menu_per_type
		"tab1_helptext"               : T("Residents and infrastructure"),
		# tab2_headline of gui_buildmenu:build_menu_per_type
		"tab2_headline"               : T("Fields"),
		# tab3_headline of gui_buildmenu:build_menu_per_type
		"tab3_headline"               : T("Agriculture"),
		# tab4_headline of gui_buildmenu:build_menu_per_type
		"tab4_headline"               : T("Companies"),
		# tab5_headline of gui_buildmenu:build_menu_per_type
		"tab5_headline"               : T("Military"),
		},
}
