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

# ###################################################
# WARNING: This fiile is generated automagically. If
#          you need to update it follow the procedure
#          outlined below.
#
# * Generate a bare version using
#     python development/extract_strings_from_xml.py \
#       horizons/i18n/guitranslations.py
# * Do the manual postprocessing needed, a diff between
#   the versions help figuring out what is needed.
#   Currently you want to replace the Version strings by
#   the magic from horizons/constants.py
# ###################################################

from horizons.constants import VERSION

text_translations = dict()

def set_translations():
	global text_translations
	text_translations = {
		"build_menu/hud_build_tab0.xml" : {
			"headline"                    : _("Sailor Buildings"),
			"residents_infra_label"       : _("Residents and Infrastructure"),
			"services_label"              : _("Services"),
			"companies_label"             : _("Companies"),
			"resident-1"                  : _("Tent: \nHouses your \ninhabitants."),
			"store-1"                     : _("Storage: \nExtends stock \nand provides \ncollectors."),
			"street-1"                    : _("Trail: \nNeeded for \ncollecting goods."),
			"main_square-1"               : _("Main square: \nSupplies citizens \nwith goods."),
			"church-1"                    : _("Pavilion: \nFulfills religious \nneeds of sailors."),
			"lighthouse-1"                : _("Signal fire: \nAllows the player \nto trade with \nthe free trader."),
			"lumberjack-1"                : _("Lumberjack: \nChops down trees \nand turns them \ninto boards."),
			"tree-1"                      : _("Tree"),
			"hunter-1"                    : _("Hunter: \nHunts wild \nforest animals, \nproduces food."),
			"fisher-1"                    : _("Fisherman: \nFishes the sea, \nproduces food.")},
		"build_menu/hud_build_tab1.xml" : {
			"headline"                    : _("Pioneer Buildings"),
			"companies_label"             : _("Companies"),
			"companies_label"             : _("Fields"),
			"services_label"              : _("Services"),
			"military_label"              : _("Military"),
			"herder-1"                    : _("Farm: \nGrows field \ncrops and raises \nlivestock."),
			"weaver-1"                    : _("Weaver: \nTurns lamb wool \ninto cloth."),
			"clay-pit-1"                  : _("Clay Pit: \nGets clay \nfrom deposit."),
			"brickyard-1"                 : _("Brickyard: \nTurns clay \ninto bricks."),
			"potatofield-1"               : _("Potato Field: \nYields food. \nNeeds a farm."),
			"pasture-1"                   : _("Pasture: \nRaises sheep. \nProduces wool. \nNeeds a farm."),
			"villageschool-1"             : _("Village school: \nProvides education."),
			"boat_builder-1"              : _("Boat builder: \nBuilds boats and \nsmall ships. \nBuilt on coast.")},
		"build_menu/hud_build_tab2.xml" : {
			"headline"                    : _("Settler Buildings"),
			"housing_label"               : _("Housing"),
			"production_label"            : _("Production"),
			"villageschool-1"             : _("Village school: \nProvides education."),
			"sugarfield-1"                : _("Sugar Field: \nProduces sugar\nfor rum.")},
		"build_menu/hud_build_tab3.xml" : {
			"headline"                    : _("Citizen Buildings")},
		"build_menu/hud_build_tab4.xml" : {
			"headline"                    : _("Merchant Buildings")},
		"build_menu/hud_build_tab5.xml" : {
			"headline"                    : _("Aristocrat Buildings")},
		"build_menu/hud_builddetail.xml" : {
			"headline"                    : _("Build"),
			"running_costs_label"         : _("Running Costs:")},
		"buildings_gui/production_building_overview.xml" : {
			"headline"                    : _("Building overview")},
		"buysellmenu/buysellmenu.xml" : {
			"headline"                    : _("Buy or sell resources"),
			"legend_label"                : _("Legend:"),
			"buy_label"                   : _("Buy resources"),
			"sell_label"                  : _("Sell resources")},
		"buysellmenu/resources.xml" : {
			"headline"                    : _("Select resources:")},
		"captains_log.xml" : {
			"backwardButton"              : _("Read prev. entries"),
			"forwardButton"               : _("Read next entries"),
			"cancelButton"                : _("Leave Captain's Log")},
		"change_name.xml" : {
			"headline"                    : _("Change name"),
			"enter_new_name_lbl"          : _("Enter new name:")},
		"chat.xml" : {
			"headline"                    : _("Chat"),
			"chat_lbl"                    : _("Enter your message:")},
		"chime.xml" : {
			"headline"                    : _("Chime The Bell"),
			"made_it_label"               : _("Yeah, you made it..."),
			"deadlink_label"              : _("But this is a deadlink, sorry.")},
		"credits/0.xml" : {
			"headline_team"               : _("UH-Team"),
			"headline_projectcoord"       : _("Project Coordination"),
			"headline_programming"        : _("Programming"),
			"headline_gamedesign"         : _("Game-Play Design"),
			"headline_sfx"                : _("Sound and Music Artists"),
			"headline_gfx"                : _("Graphic Artists"),
			"patchers_lbl"                : _("Patchers"),
			"translators_lbl"             : _("Translators"),
			"special_thanks_lbl"          : _("Special Thanks")},
		"credits/1.xml" : {
			"team_lbl"                    : _("UH-Team"),
			"headline_patchers"           : _("Patchers"),
			"translators_lbl"             : _("Translators"),
			"special_thanks_lbl"          : _("Special Thanks")},
		"credits/2.xml" : {
			"team_lbl"                    : _("UH-Team"),
			"patchers_lbl"                : _("Patchers"),
			"headline_translators"        : _("Translators"),
			"special_thanks_lbl"          : _("Special Thanks")},
		"credits/3.xml" : {
			"team_lbl"                    : _("UH-Team"),
			"patchers_lbl"                : _("Patchers"),
			"translators_lbl"             : _("Translators"),
			"headline_thanks"             : _("Special Thanks"),
			"fife_team_lbl"               : _("The whole FIFE team (www.fifengine.de)")},
		"gamemenu.xml" : {
			"version_label"               : VERSION.string(),
			"start"                       : _("Return to Game"),
			"quit"                        : _(" Cancel Game "),
			"savegame"                    : _(" Save Game "),
			"loadgame"                    : _(" Load Game "),
			"help"                        : _(" Help "),
			"chimebell"                   : _(" Chime The Bell "),
			"settings"                    : _(" Settings ")},
		"help.xml" : {
			"headline"                    : _("Key Bindings"),
			"set01"                       : _("{LEFT}        = Scroll left"),
			"set02"                       : _("{RIGHT}        = Scroll right"),
			"set03"                       : _("{UP}        = Scroll up"),
			"set04"                       : _("{DOWN}        = Scroll down"),
			"set05"                       : _("{ , }         = Rotate building left"),
			"set06"                       : _("{ . }         = Rotate building right"),
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
			"set26"                       : _("{C} = Chat"),
			"set25"                       : _("{SHIFT} = Hold to place multiple buildings"),
			"have_fun_lbl"                : _("Have fun."),
			"fife_and_uh_team_lbl"        : _("The FIFE and Unknown Horizons"),
			"fife_and_uh_team_lbl2"       : _("development teams")},
		"ingame_pause.xml" : {
			"headline"                    : _("Game paused"),
			"hit_p_to_continue_lbl"       : _("Hit P to continue the game or click below!")},
		"ingame_pdb_start.xml" : {
			"headline"                    : _("Terminal debugmode"),
			"started_pdb_lbl"             : _("You start the terminal python debugger pdb!")},
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
		"menu_panel.xml" : {
			"destroy_tool"                : _("Destroy"),
			"logbook"                     : _("Captain's log"),
			"build"                       : _("Build menu"),
			"helpLink"                    : _("Help"),
			"gameMenuButton"              : _("Game menu")},
		"multiplayer_creategame.xml" : {
			"headline"                    : _("CREATE GAME - MULTIPLAYER"),
			"mp_player_limit_lbl"         : _("Player limit:"),
			"exit_to_mp_menu_lbl"         : _("Back:"),
			"headline"                    : _("Choose a map:"),
			"create_game_lbl"             : _("Create game:"),
			"cancel"                      : _("Exit to multiplayer menu"),
			"create"                      : _("Create this new game")},
		"multiplayer_gamelobby.xml" : {
			"headline"                    : _("Gamelobby"),
			"headline"                    : _("Chat:"),
			"exit_to_mp_menu_lbl"         : _("Leave:"),
			"game_start_notice"           : _("The game will start as soon as enough players have joined."),
			"startmessage"                : _("Game details:"),
			"cancel"                      : _("Exit gamelobby")},
		"multiplayermenu.xml" : {
			"headline"                    : _("NEW GAME - MULTIPLAYER"),
			"exit_to_main_menu_lbl"       : _("Main menu:"),
			"create_game_lbl"             : _("Create game:"),
			"headline"                    : _("Active games:"),
			"refr_gamelist_lbl"           : _("Refresh list:"),
			"join_game_lbl"               : _("Join game"),
			"cancel"                      : _("Exit to main menu"),
			"create"                      : _("Create a new game"),
			"refresh"                     : _("Refresh list of active games"),
			"join"                        : _("Join the selected game")},
		"playerdataselection.xml" : {
			"player_label"                : _("Player name:"),
			"color_label"                 : _("Color:")},
		"quitgame.xml" : {
			"headline"                    : _("Quit Game"),
			"quit_game_caption"           : _("Are you sure you want to quit Unknown Horizons?")},
		"quitsession.xml" : {
			"headline"                    : _("Quit Session"),
			"ConfirmQuitLabel"            : _("Are you sure you want to abort the running session?")},
		"requirerestart.xml" : {
			"headline"                    : _("Restart Required"),
			"require_restart_label"       : _("Some of your changes require a restart of Unknown Horizons.")},
		"select_savegame.xml" : {
			"headline"                    : _("Your saved games:"),
			"enter_filename_label"        : _("Enter filename:"),
			"details_label"               : _("Details:")},
		"settings.xml" : {
			"headline"                    : _("Settings"),
			"warning"                     : _("Please make sure that you know, what you do."),
			"headline_graphics"           : _("Graphics"),
			"screen_resolution_label"     : _("Screen resolution:"),
			"color_depth_label"           : _("Color depth:"),
			"use_renderer_label"          : _("Used renderer:"),
			"screen_fullscreen_text"      : _("Full screen"),
			"headline_sound"              : _("Sound"),
			"music_volume_label"          : _("Music volume:"),
			"effect_volume_label"         : _("Effects volume:"),
			"sound_enable_opt_text"       : _("Enable sound"),
			"headline_saving"             : _("Saving"),
			"autosave_interval_label"     : _("Autosave interval:"),
			"number_of_autosaves_label"   : _("Number of autosaves:"),
			"number_of_quicksaves_label"  : _("Number of quicksaves:"),
			"headline_language"           : _("Language"),
			"language_label"              : _("Select language:")},
		"ship/trade.xml" : {
			"headline"                    : _("Trade"),
			"ship_label"                  : _("Ship:"),
			"exchange_label"              : _("Exchange:"),
			"trade_with_label"            : _("Trade partner:")},
		"singleplayermenu.xml" : {
			"headline"                    : _("NEW GAME - SINGLEPLAYER"),
			"main_menu_label"             : _("Main menu:"),
			"choose_map_lbl"              : _("Choose a map to play:"),
			"start_game_label"            : _("Start game:"),
			"showCampaign"                : _("Campaign"),
			"showRandom"                  : _("Random map"),
			"showMaps"                    : _("Free play")},
		"tab_widget/boatbuilder/boatbuilder.xml" : {
			"headline"                    : _("Building Overview"),
			"BB_howto_build_lbl"          : _("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
			"BB_current_order"            : _("Currently building:"),
			"BB_progress_label"           : _("Construction progress:"),
			"BB_cancel_build_label"       : _("Cancel building:"),
			"BB_cancel_warning_label"     : _("(lose all resources)"),
			"toggle_active_active"        : _("Pause"),
			"toggle_active_inactive"      : _("Resume"),
			"BB_cancel_button"            : _("Cancel all \nbuilding progress")},
		"tab_widget/boatbuilder/confirm.xml" : {
			"BB_confirm_build_label"      : _("Build ship:"),
			"create_unit"                 : _("Build this ship!")},
		"tab_widget/boatbuilder/fisher.xml" : {
			"headline"                    : _("Fishing Boats"),
			"BB_fisher_ship1"             : _("Fishing boat"),
			"BB_fisher_ship2"             : _("Cutter"),
			"BB_fisher_ship3"             : _("Herring fisher"),
			"BB_fisher_ship4"             : _("Whaler"),
			"BB_build_fisher_1"           : _("Build this ship!")},
		"tab_widget/tab_account.xml" : {
			"headline"                    : _("Account"),
			"income_label"                : _("Income:"),
			"taxes_label"                 : _("Taxes"),
			"sell_income_label"           : _("Sale"),
			"expenses_label"              : _("Expenses:"),
			"running_costs_label"         : _("Running Costs:"),
			"buy_expenses_label"          : _("Buying"),
			"balance_label"               : _("Balance:")},
		"tab_widget/tab_branch_overview.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"running_costs_label"         : _("Running Costs:")},
		"tab_widget/tab_marketplace_settler.xml" : {
			"headline"                    : _("Settler overview"),
			"avg_happiness_lbl"           : _("Average happiness:"),
			"most_needed_res_lbl"         : _("Most needed resource:")},
		"tab_widget/tab_overview.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:")},
		"tab_widget/tab_overview_enemy_building.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:")},
		"tab_widget/tab_overview_marketplace.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:"),
			"tax_label"                   : _("Taxes:")},
		"tab_widget/tab_overview_resourcedeposit.xml" : {
			"headline"                    : _("Resource Deposit"),
			"res_dep_description_lbl"     : _("This is a resource deposit, where you can build a mine to dig up resources."),
			"res_dep_description_lbl2"    : _("It contains these resources:")},
		"tab_widget/tab_overview_settler.xml" : {
			"headline"                    : _("Overview"),
			"tax_label"                   : _("Taxes:"),
			"needed_res_label"            : _("Needed Resources:")},
		"tab_widget/tab_overview_ship.xml" : {
			"health_label"                : _("Health:")},
		"tab_widget/tab_overview_signalfire.xml" : {
			"signal_fire_description_lbl" : _("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods.")},
		"tab_widget/tab_overview_tradership.xml" : {
			"trader_description_lbl"      : _("This is the free trader's ship. It will visit you from time to time to buy or sell goods.")},
		"tab_widget/tab_production_line.xml" : {
			"toggle_active_active"        : _("Pause production"),
			"toggle_active_inactive"      : _("Start production")},
		"tab_widget/tab_stock.xml" : {
			"headline"                    : _("Inventory")},
		"tab_widget/tab_stock_ship.xml" : {
			"headline"                    : _("Inventory"),
			"load_unload_label"           : _("Load/Unload:")},
	}
