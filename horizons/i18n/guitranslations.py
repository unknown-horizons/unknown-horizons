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

text_translations = dict()

def set_translations():
	global text_translations
	text_translations = {
		"hud_branch.xml" : {
			"buildingNameLabel"           : _("Branch office (Branch class ROMAN)")},
		"serverlobby.xml" : {
			"player_label"                : _("Player:"),
			"color_label"                 : _("Color:"),
			"slots_label"                 : _("Slots:"),
			"bots_label"                  : _("Bots:"),
			"chatbutton"                  : _("chat")},
		"popupbox.xml" : {
			"okButton"                    : _("Ok")},
		"popupbox_with_cancel.xml" : {
			"okButton"                    : _("Ok"),
			"cancelButton"                : _("Cancel")},
		"credits.xml" : {
			"creditsIntroText"            : _("These guys contributed to Unknown Horizons"),
			"okButton"                    : _("You guys rock!"),
			"credits_window"              : _("Credits")},
		"inventory.xml" : {
			"islandInventoryLabel"        : _("That's your island-wide inventory."),
			"CoinsLabel"                  : _("Coins:"),
			"LambWoolLabel"               : _("Lamb wool:"),
			"TextileLabel"                : _("Textiles:"),
			"BoardsLabel"                 : _("Boards:"),
			"FoodLabel"                   : _("Food:"),
			"1"                           : _("n/a"),
			"2"                           : _("n/a"),
			"3"                           : _("n/a"),
			"4"                           : _("n/a"),
			"5"                           : _("n/a"),
			"closeButton"                 : _("Close"),
			"inventory_window"            : _("Inventory")},
		"quitsession.xml" : {
			"ConfirmQuitLabel"            : _("Are you sure you want to abort the running session?"),
			"cancelButton"                : _("Cancel"),
			"okButton"                    : _("Ok"),
			"quit_session_window"         : _("Quit Unknown Horizons")},
		"hud_window_cityinfo.xml" : {
			"city_info_label"             : _("City infos")},
		"hud_ship.xml" : {
			"buildingNameLabel"           : _("Ship name (Ship type)"),
			"shipCanons"                  : _("0/0"),
			"shipCrew"                    : _("0/0"),
			"shipSpeed"                   : _("0/0")},
		"load_disabled.xml" : {
			"SorryLabel"                  : _("We're sorry, but the load function is not yet working."),
			"okButton"                    : _("Ok"),
			"load_disabled_window"        : _("Oh noes")},
		"settings.xml" : {
			"settings_dialog_title"       : _("This is the Unknown Horizons settings dialog. Please make sure that you know, what you do."),
			"language_label"              : _("Language:"),
			"autosave_interval_label"     : _("Autosave interval"),
			"number_of_autosaves_label"   : _("Number of saved autosaves:"),
			"number_of_quicksaves_label"  : _("Number of saved quicksaves:"),
			"screen_resolution_label"     : _("Screen resolution:"),
			"use_renderer_label"          : _("Used renderer:"),
			"color_depth_label"           : _("Color depth:"),
			"music_volume_label"          : _("Music volume:"),
			"effect_volume_label"         : _("Effects volume:"),
			"minutes_label"               : _("minutes"),
			"cancelButton"                : _("Cancel"),
			"okButton"                    : _("Ok"),
			"settings_window"             : _("Settings")},
		"ingame_save.xml" : {
			"enter_filename_label"        : _("Enter filename:"),
			"deleteButton"                : _("Delete"),
			"cancelButton"                : _("Cancel"),
			"okButton"                    : _("Ok"),
			"ingame_save_window"          : _("Save game")},
		"changes_require_restart.xml" : {
			"require_restart_label"       : _("Some of your changes require a restart of Unknown Horizons."),
			"okButton"                    : _("Ok"),
			"restart_required_window"     : _("Changes require restart")},
		"loadingscreen.xml" : {
			"loading_label"               : _("Loading..."),
			"version_label"               : _("Unknown Horizons Alpha 2009.0")},
		"hud_buildinfo.xml" : {
			"buildingNameLabel"           : _("Building name (Building Class ROMAN)"),
			"tiles_label"                 : _("Tiles:"),
			"tilesInfo"                   : _("10x10")},
		"hud_res.xml" : {
			"resBoles"                    : _("?"),
			"resBoles"                    : _("?"),
			"resTextiles"                 : _("?"),
			"resTools"                    : _("?")},
		"mainmenu.xml" : {
			"version_label"               : _("Unknown Horizons Alpha 2009.0"),
			"start"                       : _("Singleplayer"),
			"start_multi"                 : _("Multiplayer"),
			"credits"                     : _(" Credits "),
			"quit"                        : _(" Quit "),
			"settings"                    : _(" Settings "),
			"help"                        : _(" Help "),
			"loadgame"                    : _(" Continue Game "),
			"chimebell"                   : _(" Chime The Bell ")},
		"singleplayermenu.xml" : {
			"player_label"                : _("Player:"),
			"color_label"                 : _("Color:"),
			"main_menu_label"             : _("Main menu:"),
			"start_game_label"            : _("Start game:")},
		"chime.xml" : {
			"made_it_label"               : _("Yeah, you made it..."),
			"deadlink_label"              : _("But this is a deadlink, sorry."),
			"okButton"                    : _("Back to business..."),
			"chime_window"                : _("Chime The Bell")},
		"save_disabled.xml" : {
			"save_disabled"               : _("We're sorry, but the save function is not yet working."),
			"okButton"                    : _("Ok"),
			"save_disabled_window"        : _("Oh noes")},
		"quitgame.xml" : {
			"quit_game_caption"           : _("Are you sure you want to Quit Unknown Horizons?"),
			"cancelButton"                : _("Cancel"),
			"okButton"                    : _("Ok"),
			"quitgame_window"             : _("Quit Unknown Horizons")},
		"boatbuilder.xml" : {
			"boat_builder_window"         : _("boatbuilder")},
		"ingame_load.xml" : {
			"details_label"               : _(" Details:"),
			"deleteButton"                : _("Delete"),
			"cancelButton"                : _("Cancel"),
			"okButton"                    : _("Ok"),
			"load_game_window"            : _("Load game")},
		"gamemenu.xml" : {
			"start"                       : _("Return to Game"),
			"quit"                        : _(" Cancel Game "),
			"savegame"                    : _(" Save Game "),
			"loadgame"                    : _(" Load Game "),
			"help"                        : _(" Help "),
			"chimebell"                   : _(" Chime The Bell "),
			"settings"                    : _(" Settings ")},
		"hud_cityinfo.xml" : {
			"cityName"                    : _("City name"),
			"islandClass"                 : _("Class ROMAN"),
			"islandInhabitants"           : _("Inhabitants")},
		"hud_chat.xml" : {
			"chat_label"                  : _("Chat"),
			"sendButton"                  : _("Send")},
		"help.xml" : {
			"okButton"                    : _("Close"),
			"help_window"                 : _("Help")},
		"hud_fertility.xml" : {
			"fertility1"                  : _("?"),
			"fertility2"                  : _("?")},
		"general.xml" : {
			"language_label"              : _("Language:"),
			"autosave_interval_label"     : _("Autosave interval"),
			"number_of_autosaves_label"   : _("Number of saved autosaves:"),
			"number_of_quicksaves_label"  : _("Number of saved quicksaves:"),
			"minutes_label"               : _("minutes")},
		"settings.xml" : {
			"settings_dialog_title"       : _("This is the Unknown Horizons settings dialog. Please make sure that you know, what you do."),
			"showGeneral"                 : _("General"),
			"showGraphic"                 : _("Graphic"),
			"showAudio"                   : _("Audio"),
			"cancelButton"                : _("Cancel"),
			"okButton"                    : _("Ok")},
		"graphics.xml" : {
			"screen_resolution_label"     : _("Screen resolution:"),
			"use_renderer_label"          : _("Used renderer:"),
			"color_depth_label"           : _("Color depth:")},
		"audio.xml" : {
			"music_volume_label"          : _("Music volume:"),
			"effect_volume_label"         : _("Effects volume:")},
		"work_building_tab1.xml" : {
			"StockLabel"                  : _("stock")},
		"work_building_tab4.xml" : {
			"ProductionLabel"             : _("production")},
		"work_building_tab0.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"running_cost_label"          : _("Running Costs:"),
			"buy_sell_label"              : _("Buy/Sell Resources:")},
		"production_building_overview.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"running_costs_label"         : _("Running Costs:"),
			"toggle_label"                : _("Toggle active:")},
		"work_building_tab5.xml" : {
			"ResearchLabel"               : _("research")},
		"work_building_tab3.xml" : {
			"RouteLabel"                  : _("route")},
		"work_building_tab2.xml" : {
			"CombatLabel"                 : _("combat")},
		"tab_stock.xml" : {
			"headline"                    : _("Inventory of")},
		"tab_branch_overview.xml" : {
			"headline"                    : _("Building overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:"),
			"running_cost_label"          : _("Running Costs:"),
			"buy_sell_resource_label"     : _("Buy/Sell Resources:")},
		"tab_overview_ship.xml" : {
			"health_label"                : _("Health:")},
		"boatbuilder.xml" : {
			"current_construction_label"  : _("Current construction progress:")},
		"tab_boatbuilder_create.xml" : {
			"overview_label"              : _("Select a boat to build:"),
			"new_settlement_label"        : _("Build selected:")},
		"tab_stock_ship.xml" : {
			"headline"                    : _("Inventory"),
			"load_unload_label"           : _("Load/Unload:")},
		"tab_overview.xml" : {
			"headline"                    : _("Overview"),
			"name_label"                  : _("Name:"),
			"health_label"                : _("Health:")},
		"trade.xml" : {
			"headline"                    : _("Trade"),
			"ship_label"                  : _("Ship:"),
			"exchange_label"              : _("Exchange:"),
			"trade_with_label"            : _("Trade partner:")},
		"buysellmenu.xml" : {
			"headline"                    : _("Buy or sell ressources"),
			"legend_label"                : _("Legend:"),
			"buy_label"                   : _("Buy ressources"),
			"sell_label"                  : _("Sell ressources")},
		"resources.xml" : {
			"headline"                    : _("Select ressources to buy/sell:")},
		"hud_build_tab0.xml" : {
			"headline"                    : _("Build menu"),
			"residental_label"            : _("Residents and Infrastructural"),
			"service_label"               : _("Services"),
			"companies_label"             : _("Companies"),
			"military_label"              : _("Military")},
		"hud_builddetail.xml" : {
			"headline"                    : _("Build"),
			"running_cost_label"          : _("Running costs:")},
		"hud_tears_menu.xml" : {
			"ConfirmTearLabel"            : _("Do you want to remove this building?"),
			"accept-1"                    : _("yes"),
			"abort-1"                     : _("no")},
	}