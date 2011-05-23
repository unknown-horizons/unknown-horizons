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

# ###################################################
# WARNING: This file is generated automagically. If
#          you need to update it follow the procedure
#          outlined below.
#
# * Generate a bare version using
#     python development/extract_strings_from_xml.py \
#       horizons/i18n/guitranslations.py
# * Do the manual postprocessing needed, a diff between
#   the versions help figuring out what is needed.
# ###################################################

from horizons.constants import VERSION

text_translations = dict()

def set_translations():
	global text_translations
	text_translations = {
		"buildtab_increment0.xml" : {
			"companies_label"             : _("Companies"),
			"headline"                    : _("Sailor buildings"),
			"residents_infra_label"       : _("Residents and infrastructure"),
			"services_label"              : _("Services"),
			"church-1"                    : _("Pavilion: Fulfills religious needs of sailors."),
			"fisher-1"                    : _("Fisherman: Fishes the sea, produces food."),
			"hunter-1"                    : _("Hunter: Hunts wild forest animals, produces food."),
			"lighthouse-1"                : _("Signal fire: Allows the player to trade with the free trader."),
			"lumberjack-1"                : _("Lumberjack: Chops down trees and turns them into boards."),
			"main_square-1"               : _("Main square: Supplies citizens with goods."),
			"resident-1"                  : _("Tent: Houses your inhabitants."),
			"store-1"                     : _("Storage: Extends stock and provides collectors."),
			"street-1"                    : _("Trail: Needed for collecting goods."),
			"tree-1"                      : _("Tree")},
		"buildtab_increment1.xml" : {
			"companies_label"             : _("Companies"),
			"fields_label"                : _("Fields"),
			"headline"                    : _("Pioneer buildings"),
			"military_label"              : _("Military"),
			"services_label"              : _("Services"),
			"boat_builder-1"              : _("Boat builder: Builds boats and small ships. Built on coast."),
			"brickyard-1"                 : _("Brickyard: Turns clay into bricks."),
			"clay-pit-1"                  : _("Clay pit: Gets clay from deposit."),
			"distillery-1"                : _("Distillery: Turns sugar into liquor."),
			"herder-1"                    : _("Farm: Grows field crops and raises livestock."),
			"pasture-1"                   : _("Pasture: Raises sheep. Produces wool. Needs a farm."),
			"potatofield-1"               : _("Potato field: Yields food. Needs a farm."),
			"sugarfield-1"                : _("Sugarcane field: Used in liquor production. Needs a farm."),
			"villageschool-1"             : _("Village school: Provides education."),
			"weaver-1"                    : _("Weaver: Turns lamb wool into cloth.")},
		"buildtab_increment2.xml" : {
			"companies_label"             : _("Companies"),
			"headline"                    : _("Settler buildings"),
			"services_label"              : _("Services"),
			"charcoal-burning-1"          : _("Charcoal burning: Burns a lot of boards."),
			"iron-mine-1"                 : _("Iron mine: Gets iron ore from deposit."),
			"smeltery-1"                  : _("Smeltery: Refines all kind of ores."),
			"tavern-1"                    : _("Tavern: Provides get-together."),
			"toolmaker-1"                 : _("Toolmaker: Produces tools out of iron.")},
		"place_building.xml" : {
			"headline"                    : _("Build"),
			"running_costs_label"         : _("Running costs:")},
		"stringpreviewwidget.xml" : {
			"headline"                    : _("String Previewer Tool for Scenario files"),
			"hintlbl"                     : _("select a scenario and click on load/reload to update the messages in the captain's log"),
			"load"                        : _("load/reload")},
		"city_info.xml" : {
			"city_info_inhabitants"       : _("Inhabitants"),
			"city_name"                   : _("Click to change the name of your settlement.")},
		"menu_panel.xml" : {
			"destroy_tool"                : _("Destroy"),
			"build"                       : _("Build menu"),
			"gameMenuButton"              : _("Game menu"),
			"helpLink"                    : _("Help"),
			"logbook"                     : _("Captain's log")},
		"minimap.xml" : {
			"rotateLeft"                  : _("Rotate map counterclockwise"),
			"rotateRight"                 : _("Rotate map clockwise"),
			"speedDown"                   : _("Decrease game speed"),
			"speedUp"                     : _("Increase game speed"),
			"zoomIn"                      : _("Zoom in"),
			"zoomOut"                     : _("Zoom out")},
		"status.xml" : {
			"boards_icon"                 : _("Boards"),
			"bricks_icon"                 : _("Bricks"),
			"food_icon"                   : _("Food"),
			"textiles_icon"               : _("Textiles"),
			"tools_icon"                  : _("Tools")},
		"status_gold.xml" : {
			"gold_icon"                   : _("Gold")},
		"change_name.xml" : {
			"enter_new_name_lbl"          : _("Enter new name:"),
			"headline_change_name"        : _("Change name")},
		"chat.xml" : {
			"chat_lbl"                    : _("Enter your message:"),
			"headline"                    : _("Chat")},
		"buysellmenu.xml" : {
			"buy_label"                   : _("Buy resources"),
			"headline"                    : _("Buy or sell resources"),
			"legend_label"                : _("Legend:"),
			"sell_label"                  : _("Sell resources")},
		"overview_productionline.xml" : {
			"toggle_active_active"        : _("Pause production"),
			"toggle_active_inactive"      : _("Start production")},
		"captains_log.xml" : {
			"cancelButton"                : _("Leave Captain's log"),
			"backwardButton"              : _("Read prev. entries"),
			"forwardButton"               : _("Read next entries")},
		"configure_route.xml" : {
			"cancelButton"                : _("Exit"),
			"add_bo"                      : _("Add to list"),
			"start_route"                 : _("Start route")},
		"route_entry.xml" : {
			"delete_bo"                   : _("Delete entry"),
			"move_down"                   : _("Move down"),
			"move_up"                     : _("Move up")},
		"gamemenu.xml" : {
			"chimebell"                   : _("Attention please!"),
			"credits"                     : _("Credits"),
			"help"                        : _("Help"),
			"loadgame"                    : _("Load game"),
			"quit"                        : _("Cancel game"),
			"savegame"                    : _("Save game"),
			"settings"                    : _("Settings"),
			"start"                       : _("Return to game"),
			"version_label"               : VERSION.string()},
		"help.xml" : {
			"fife_and_uh_team_lbl"        : _("The FIFE and Unknown Horizons development teams"),
			"have_fun_lbl"                : _("Have fun."),
			"headline"                    : _("Key bindings"),
			"set01"                       : _("{LEFT} = Scroll left"),
			"set02"                       : _("{RIGHT} = Scroll right"),
			"set03"                       : _("{UP} = Scroll up"),
			"set04"                       : _("{DOWN} = Scroll down"),
			"set05"                       : _("{ , } = Rotate building left"),
			"set06"                       : _("{ . } = Rotate building right"),
			"set07"                       : _("{B} = Show build menu"),
			"set08"                       : _("{F1} = Display help"),
			"set09"                       : _("{F5} = Quicksave"),
			"set10"                       : _("{F9} = Quickload"),
			"set11"                       : _("{F10} = Toggle console on/off"),
			"set12"                       : _("{ESC} = Show pause menu"),
			"set13"                       : _("{G} = Toggle grid on/off"),
			"set14"                       : _("{X} = Enable destruct mode"),
			"set20"                       : _("{P} = Pause game"),
			"set21"                       : _("{ + } = Increase game speed"),
			"set22"                       : _("{ - } = Decrease game speed"),
			"set23"                       : _("{S} = Screenshot"),
			"set25"                       : _("{SHIFT} = Hold to place multiple buildings"),
			"set26"                       : _("{C} = Chat"),
			"set27"                       : _("{L} = Toggle Captain's log"),
			"okButton"                    : _("Exit to main menu")},
		"loadingscreen.xml" : {
			"loading_label"               : _("Loading ..."),
			"version_label"               : VERSION.string()},
		"mainmenu.xml" : {
			"chimebell"                   : _("Attention please!"),
			"credits"                     : _("Credits"),
			"help"                        : _("Help"),
			"loadgame"                    : _("Load game"),
			"quit"                        : _("Quit"),
			"settings"                    : _("Settings"),
			"start"                       : _("Singleplayer"),
			"start_multi"                 : _("Multiplayer"),
			"version_label"               : VERSION.string()},
		"multiplayer_creategame.xml" : {
			"create_game_lbl"             : _("Create game:"),
			"exit_to_mp_menu_lbl"         : _("Back:"),
			"headline"                    : _("Choose a map:"),
			"headline"                    : _("Create game - Multiplayer"),
			"mp_player_limit_lbl"         : _("Player limit:"),
			"create"                      : _("Create this new game"),
			"cancel"                      : _("Exit to multiplayer menu")},
		"multiplayer_gamelobby.xml" : {
			"exit_to_mp_menu_lbl"         : _("Leave:"),
			"game_start_notice"           : _("The game will start as soon as enough players have joined."),
			"headline"                    : _("Chat:"),
			"headline"                    : _("Gamelobby"),
			"startmessage"                : _("Game details:"),
			"cancel"                      : _("Exit gamelobby")},
		"multiplayermenu.xml" : {
			"active_games_lbl"            : _("Active games:"),
			"create_game_lbl"             : _("Create game:"),
			"exit_to_main_menu_lbl"       : _("Main menu:"),
			"game_showonlyownversion"     : _("Show only games with the same version:"),
			"headline_left"               : _("New game - Multiplayer"),
			"join_game_lbl"               : _("Join game"),
			"name_lbl"                    : _("Apply:"),
			"refr_gamelist_lbl"           : _("Refresh list:"),
			"apply_new_nickname"          : _("Apply the new name"),
			"create"                      : _("Create a new game"),
			"join"                        : _("Join the selected game"),
			"cancel"                      : _("Exit to main menu"),
			"refresh"                     : _("Refresh list of active games")},
		"settings.xml" : {
			"autosave_interval_label"     : _("Autosave interval in minutes:"),
			"color_depth_label"           : _("Color depth:"),
			"edge_scrolling_label"        : _("Enable edge scrolling:"),
			"effect_volume_label"         : _("Effects volume:"),
			"headline"                    : _("Settings"),
			"headline_graphics"           : _("Graphics"),
			"headline_language"           : _("Language"),
			"headline_network"            : _("Network"),
			"headline_saving"             : _("Saving"),
			"headline_sound"              : _("Sound"),
			"language_label"              : _("Select language:"),
			"minimap_rotation_label"      : _("Enable minimap rotation:"),
			"music_volume_label"          : _("Music volume:"),
			"network_port_hint_lbl"       : _("(0 means default)"),
			"network_port_lbl"            : _("Network port:"),
			"number_of_autosaves_label"   : _("Number of autosaves:"),
			"number_of_quicksaves_label"  : _("Number of quicksaves:"),
			"screen_fullscreen_text"      : _("Full screen:"),
			"screen_resolution_label"     : _("Screen resolution:"),
			"sound_enable_opt_text"       : _("Enable sound:"),
			"use_renderer_label"          : _("Used renderer:"),
			"warning"                     : _("Please make sure that you know what you do.")},
		"select_savegame.xml" : {
			"enter_filename_label"        : _("Enter filename:"),
			"headline_details_label"      : _("Details:"),
			"headline_saved_games_label"  : _("Your saved games:")},
		"singleplayermenu.xml" : {
			"choose_map_lbl"              : _("Choose a map to play:"),
			"headline"                    : _("New game - Singleplayer"),
			"main_menu_label"             : _("Main menu:"),
			"start_game_label"            : _("Start game:"),
			"showCampaign"                : _("Campaign"),
			"showMaps"                    : _("Free play"),
			"showRandom"                  : _("Random map"),
			"showScenario"                : _("Scenario"),
			"okay"                        : _("Start game"),
			"cancel"                      : _("Exit to main menu")},
		"playerdataselection.xml" : {
			"color_label"                 : _("Color:"),
			"player_label"                : _("Player name:")},
		"boatbuilder.xml" : {
			"BB_cancel_build_label"       : _("Cancel building:"),
			"BB_cancel_warning_label"     : _("(lose all resources)"),
			"BB_current_order"            : _("Currently building:"),
			"BB_howto_build_lbl"          : _("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
			"BB_progress_label"           : _("Construction progress:"),
			"headline"                    : _("Building overview"),
			"BB_cancel_button"            : _("Cancel all building progress"),
			"toggle_active_active"        : _("Pause"),
			"toggle_active_inactive"      : _("Resume"),
			"running_costs_label"         : _("Running costs")},
		"boatbuilder_fisher.xml" : {
			"headline"                    : _("Fishing boats"),
			"headline_BB_fisher_ship1"    : _("Fishing boat"),
			"headline_BB_fisher_ship2"    : _("Cutter"),
			"headline_BB_fisher_ship3"    : _("Herring fisher"),
			"headline_BB_fisher_ship4"    : _("Whaler"),
			"BB_build_fisher_1"           : _("Build this ship!"),
			"cancelButton"                : _("Not yet implemented!"),
			"cancelButton"                : _("Not yet implemented!"),
			"cancelButton"                : _("Not yet implemented!")},
		"select_trade_resource.xml" : {
			"headline"                    : _("Select resources:")},
		"tab_account.xml" : {
			"buy_expenses_label"          : _("Buying"),
			"headline"                    : _("Account"),
			"headline_balance_label"      : _("Balance:"),
			"headline_expenses_label"     : _("Expenses:"),
			"headline_income_label"       : _("Income:"),
			"running_costs_label"         : _("Running costs"),
			"sell_income_label"           : _("Sale"),
			"taxes_label"                 : _("Taxes")},
		"island_inventory.xml" : {
			"headline"                    : _("Inventory")},
		"mainsquare_inhabitants.xml" : {
			"avg_happiness_lbl"           : _("Average happiness:"),
			"headline"                    : _("Settler overview"),
			"most_needed_res_lbl"         : _("Most needed resource:")},
		"overview_branchoffice.xml" : {
			"name_label"                  : _("Name:"),
			"running_costs_label"         : _("Running costs:")},
		"overview_enemybuilding.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:")},
		"overview_mainsquare.xml" : {
			"name_label"                  : _("Name:"),
			"tax_label"                   : _("Taxes:"),
			"tax_rate_label"              : _("Tax Rate")},
		"overview_productionbuilding.xml" : {
			"headline"                    : _("Building overview"),
			"running_costs_label"         : _("Running costs"),
			"capacity_utilisation"        : _("capacity utilization"),
			"running_costs"               : _("Running costs")},
		"overview_resourcedeposit.xml" : {
			"headline"                    : _("Resource deposit"),
			"res_dep_description_lbl"     : _("This is a resource deposit where you can build a mine to dig up resources."),
			"res_dep_description_lbl2"    : _("It contains these resources:")},
		"overview_settler.xml" : {
			"needed_res_label"            : _("Needed resources:"),
			"tax_label"                   : _("Taxes:"),
			"happiness_label"             : _("Happiness"),
			"paid_taxes_label"            : _("Paid taxes"),
			"paid_taxes_label"            : _("Tax Rate"),
			"residents_label"             : _("Residents"),
			"happiness"                   : _("Happiness")},
		"overview_ship.xml" : {
			"foundSettlement_label"       : _("Build settlement:"),
			"name"                        : _("Click to change the name of this ship."),
			"foundSettlement"             : _("Build settlement")},
		"overview_signalfire.xml" : {
			"signal_fire_description_lbl" : _("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods.")},
		"overview_tradership.xml" : {
			"trader_description_lbl"      : _("This is the free trader's ship. It will visit you from time to time to buy or sell goods.")},
		"overviewtab.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:")},
		"exchange_goods.xml" : {
			"exchange_label"              : _("Exchange:"),
			"headline"                    : _("Trade"),
			"ship_label"                  : _("Ship:"),
			"trade_with_label"            : _("Trade partner:")},
		"ship_inventory.xml" : {
			"configure_route_label"       : _("Configure trading route:"),
			"headline"                    : _("Inventory"),
			"load_unload_label"           : _("Load/Unload:")},
	}
