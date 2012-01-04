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

# ###################################################################
# WARNING: This file is generated automagically.
#          You need to update it to see changes to strings in-game.
#          DO NOT MANUALLY UPDATE THIS FILE (by editing strings).
#          The script to generate .pot templates calls the following:
# ./development/extract_strings_from_objects.py  horizons/i18n/objecttranslations.py
#          If you changed strings in code, you might just run this
#          command as well.
# NOTE: In string-freeze mode (shortly before releases, usually
#       announced in a meeting), updates to this file must not happen
#       without permission of the responsible translation admin!
# ###################################################################

from horizons.constants import VERSION

object_translations = dict()

def set_translations():
	global object_translations
	object_translations = {

	"content/objects/buildings/boatbuilder.yaml" : {
		"name"                        : _("Boat Builder"),
		"tooltip_text"                : _("Builds boats and small ships. Built on coast."),
		},

	"content/objects/buildings/brickyard.yaml" : {
		"name"                        : _("Brickyard"),
		"tooltip_text"                : _("Turns clay into bricks."),
		},

	"content/objects/buildings/butchery.yaml" : {
		"name"                        : _("Butchery"),
		"tooltip_text"                : _("Needs pigs or cattle. Produces food."),
		},

	"content/objects/buildings/cattlerun.yaml" : {
		"name"                        : _("Cattle Run"),
		"tooltip_text"                : _("Raises cattle. Needs a farm."),
		},

	"content/objects/buildings/charcoalburning.yaml" : {
		"name"                        : _("Charcoal Burning"),
		"tooltip_text"                : _("Burns a lot of boards."),
		},

	"content/objects/buildings/claydeposit.yaml" : {
		"name"                        : _("Clay Deposit"),
		},

	"content/objects/buildings/claypit.yaml" : {
		"name"                        : _("Clay Pit"),
		"tooltip_text"                : _("Gets clay from deposit."),
		},

	"content/objects/buildings/distillery.yaml" : {
		"name"                        : _("Distillery"),
		"tooltip_text"                : _("Turns sugar into liquor."),
		},

	"content/objects/buildings/doctor.yaml" : {
		"name"                        : _("Doctor"),
		"tooltip_text"                : _("Treats diseases. Consumes herbs."),
		},

	"content/objects/buildings/farm.yaml" : {
		"name"                        : _("Farm"),
		"tooltip_text"                : _("Grows field crops and raises livestock."),
		},

	"content/objects/buildings/fishdeposit.yaml" : {
		"name"                        : _("Fish Deposit"),
		},

	"content/objects/buildings/fishermanstent.yaml" : {
		"name"                        : _("Fisherman's Tent"),
		"tooltip_text"                : _("Fishes the sea, produces food."),
		},

	"content/objects/buildings/gravelpath.yaml" : {
		"name"                        : _("Gravel Path"),
		},

	"content/objects/buildings/herbary.yaml" : {
		"name"                        : _("Herbary"),
		"tooltip_text"                : _("Produces herbs. Needs a farm."),
		},

	"content/objects/buildings/hunterstent.yaml" : {
		"name"                        : _("Hunter's Tent"),
		"tooltip_text"                : _("Hunts wild forest animals, produces food."),
		},

	"content/objects/buildings/ironmine.yaml" : {
		"name"                        : _("Iron Mine"),
		"tooltip_text"                : _("Gets iron ore from deposit."),
		},

	"content/objects/buildings/log.yaml" : {
		"name"                        : _("Log"),
		"tooltip_text"                : _("Road across a river."),
		},

	"content/objects/buildings/lookout.yaml" : {
		"name"                        : _("Lookout"),
		"tooltip_text"                : _("Increases the player's sight."),
		},

	"content/objects/buildings/lumberjackcamp.yaml" : {
		"name"                        : _("Lumberjack Camp"),
		"tooltip_text"                : _("Chops down trees and turns them into boards."),
		},

	"content/objects/buildings/mainsquare.yaml" : {
		"name"                        : _("Main Square"),
		"tooltip_text"                : _("Supplies citizens with goods."),
		},

	"content/objects/buildings/mountain.yaml" : {
		"name"                        : _("Mountain"),
		},

	"content/objects/buildings/pasture.yaml" : {
		"name"                        : _("Pasture"),
		"tooltip_text"                : _("Raises sheep. Produces wool. Needs a farm."),
		},

	"content/objects/buildings/pavilion.yaml" : {
		"name"                        : _("Pavilion"),
		"tooltip_text"                : _("Fulfills religious needs of sailors."),
		},

	"content/objects/buildings/pigsty.yaml" : {
		"name"                        : _("Pigsty"),
		"tooltip_text"                : _("Raises pigs. Needs a farm."),
		},

	"content/objects/buildings/potatofield.yaml" : {
		"name"                        : _("Potato Field"),
		"tooltip_text"                : _("Yields food. Needs a farm."),
		},

	"content/objects/buildings/rampart.yaml" : {
		"name"                        : _("Rampart"),
		"tooltip_text"                : _("Protects your settlement."),
		},

	"content/objects/buildings/saltponds.yaml" : {
		"name"                        : _("Salt Ponds"),
		"tooltip_text"                : _("Evaporates salt. Built on sea coast."),
		},

	"content/objects/buildings/signalfire.yaml" : {
		"name"                        : _("Signal Fire"),
		"tooltip_text"                : _("Allows the player to trade with the free trader."),
		},

	"content/objects/buildings/smeltery.yaml" : {
		"name"                        : _("Smeltery"),
		"tooltip_text"                : _("Refines all kind of ores."),
		},

	"content/objects/buildings/storagetent.yaml" : {
		"name"                        : _("Storage Tent"),
		"tooltip_text"                : _("Extends stock and provides collectors."),
		},

	"content/objects/buildings/sugarfield.yaml" : {
		"name"                        : _("Sugar Field"),
		"tooltip_text"                : _("Used in liquor production. Needs a farm."),
		},

	"content/objects/buildings/tavern.yaml" : {
		"name"                        : _("Tavern"),
		"tooltip_text"                : _("Provides get-together."),
		},

	"content/objects/buildings/tent.yaml" : {
		"name"                        : _("Tent"),
		"tooltip_text"                : _("Houses your inhabitants."),
		},

	"content/objects/buildings/tentruin.yaml" : {
		"name"                        : _("Tent Ruin"),
		},

	"content/objects/buildings/tobaccofield.yaml" : {
		"name"                        : _("Tobacco Field"),
		"tooltip_text"                : _("Produces tobacco. Needs a farm."),
		},

	"content/objects/buildings/tobacconist.yaml" : {
		"name"                        : _("Tobacconist"),
		"tooltip_text"                : _("Produces tobaccos out of tobacco."),
		},

	"content/objects/buildings/toolmaker.yaml" : {
		"name"                        : _("Toolmaker"),
		"tooltip_text"                : _("Produces tools out of iron."),
		},

	"content/objects/buildings/trail.yaml" : {
		"name"                        : _("Trail"),
		"tooltip_text"                : _("Needed for collecting goods."),
		},

	"content/objects/buildings/tree.yaml" : {
		"name"                        : _("Tree"),
		},

	"content/objects/buildings/villageschool.yaml" : {
		"name"                        : _("Village school"),
		"tooltip_text"                : _("Provides education."),
		},

	"content/objects/buildings/warehouse.yaml" : {
		"name"                        : _("Warehouse"),
		},

	"content/objects/buildings/weaverstent.yaml" : {
		"name"                        : _("Weaver's Tent"),
		"tooltip_text"                : _("Turns lamb wool into cloth."),
		},

	"content/objects/buildings/woodentower.yaml" : {
		"name"                        : _("Wooden Tower"),
		"tooltip_text"                : _("Defends your settlement."),
		},
	}
