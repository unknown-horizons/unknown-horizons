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
		"xml/buildmenu/buildtab_increment0.xml" : {
			"headline"                    : _("Sailor buildings"),
			"residents_infra_label"       : _("Residents and infrastructure"),
			"services_label"              : _("Services"),
			"companies_label"             : _("Companies"),
			"resident-1"                  : _("Tent: Houses your inhabitants."),
			"store-1"                     : _("Storage: Extends stock and provides collectors."),
			"street-1"                    : _("Trail: Needed for collecting goods."),
			"main_square-1"               : _("Main square: Supplies citizens with goods."),
			"church-1"                    : _("Pavilion: Fulfills religious needs of sailors."),
			"lighthouse-1"                : _("Signal fire: Allows the player to trade with the free trader."),
			"lumberjack-1"                : _("Lumberjack: Chops down trees and turns them into boards."),
			"tree-1"                      : _("Tree"),
			"hunter-1"                    : _("Hunter: Hunts wild forest animals, produces food."),
			"fisher-1"                    : _("Fisherman: Fishes the sea, produces food.")},
		"xml/buildmenu/buildtab_increment1.xml" : {
			"headline"                    : _("Pioneer buildings"),
			"companies_label"             : _("Companies"),
			"fields_label"                : _("Fields"),
			"services_label"              : _("Services"),
			"military_label"              : _("Military"),
			"companies_label"             : _("Companies"),
			"herder-1"                    : _("Farm: Grows field crops and raises livestock."),
			"weaver-1"                    : _("Weaver: Turns lamb wool into cloth."),
			"clay-pit-1"                  : _("Clay pit: Gets clay from deposit."),
			"brickyard-1"                 : _("Brickyard: Turns clay into bricks."),
			"potatofield-1"               : _("Potato field: Yields food. Needs a farm."),
			"pasture-1"                   : _("Pasture: Raises sheep. Produces wool. Needs a farm."),
			"sugarfield-1"                : _("Sugarcane field: Used in liquor production. Needs a farm."),
			"villageschool-1"             : _("Village school: Provides education."),
			"boat_builder-1"              : _("Boat builder: Builds boats and small ships. Built on coast."),
			"distillery-1"                : _("Distillery: Turns sugar into liquor.")},
		"xml/buildmenu/buildtab_increment2.xml" : {
			"headline"                    : _("Settler buildings"),
			"companies_label"             : _("Companies"),
			"services_label"              : _("Services"),
			"iron-mine-1"                 : _("Iron mine: Gets iron ore from deposit."),
			"smeltery-1"                  : _("Smeltery: Refines all kind of ores."),
			"toolmaker-1"                 : _("Toolmaker: Produces tools out of iron."),
			"charcoal-burning-1"          : _("Charcoal burning: Burns a lot of boards."),
			"tavern-1"                    : _("Tavern: Provides get-together.")},
		"xml/buildmenu/place_building.xml" : {
			"headline"                    : _("Build"),
			"running_costs_label"         : _("Running costs:")},
		"xml/ingame/hud/city_info.xml" : {
			"city_info_inhabitants"       : _("Inhabitants"),
			"city_name"                   : _("Click to change the name of your settlement.")},
		"xml/ingame/hud/menu_panel.xml" : {
			"destroy_tool"                : _("Destroy"),
			"logbook"                     : _("Captain's log"),
			"build"                       : _("Build menu"),
			"helpLink"                    : _("Help"),
			"gameMenuButton"              : _("Game menu")},
		"xml/ingame/hud/status.xml" : {
			"food_icon"                   : _("Food"),
			"tools_icon"                  : _("Tools"),
			"boards_icon"                 : _("Boards"),
			"bricks_icon"                 : _("Bricks"),
			"textiles_icon"               : _("Textiles")},
		"xml/ingame/hud/status_gold.xml" : {
			"gold_icon"                   : _("Gold")},
		"xml/ingame/popups/change_name.xml" : {
			"change_name_headline"        : _("Change name"),
			"enter_new_name_lbl"          : _("Enter new name:")},
		"xml/ingame/popups/chat.xml" : {
			"headline"                    : _("Chat"),
			"chat_lbl"                    : _("Enter your message:")},
		"xml/ingame/popups/ingame_pause.xml" : {
			"headline"                    : _("Game paused"),
			"hit_p_to_continue_lbl"       : _("Hit P to continue the game or click below!")},
		"xml/ingame/templates/buysellmenu.xml" : {
			"headline"                    : _("Buy or sell resources"),
			"legend_label"                : _("Legend:"),
			"buy_label"                   : _("Buy resources"),
			"sell_label"                  : _("Sell resources")},
		"xml/ingame/templates/overview_productionline.xml" : {
			"toggle_active_active"        : _("Pause production"),
			"toggle_active_inactive"      : _("Start production")},
		"xml/ingame/widgets/captains_log.xml" : {
			"cancelButton"                : _("Leave Captain's log"),
			"backwardButton"              : _("Read prev. entries"),
			"forwardButton"               : _("Read next entries")},
		"xml/mainmenu/credits/credits0.xml" : {
			"headline_team"               : _("UH-Team"),
			"headline_projectcoord"       : _("Project Coordination"),
			"headline_programming"        : _("Programming"),
			"headline_gamedesign"         : _("Game-Play Design"),
			"headline_sfx"                : _("Sound and Music Artists"),
			"headline_gfx"                : _("Graphic Artists"),
			"patchers_lbl"                : _("Patchers"),
			"translators_lbl"             : _("Translators"),
			"special_thanks_lbl"          : _("Special Thanks")},
		"xml/mainmenu/credits/credits1.xml" : {
			"team_lbl"                    : _("UH-Team"),
			"headline_patchers"           : _("Patchers"),
			"translators_lbl"             : _("Translators"),
			"special_thanks_lbl"          : _("Special Thanks")},
		"xml/mainmenu/credits/credits2.xml" : {
			"team_lbl"                    : _("UH-Team"),
			"patchers_lbl"                : _("Patchers"),
			"headline_translators"        : _("Translators"),
			"special_thanks_lbl"          : _("Special Thanks")},
		"xml/mainmenu/credits/credits3.xml" : {
			"team_lbl"                    : _("UH-Team"),
			"patchers_lbl"                : _("Patchers"),
			"translators_lbl"             : _("Translators"),
			"headline_thanks"             : _("Special Thanks"),
			"fife_team_lbl"               : _("The whole FIFE team (www.fifengine.de)")},
		"xml/mainmenu/gamemenu.xml" : {
			"version_label"               : VERSION.string(),
			"start"                       : _("Return to game"),
			"savegame"                    : _("Save game"),
			"settings"                    : _("Settings"),
			"help"                        : _("Help"),
			"quit"                        : _("Cancel game"),
			"chimebell"                   : _("Chime the bell"),
			"credits"                     : _("Credits"),
			"loadgame"                    : _("Load game")},
		"xml/mainmenu/help.xml" : {
			"headline"                    : _("Key bindings"),
			"set01"                       : _("{LEFT} = Scroll left"),
			"set02"                       : _("{RIGHT} = Scroll right"),
			"set03"                       : _("{UP} = Scroll up"),
			"set04"                       : _("{DOWN} = Scroll down"),
			"set21"                       : _("{ + } = Increase game speed"),
			"set22"                       : _("{ - } = Decrease game speed"),
			"set05"                       : _("{ , } = Rotate building left"),
			"set06"                       : _("{ . } = Rotate building right"),
			"set07"                       : _("{B} = Show build menu"),
			"set12"                       : _("{ESC} = Show pause menu"),
			"set08"                       : _("{F1} = Display help"),
			"set09"                       : _("{F5} = Quicksave"),
			"set10"                       : _("{F9} = Quickload"),
			"set11"                       : _("{F10} = Toggle console on/off"),
			"set20"                       : _("{P} = Pause game"),
			"set13"                       : _("{G} = Toggle grid on/off"),
			"set14"                       : _("{X} = Enable destruct mode"),
			"set23"                       : _("{S} = Screenshot"),
			"set26"                       : _("{C} = Chat"),
			"set25"                       : _("{SHIFT} = Hold to place multiple buildings"),
			"have_fun_lbl"                : _("Have fun."),
			"fife_and_uh_team_lbl"        : _("The FIFE and Unknown Horizons"),
			"fife_and_uh_team_lbl2"       : _("development teams"),
			"okButton"                    : _("Exit to main menu")},
		"xml/mainmenu/loadingscreen.xml" : {
			"loading_label"               : _("Loading ..."),
			"version_label"               : VERSION.string()},
		"xml/mainmenu/mainmenu.xml" : {
			"version_label"               : VERSION.string(),
			"start"                       : _("Singleplayer"),
			"start_multi"                 : _("Multiplayer"),
			"settings"                    : _("Settings"),
			"help"                        : _("Help"),
			"quit"                        : _("Quit"),
			"chimebell"                   : _("Chime the bell"),
			"credits"                     : _("Credits"),
			"loadgame"                    : _("Load game")},
		"xml/mainmenu/multiplayer/multiplayer_creategame.xml" : {
			"headline"                    : _("Create game - Multiplayer"),
			"mp_player_limit_lbl"         : _("Player limit:"),
			"exit_to_mp_menu_lbl"         : _("Back:"),
			"headline"                    : _("Choose a map:"),
			"create_game_lbl"             : _("Create game:"),
			"cancel"                      : _("Exit to multiplayer menu"),
			"create"                      : _("Create this new game")},
		"xml/mainmenu/multiplayer/multiplayer_gamelobby.xml" : {
			"headline"                    : _("Gamelobby"),
			"headline"                    : _("Chat:"),
			"exit_to_mp_menu_lbl"         : _("Leave:"),
			"game_start_notice"           : _("The game will start as soon as enough players have joined."),
			"startmessage"                : _("Game details:"),
			"cancel"                      : _("Exit gamelobby")},
		"xml/mainmenu/multiplayer/multiplayermenu.xml" : {
			"headline_left"               : _("New game - Multiplayer"),
			"name_lbl"                    : _("Apply:"),
			"create_game_lbl"             : _("Create game:"),
			"exit_to_main_menu_lbl"       : _("Main menu:"),
			"active_games_lbl"            : _("Active games:"),
			"refr_gamelist_lbl"           : _("Refresh list:"),
			"game_showonlyownversion"     : _("Show only games with the same version:"),
			"join_game_lbl"               : _("Join game"),
			"apply_new_nickname"          : _("Apply the new name"),
			"create"                      : _("Create a new game"),
			"cancel"                      : _("Exit to main menu"),
			"refresh"                     : _("Refresh list of active games"),
			"join"                        : _("Join the selected game")},
		"xml/mainmenu/popups/requirerestart.xml" : {
			"headline"                    : _("Restart required"),
			"require_restart_label"       : _("Some of your changes require a restart of Unknown Horizons.")},
		"xml/mainmenu/settings.xml" : {
			"headline"                    : _("Settings"),
			"warning"                     : _("Please make sure that you know what you do."),
			"headline_graphics"           : _("Graphics"),
			"screen_resolution_label"     : _("Screen resolution:"),
			"color_depth_label"           : _("Color depth:"),
			"use_renderer_label"          : _("Used renderer:"),
			"screen_fullscreen_text"      : _("Full screen:"),
			"headline_sound"              : _("Sound"),
			"music_volume_label"          : _("Music volume:"),
			"effect_volume_label"         : _("Effects volume:"),
			"sound_enable_opt_text"       : _("Enable sound:"),
			"headline_saving"             : _("Saving"),
			"autosave_interval_label"     : _("Autosave interval:"),
			"number_of_autosaves_label"   : _("Number of autosaves:"),
			"number_of_quicksaves_label"  : _("Number of quicksaves:"),
			"headline_language"           : _("Language"),
			"language_label"              : _("Select language:")},
		"xml/mainmenu/singleplayer/select_savegame.xml" : {
			"saved_games_label"           : _("Your saved games:"),
			"enter_filename_label"        : _("Enter filename:"),
			"details_label"               : _("Details:")},
		"xml/mainmenu/singleplayer/singleplayermenu.xml" : {
			"headline"                    : _("New game - Singleplayer"),
			"main_menu_label"             : _("Main menu:"),
			"choose_map_lbl"              : _("Choose a map to play:"),
			"start_game_label"            : _("Start game:"),
			"showScenario"                : _("Scenario"),
			"showRandom"                  : _("Random map"),
			"showMaps"                    : _("Free play"),
			"cancel"                      : _("Exit to main menu"),
			"okay"                        : _("Start game")},
		"xml/mainmenu/templates/playerdataselection.xml" : {
			"player_label"                : _("Player name:"),
			"color_label"                 : _("Color:")},
		"xml/tabwidget/boatbuilder/boatbuilder.xml" : {
			"headline"                    : _("Building overview"),
			"BB_howto_build_lbl"          : _("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
			"BB_current_order"            : _("Currently building:"),
			"BB_progress_label"           : _("Construction progress:"),
			"BB_cancel_build_label"       : _("Cancel building:"),
			"BB_cancel_warning_label"     : _("(lose all resources)"),
			"toggle_active_active"        : _("Pause"),
			"toggle_active_inactive"      : _("Resume"),
			"BB_cancel_button"            : _("Cancel all building progress"),
			"running_costs_label"         : _("Running costs")},
		"xml/tabwidget/boatbuilder/boatbuilder_fisher.xml" : {
			"headline"                    : _("Fishing boats"),
			"BB_fisher_ship1"             : _("Fishing boat"),
			"BB_fisher_ship2"             : _("Cutter"),
			"BB_fisher_ship3"             : _("Herring fisher"),
			"BB_fisher_ship4"             : _("Whaler"),
			"BB_build_fisher_1"           : _("Build this ship!")},
		"xml/tabwidget/boatbuilder/boatbuilder_trade.xml" : {
			"headline"                    : _("Trade boats")},
		"xml/tabwidget/boatbuilder/boatbuilder_war1.xml" : {
			"headline"                    : _("War boats")},
		"xml/tabwidget/boatbuilder/boatbuilder_war2.xml" : {
			"headline"                    : _("War ships")},
		"xml/tabwidget/branchoffice/select_trade_resource.xml" : {
			"headline"                    : _("Select resources:")},
		"xml/tabwidget/branchoffice/tab_account.xml" : {
			"headline"                    : _("Account"),
			"income_label"                : _("Income:"),
			"taxes_label"                 : _("Taxes"),
			"sell_income_label"           : _("Sale"),
			"expenses_label"              : _("Expenses:"),
			"running_costs_label"         : _("Running costs"),
			"buy_expenses_label"          : _("Buying"),
			"balance_label"               : _("Balance:")},
		"xml/tabwidget/island_inventory.xml" : {
			"headline"                    : _("Inventory")},
		"xml/tabwidget/overview/overview_branchoffice.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"running_costs_label"         : _("Running costs:")},
		"xml/tabwidget/overview/overview_enemybuilding.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:")},
		"xml/tabwidget/overview/overview_mainsquare.xml" : {
			"headline"                    : _("Settler overview"),
			"avg_happiness_lbl"           : _("Average happiness:"),
			"most_needed_res_lbl"         : _("Most needed resource:")},
		"xml/tabwidget/overview/overview_marketplace.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:"),
			"tax_label"                   : _("Taxes:")},
		"xml/tabwidget/overview/overview_productionbuilding.xml" : {
			"headline"                    : _("Building overview"),
			"running_costs_label"         : _("Running costs")},
		"xml/tabwidget/overview/overview_resourcedeposit.xml" : {
			"headline"                    : _("Resource deposit"),
			"res_dep_description_lbl"     : _("This is a resource deposit where you can build a mine to dig up resources."),
			"res_dep_description_lbl2"    : _("It contains these resources:")},
		"xml/tabwidget/overview/overview_settler.xml" : {
			"headline"                    : _("Overview"),
			"tax_label"                   : _("Taxes:"),
			"needed_res_label"            : _("Needed resources:"),
			"happiness_label"             : _("Happiness"),
			"residents_label"             : _("Residents"),
			"paid_taxes_label"            : _("Paid taxes"),
			"happiness"                   : _("Happiness")},
		"xml/tabwidget/overview/overview_ship.xml" : {
			"health_label"                : _("Health:"),
			"name"                        : _("Click to change the name of this ship."),
			"foundSettlement"             : _("Build settlement")},
		"xml/tabwidget/overview/overview_signalfire.xml" : {
			"signal_fire_description_lbl" : _("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods.")},
		"xml/tabwidget/overview/overview_tradership.xml" : {
			"trader_description_lbl"      : _("This is the free trader's ship. It will visit you from time to time to buy or sell goods.")},
		"xml/tabwidget/overview/overviewtab.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:")},
		"xml/tabwidget/ships/exchange_goods.xml" : {
			"headline"                    : _("Trade"),
			"ship_label"                  : _("Ship:"),
			"exchange_label"              : _("Exchange:"),
			"trade_with_label"            : _("Trade partner:")},
		"xml/tabwidget/ships/ship_inventory.xml" : {
			"headline"                    : _("Inventory"),
			"load_unload_label"           : _("Load/Unload:")},
	}
