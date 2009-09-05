# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from horizons.constatns import VERSION

text_translations = dict()

def set_translations():
	global text_translations
	text_translations = {
		"serverlobby.xml" : {
			"player_label"                : _("Player:"),
			"color_label"                 : _("Color:"),
			"slots_label"                 : _("Slots:"),
			"bots_label"                  : _("Bots:"),
			"chatbutton"                  : _("chat")},
		"popupbox.xml" : {
			"headline"                    : _("Not Implemented Yet")},
		"credits.xml" : {
			"headline"                    : _("Contributors")},
		"quitsession.xml" : {
			"headline"                    : _("Quit Session"),
			"ConfirmQuitLabel"            : _("Are you sure you want to abort the running session?")},
		"settings.xml" : {
			"headline"                    : _("Settings"),
			"screen_resolution_label"     : _("Screen resolution:"),
			"color_depth_label"           : _("Color depth:"),
			"use_renderer_label"          : _("Used renderer:"),
			"music_volume_label"          : _("Music volume:"),
			"effect_volume_label"         : _("Effects volume:"),
			"autosave_interval_label"     : _("Autosave interval:"),
			"minutes_label"               : _("minutes"),
			"number_of_autosaves_label"   : _("Number of autosaves:"),
			"number_of_quicksaves_label"  : _("Number of quicksaves:"),
			"language_label"              : _("Language:"),
			"screen_fullscreen"           : _("Full screen"),
			"sound_enable_opt"            : _("Enable sound")},
		"ingame_pdb_start.xml" : {
			"headline"                    : _("Terminal debugmode")},
		"ingame_save.xml" : {
			"headline"                    : _("Save Game"),
			"enter_filename_label"        : _("Enter filename:")},
		"changes_require_restart.xml" : {
			"headline"                    : _("Restart Required"),
			"require_restart_label"       : _("Some of your changes require a restart of Unknown Horizons.")},
		"loadingscreen.xml" : {
			"loading_label"               : _("Loading ..."),
			"version_label"               : VERSION.string()},
		"mainmenu.xml" : {
			"version_label"               : VERSION.string(),
			"start"                       : _("Singleplayer"),
			"start_multi"                 : _("Multiplayer"),
			"credits"                     : _(" Credits "),
			"quit"                        : _(" Quit "),
			"settings"                    : _(" Settings "),
			"help"                        : _(" Help "),
			"loadgame"                    : _(" Continue Game "),
			"chimebell"                   : _(" Chime The Bell ")},
		"singleplayermenu.xml" : {
			"headline"                    : _("NEW GAME - SINGLEPLAYER"),
			"main_menu_label"             : _("Main menu:"),
			"player_label"                : _("Player:"),
			"color_label"                 : _("Color:"),
			"start_game_label"            : _("Start game:")},
		"chime.xml" : {
			"headline"                    : _("Chime The Bell"),
			"made_it_label"               : _("Yeah, you made it..."),
			"deadlink_label"              : _("But this is a deadlink, sorry.")},
		"menu_panel.xml" : {
			"destroy_tool"                : _("Destroy"),
			"diplomacy"                   : _("Diplomacy\n(not yet \nimplemented)"),
			"build"                       : _("Build menu"),
			"helpLink"                    : _("Help"),
			"gameMenuButton"              : _("Game menu")},
		"quitgame.xml" : {
			"headline"                    : _("Quit Game"),
			"quit_game_caption"           : _("Are you sure you want to quit Unknown Horizons?")},
		"boatbuilder.xml" : {
			"boat_builder_window"         : _("boatbuilder")},
		"ingame_pause.xml" : {
			"headline"                    : _("Game paused")},
		"ingame_load.xml" : {
			"headline"                    : _("Load Game"),
			"details_label"               : _("Details:")},
		"gamemenu.xml" : {
			"version_label"               : VERSION.string(),
			"start"                       : _("Return to Game"),
			"quit"                        : _(" Cancel Game "),
			"savegame"                    : _(" Save Game "),
			"loadgame"                    : _(" Load Game "),
			"help"                        : _(" Help "),
			"chimebell"                   : _(" Chime The Bell "),
			"settings"                    : _(" Settings ")},
		"change_name_dialog.xml" : {
			"headline"                    : _("Change name")},
		"help.xml" : {
			"headline"                    : _("Key Bindings")},
		"buildings_gui/work_building_tab1.xml" : {
			"StockLabel"                  : _("stock")},
		"buildings_gui/work_building_tab4.xml" : {
			"ProductionLabel"             : _("production")},
		"buildings_gui/work_building_tab0.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"running_cost_label"          : _("Running Costs:"),
			"buy_sell_label"              : _("Buy/Sell Resources:")},
		"buildings_gui/production_building_overview.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"running_costs_label"         : _("Running Costs:"),
			"toggle_label"                : _("Toggle active:")},
		"buildings_gui/work_building_tab5.xml" : {
			"ResearchLabel"               : _("research")},
		"buildings_gui/work_building_tab3.xml" : {
			"RouteLabel"                  : _("route")},
		"buildings_gui/work_building_tab2.xml" : {
			"CombatLabel"                 : _("combat")},
		"tab_widget/tab_stock.xml" : {
			"headline"                    : _("Inventory")},
		"tab_widget/tab_overview_marketplace.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"tax_label"                   : _("Taxes:")},
		"tab_widget/tab_branch_overview.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"running_cost_label"          : _("Running Costs:")},
		"tab_widget/tab_overview_ship.xml" : {
			"health_label"                : _("Health:")},
		"tab_widget/tab_account.xml" : {
			"headline"                    : _("Account"),
			"income_label"                : _("Income:"),
			"taxes_label"                 : _("Taxes"),
			"expenses_label"              : _("Expenses:"),
			"running_costs_label"         : _("Running Costs:"),
			"balance_label"               : _("Balance:")},
		"tab_widget/tab_overview_settler.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"happiness_label"             : _("Happiness:"),
			"needed_res_label"            : _("Needed Resources:"),
			"inhabitants_label"           : _("Inhabitants:"),
			"level_label"                 : _("Level:"),
			"taxes_label"                 : _("Taxes:")},
		"tab_widget/boatbuilder.xml" : {
			"current_construction_label"  : _("Current construction progress:")},
		"tab_widget/tab_boatbuilder_create.xml" : {
			"overview_label"              : _("Select a boat to build:"),
			"new_settlement_label"        : _("Build selected:")},
		"tab_widget/tab_stock_ship.xml" : {
			"headline"                    : _("Inventory"),
			"load_unload_label"           : _("Load/Unload:")},
		"tab_widget/tab_overview.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:")},
		"ship/trade.xml" : {
			"headline"                    : _("Trade"),
			"ship_label"                  : _("Ship:"),
			"exchange_label"              : _("Exchange:"),
			"trade_with_label"            : _("Trade partner:")},
		"buysellmenu/buysellmenu.xml" : {
			"headline"                    : _("Buy or sell resources"),
			"legend_label"                : _("Legend:"),
			"buy_label"                   : _("Buy resources"),
			"sell_label"                  : _("Sell resources")},
		"buysellmenu/resources.xml" : {
			"headline"                    : _("Select resources:")},
		"build_menu/hud_build_tab0.xml" : {
			"headline"                    : _("Sailor Buildings"),
			"residental_label"            : _("Residents and Infrastructural"),
			"service_label"               : _("Services"),
			"companies_label"             : _("Companies"),
			"military_label"              : _("Military"),
			"resident-1"                  : _("Tent"),
			"street-1"                    : _("Trail: \nNeeded for \ndelivering goods"),
			"tree-1"                      : _("Tree"),
			"main_square-1"               : _("Main square: \nSupplies citizens\nwith goods"),
			"store-1"                     : _("Storage: \nExtends settlement,\nstores goods"),
			"church-1"                    : _("Ministry: \nFullfiles religious \nneeds of citizens"),
			"lighthouse-1"                : _("Signal fire: \nAllows the player \nto trade with \nthe free trader"),
			"lumberjack-1"                : _("Lumberjack: \nHarvests wood \nand turns them \ninto boards "),
			"hunter-1"                    : _("Hunter: \nHunts wild animals, \ngathers food "),
			"weaver-1"                    : _("Weaver: \nTurns lamb wool \ninto cloth"),
			"boat_builder-1"              : _("Boat builder: \nBuilds boats and \nsmall ships, \nbuilt on coast"),
			"fisher-1"                    : _("Fisherman: \nFishes the sea, \ngathers food"),
			"herder-1"                    : _("Farm: \nGrows field \ncrops and raises \nlivestock."),
			"pasture-1"                   : _("Pasture is used \nto grow sheep.\nProduces wool. \nNeeds a farm"),
			"potatofield-1"               : _("Potato Field:\nDelivers food \nNeeds a farm"),
			"tower-1"                     : _("Lookout: \nIncreases the \nplayer's sight")},
		"build_menu/hud_builddetail.xml" : {
			"headline"                    : _("Build"),
			"running_cost_label"          : _("Running Costs:")},
		"build_menu/hud_build_tab1.xml" : {
			"headline"                    : _("Pioneer Buildings")},
	}
