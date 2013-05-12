# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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
# ./development/extract_strings_from_xml.py  horizons/i18n/guitranslations.py
#
# NOTE: In string-freeze mode (shortly before releases, usually
#       announced in a meeting), updates to this file must not happen
#       without permission of the responsible translation admin!
#
###############################################################################

from horizons.constants import VERSION

text_translations = {}

def set_translations():
	global text_translations
	text_translations = {

	'stringpreviewwidget.xml' : {
		},

	'editor_pause_menu.xml' : {
		(u'help'                         , 'text'    ): _("Help"),
		(u'loadgame'                     , 'text'    ): _("Load map"),
		(u'quit'                         , 'text'    ): _("Exit editor"),
		(u'savegame'                     , 'text'    ): _("Save map"),
		(u'settings'                     , 'text'    ): _("Settings"),
		(u'start'                        , 'text'    ): _("Return to editor"),
		},

	'editor_settings.xml' : {
		(u'cursor_hint'                  , 'text'    ): _("(right click to stop)"),
		(u'headline_brush_size'          , 'text'    ): _("Select brush size:"),
		(u'headline_terrain'             , 'text'    ): _("Select terrain:"),
		},

	'buildtab.xml' : {
		},

	'buildtab_no_settlement.xml' : {
		(u'headline'                     , 'text'    ): _("Game start"),
		(u'howto_1_need_warehouse'       , 'text'    ): _("You need to found a settlement before you can construct buildings!"),
		(u'howto_2_navigate_ship'        , 'text'    ): _("Select your ship and approach the coast via right-click."),
		(u'howto_3_build_warehouse'      , 'text'    ): _("Afterwards, press the large button in the ship overview tab."),
		},

	'place_building.xml' : {
		(u'headline'                     , 'text'    ): _("Build"),
		(u'running_costs_label'          , 'text'    ): _("Running costs:"),
		},

	'related_buildings.xml' : {
		(u'headline'                     , 'text'    ): _("Related buildings"),
		},

	'city_info.xml' : {
		(u'city_info_inhabitants'        , 'helptext'): _("Inhabitants"),
		},

	'messagewidget_icon.xml' : {
		},

	'messagewidget_message.xml' : {
		},

	'minimap.xml' : {
		(u'build'                        , 'helptext'): _("Build menu (B)"),
		(u'destroy_tool'                 , 'helptext'): _("Destroy (X)"),
		(u'diplomacyButton'              , 'helptext'): _("Diplomacy"),
		(u'gameMenuButton'               , 'helptext'): _("Game menu (Esc)"),
		(u'logbook'                      , 'helptext'): _("Captain's log (L)"),
		(u'rotateLeft'                   , 'helptext'): _("Rotate map counterclockwise (,)"),
		(u'rotateRight'                  , 'helptext'): _("Rotate map clockwise (.)"),
		(u'speedDown'                    , 'helptext'): _("Decrease game speed (-)"),
		(u'speedUp'                      , 'helptext'): _("Increase game speed (+)"),
		(u'zoomIn'                       , 'helptext'): _("Zoom in"),
		(u'zoomOut'                      , 'helptext'): _("Zoom out"),
		},

	'resource_overview_bar_entry.xml' : {
		},

	'resource_overview_bar_gold.xml' : {
		},

	'resource_overview_bar_stats.xml' : {
		},

	'change_name.xml' : {
		(u'enter_new_name_lbl'           , 'text'    ): _("Enter new name:"),
		(u'headline_change_name'         , 'text'    ): _("Change name"),
		(u'old_name_label'               , 'text'    ): _("Old name:"),
		(u'okButton'                     , 'helptext'): _("Apply the new name"),
		},

	'chat.xml' : {
		(u'chat_lbl'                     , 'text'    ): _("Enter your message:"),
		(u'headline'                     , 'text'    ): _("Chat"),
		},

	'boatbuilder.xml' : {
		(u'BB_cancel_build_label'        , 'text'    ): _("Cancel building:"),
		(u'BB_cancel_warning_label'      , 'text'    ): _("(lose all resources)"),
		(u'BB_current_order'             , 'text'    ): _("Currently building:"),
		(u'BB_howto_build_lbl'           , 'text'    ): _("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
		(u'BB_needed_res_label'          , 'text'    ): _("Resources still needed:"),
		(u'BB_progress_label'            , 'text'    ): _("Construction progress:"),
		(u'BB_cancel_button'             , 'helptext'): _("Cancel all building progress"),
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		(u'toggle_active_active'         , 'helptext'): _("Pause"),
		(u'toggle_active_inactive'       , 'helptext'): _("Resume"),
		},

	'boatbuilder_showcase.xml' : {
		},

	'diplomacy.xml' : {
		(u'ally_label'                   , 'text'    ): _("ally"),
		(u'enemy_label'                  , 'text'    ): _("enemy"),
		(u'neutral_label'                , 'text'    ): _("neutral"),
		},

	'overview_farm.xml' : {
		(u'headline'                     , 'text'    ): _("Building overview"),
		(u'capacity_utilization_label'   , 'helptext'): _("Capacity utilization"),
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		(u'capacity_utilization'         , 'helptext'): _("Capacity utilization"),
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'island_inventory.xml' : {
		(u'headline'                     , 'text'    ): _("Settlement inventory"),
		},

	'mainsquare_inhabitants.xml' : {
		(u'headline'                     , 'text'    ): _("Settler overview"),
		(u'headline_happiness_per_house' , 'text'    ): _("Happiness per house"),
		(u'headline_residents_per_house' , 'text'    ): _("Residents per house"),
		(u'headline_residents_total'     , 'text'    ): _("Summary"),
		(u'houses'                       , 'text'    ): _("houses"),
		(u'residents'                    , 'text'    ): _("residents"),
		(u'tax_label'                    , 'text'    ): _("Taxes:"),
		(u'upgrades_lbl'                 , 'text'    ): _("Upgrade permissions:"),
		(u'avg_icon'                     , 'helptext'): _("satisfied"),
		(u'happiness_house_icon'         , 'helptext'): _("Amount of houses with this happiness"),
		(u'happy_icon'                   , 'helptext'): _("happy"),
		(u'houses_icon'                  , 'helptext'): _("Houses with this amount of inhabitants"),
		(u'inhabitants_icon'             , 'helptext'): _("Number of inhabitants per house"),
		(u'paid_taxes_icon'              , 'helptext'): _("Paid taxes"),
		(u'sad_icon'                     , 'helptext'): _("sad"),
		(u'tax_rate_icon'                , 'helptext'): _("Tax rate"),
		(u'tax_val_label'                , 'helptext'): _("Tax rate"),
		(u'taxes'                        , 'helptext'): _("Paid taxes"),
		},

	'overview_enemybuilding.xml' : {
		},

	'overview_enemyunit.xml' : {
		},

	'overview_enemywarehouse.xml' : {
		(u'buying_label'                 , 'text'    ): _("Buying"),
		(u'selling_label'                , 'text'    ): _("Selling"),
		},

	'overview_firestation.xml' : {
		(u'headline'                     , 'text'    ): _("Building overview"),
		(u'name_label'                   , 'text'    ): _("Name:"),
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_groundunit.xml' : {
		(u'lbl_weapon_storage'           , 'text'    ): _("Weapons:"),
		},

	'overview_productionbuilding.xml' : {
		(u'capacity_utilization_label'   , 'helptext'): _("Capacity utilization"),
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		(u'capacity_utilization'         , 'helptext'): _("Capacity utilization"),
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_resourcedeposit.xml' : {
		(u'headline'                     , 'text'    ): _("Resource deposit"),
		(u'res_dep_description_lbl'      , 'text'    ): _("This is a resource deposit where you can build a mine to dig up resources."),
		(u'res_dep_description_lbl2'     , 'text'    ): _("It contains these resources:"),
		},

	'overview_settler.xml' : {
		(u'needed_res_label'             , 'text'    ): _("Needed resources:"),
		(u'tax_label'                    , 'text'    ): _("Taxes:"),
		(u'happiness_label'              , 'helptext'): _("Happiness"),
		(u'paid_taxes_label'             , 'helptext'): _("Paid taxes"),
		(u'paid_taxes_label'             , 'helptext'): _("Tax rate"),
		(u'residents_label'              , 'helptext'): _("Residents"),
		(u'inhabitants'                  , 'helptext'): _("Residents"),
		(u'tax_val_label'                , 'helptext'): _("Tax rate"),
		(u'taxes'                        , 'helptext'): _("Paid taxes"),
		(u'happiness'                    , 'helptext'): _("Happiness"),
		},

	'overview_signalfire.xml' : {
		(u'signal_fire_description_lbl'  , 'text'    ): _("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods."),
		},

	'overview_tower.xml' : {
		(u'name_label'                   , 'text'    ): _("Name:"),
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_tradership.xml' : {
		(u'trader_description_lbl'       , 'text'    ): _("This is the free trader's ship. It will visit you from time to time to buy or sell goods."),
		},

	'overview_warehouse.xml' : {
		(u'name_label'                   , 'text'    ): _("Name:"),
		(u'collector_utilization_label'  , 'helptext'): _("Collector utilization"),
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		(u'collector_utilization'        , 'helptext'): _("Collector utilization"),
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overviewtab.xml' : {
		},

	'overview_select_multi.xml' : {
		},

	'unit_entry_widget.xml' : {
		},

	'overview_trade_ship.xml' : {
		(u'configure_route'              , 'helptext'): _("Configure trading route"),
		(u'found_settlement'             , 'helptext'): _("Build settlement"),
		(u'trade'                        , 'helptext'): _("Trade"),
		},

	'overview_war_ship.xml' : {
		(u'configure_route'              , 'helptext'): _("Configure trading route"),
		(u'found_settlement'             , 'helptext'): _("Build settlement"),
		(u'trade'                        , 'helptext'): _("Trade"),
		},

	'tradetab.xml' : {
		(u'buying_label'                 , 'text'    ): _("Buying"),
		(u'exchange_label'               , 'text'    ): _("Exchange:"),
		(u'headline'                     , 'text'    ): _("Trade"),
		(u'selling_label'                , 'text'    ): _("Selling"),
		(u'ship_label'                   , 'text'    ): _("Ship:"),
		(u'trade_with_label'             , 'text'    ): _("Trade partner:"),
		},

	'tab_base.xml' : {
		},

	'buysellmenu.xml' : {
		(u'headline'                     , 'text'    ): _("Buy or sell resources"),
		(u'headline_trade_history'       , 'text'    ): _("Trade history"),
		},

	'select_trade_resource.xml' : {
		(u'headline'                     , 'text'    ): _("Select resources:"),
		},

	'tab_account.xml' : {
		(u'buy_expenses_label'           , 'text'    ): _("Buying"),
		(u'headline_balance_label'       , 'text'    ): _("Balance:"),
		(u'headline_expenses_label'      , 'text'    ): _("Expenses:"),
		(u'headline_income_label'        , 'text'    ): _("Income:"),
		(u'running_costs_label'          , 'text'    ): _("Running costs"),
		(u'sell_income_label'            , 'text'    ): _("Sale"),
		(u'taxes_label'                  , 'text'    ): _("Taxes"),
		(u'show_production_overview'     , 'helptext'): _("Show resources produced in this settlement"),
		},

	'trade_single_slot.xml' : {
		},

	'overview_farmproductionline.xml' : {
		(u'toggle_active_active'         , 'helptext'): _("Pause production"),
		(u'toggle_active_inactive'       , 'helptext'): _("Start production"),
		},

	'overview_productionline.xml' : {
		(u'toggle_active_active'         , 'helptext'): _("Pause production"),
		(u'toggle_active_inactive'       , 'helptext'): _("Start production"),
		},

	'related_buildings_container.xml' : {
		},

	'resbar_resource_selection.xml' : {
		(u'headline'                     , 'text'    ): _("Select resource:"),
		(u'make_default_btn'             , 'helptext'): _("Save current resource configuration as default for all settlements."),
		(u'reset_default_btn'            , 'helptext'): _("Reset default resource configuration for all settlements."),
		(u'headline'                     , 'helptext'): _("The resource you select is displayed instead of the current one. Empty by clicking on X."),
		},

	'route_entry.xml' : {
		(u'delete_warehouse'             , 'helptext'): _("Delete entry"),
		(u'move_down'                    , 'helptext'): _("Move down"),
		(u'move_up'                      , 'helptext'): _("Move up"),
		},

	'trade_history_item.xml' : {
		},

	'traderoute_resource_selection.xml' : {
		(u'select_res_label'             , 'text'    ): _("Select a resource:"),
		},

	'captains_log.xml' : {
		(u'stats_players'                , 'text'    ): _("Players"),
		(u'stats_settlements'            , 'text'    ): _("My settlements"),
		(u'stats_ships'                  , 'text'    ): _("My ships"),
		(u'weird_button_1'               , 'text'    ): _("Whole world"),
		(u'weird_button_4'               , 'text'    ): _("Everybody"),
		(u'headline_chat'                , 'text'    ): _("Chat"),
		(u'headline_game_messages'       , 'text'    ): _("Game messages"),
		(u'headline_statistics'          , 'text'    ): _("Statistics"),
		(u'okButton'                     , 'helptext'): _("Return to game"),
		(u'weird_button_4'               , 'helptext'): _("Sends the chat messages to all players."),
		(u'backwardButton'               , 'helptext'): _("Read previous entries"),
		(u'forwardButton'                , 'helptext'): _("Read next entries"),
		},

	'configure_route.xml' : {
		(u'lbl_route_activity'           , 'text'    ): _("Route activity:"),
		(u'lbl_wait_at_load'             , 'text'    ): _("Wait at load:"),
		(u'lbl_wait_at_unload'           , 'text'    ): _("Wait at unload:"),
		(u'okButton'                     , 'helptext'): _("Exit"),
		(u'start_route'                  , 'helptext'): _("Start route"),
		},

	'healthwidget.xml' : {
		},

	'island_production.xml' : {
		(u'okButton'                     , 'helptext'): _("Close"),
		},

	'players_overview.xml' : {
		(u'building_score'               , 'text'    ): _("Buildings"),
		(u'headline'                     , 'text'    ): _("Player scores"),
		(u'land_score'                   , 'text'    ): _("Land"),
		(u'money_score'                  , 'text'    ): _("Money"),
		(u'player_name'                  , 'text'    ): _("Name"),
		(u'resource_score'               , 'text'    ): _("Resources"),
		(u'settler_score'                , 'text'    ): _("Settlers"),
		(u'total_score'                  , 'text'    ): _("Total"),
		(u'unit_score'                   , 'text'    ): _("Units"),
		(u'building_score'               , 'helptext'): _("Value of all the buildings in the player's settlement(s)"),
		(u'land_score'                   , 'helptext'): _("Value of usable land i.e Amount of Land that can be used to create buildings "),
		(u'money_score'                  , 'helptext'): _("Player's current treasury + income expected in near future"),
		(u'player_name'                  , 'helptext'): _("Player Name"),
		(u'resource_score'               , 'helptext'): _("Value of resources generated from all the possible sources in the player's settlement(s)"),
		(u'settler_score'                , 'helptext'): _("Value denoting the progress of the settlement(s) in terms of inhabitants, buildings and overall happiness"),
		(u'total_score'                  , 'helptext'): _("The total value from all individual entities or in short : Total Player Score"),
		(u'unit_score'                   , 'helptext'): _("Value of all the units owned by the player"),
		},

	'players_settlements.xml' : {
		(u'balance'                      , 'text'    ): _("Balance"),
		(u'inhabitants'                  , 'text'    ): _("Inhabitants"),
		(u'running_costs'                , 'text'    ): _("Running costs"),
		(u'settlement_name'              , 'text'    ): _("Name"),
		(u'taxes'                        , 'text'    ): _("Taxes"),
		},

	'ships_list.xml' : {
		(u'health'                       , 'text'    ): _("Health"),
		(u'ship_name'                    , 'text'    ): _("Name"),
		(u'ship_type'                    , 'text'    ): _("Type"),
		(u'status'                       , 'text'    ): _("Status"),
		(u'weapons'                      , 'text'    ): _("Weapons"),
		},

	'stancewidget.xml' : {
		(u'aggressive_stance'            , 'helptext'): _("Aggressive"),
		(u'flee_stance'                  , 'helptext'): _("Flee"),
		(u'hold_ground_stance'           , 'helptext'): _("Hold ground"),
		(u'none_stance'                  , 'helptext'): _("Passive"),
		},

	'credits.xml' : {
		},

	'editor_create_map.xml' : {
		(u'headline_choose_map_size_lbl' , 'text'    ): _("Choose a map size:"),
		},

	'editor_select_map.xml' : {
		(u'headline_choose_map_lbl'      , 'text'    ): _("Choose a map:"),
		},

	'editor_select_saved_game.xml' : {
		(u'headline_choose_saved_game'   , 'text'    ): _("Choose a saved game's map:"),
		},

	'editor_start_menu.xml' : {
		(u'headline'                     , 'text'    ): _("Select map source"),
		(u'create_new_map'               , 'text'    ): _("Create new map"),
		(u'load_existing_map'            , 'text'    ): _("Load existing map"),
		(u'load_saved_game_map'          , 'text'    ): _("Load saved game's map"),
		(u'cancel'                       , 'helptext'): _("Exit to main menu"),
		(u'okay'                         , 'helptext'): _("Start editor"),
		},

	'help.xml' : {
		(u'headline'                     , 'text'    ): _("Key bindings"),
		(u'lbl_BUILD_TOOL'               , 'text'    ): _("Show build menu"),
		(u'lbl_CHAT'                     , 'text'    ): _("Chat"),
		(u'lbl_CONSOLE'                  , 'text'    ): _("Display FPS counter"),
		(u'lbl_COORD_TOOLTIP'            , 'text'    ): _("Show coordinate values (Debug)"),
		(u'lbl_DESTROY_TOOL'             , 'text'    ): _("Enable destruct mode"),
		(u'lbl_DOWN'                     , 'text'    ): _("Scroll down"),
		(u'lbl_ESCAPE'                   , 'text'    ): _("Close dialogs"),
		(u'lbl_GRID'                     , 'text'    ): _("Toggle grid on/off"),
		(u'lbl_HEALTH_BAR'               , 'text'    ): _("Toggle health bars"),
		(u'lbl_HELP'                     , 'text'    ): _("Display help"),
		(u'lbl_LEFT'                     , 'text'    ): _("Scroll left"),
		(u'lbl_LOGBOOK'                  , 'text'    ): _("Toggle Captain's log"),
		(u'lbl_PAUSE'                    , 'text'    ): _("Pause game"),
		(u'lbl_PIPETTE'                  , 'text'    ): _("Enable pipette mode (clone buildings)"),
		(u'lbl_PLAYERS_OVERVIEW'         , 'text'    ): _("Show player scores"),
		(u'lbl_QUICKLOAD'                , 'text'    ): _("Quickload"),
		(u'lbl_QUICKSAVE'                , 'text'    ): _("Quicksave"),
		(u'lbl_REMOVE_SELECTED'          , 'text'    ): _("Remove selected units / buildings"),
		(u'lbl_RIGHT'                    , 'text'    ): _("Scroll right"),
		(u'lbl_ROAD_TOOL'                , 'text'    ): _("Enable road building mode"),
		(u'lbl_ROTATE_LEFT'              , 'text'    ): _("Rotate building or map counterclockwise"),
		(u'lbl_ROTATE_RIGHT'             , 'text'    ): _("Rotate building or map clockwise"),
		(u'lbl_SCREENSHOT'               , 'text'    ): _("Screenshot"),
		(u'lbl_SETTLEMENTS_OVERVIEW'     , 'text'    ): _("Show settlement list"),
		(u'lbl_SHIFT'                    , 'text'    ): _("Hold to place multiple buildings"),
		(u'lbl_SHIPS_OVERVIEW'           , 'text'    ): _("Show ship list"),
		(u'lbl_SHOW_SELECTED'            , 'text'    ): _("Focus camera on selection"),
		(u'lbl_SPEED_DOWN'               , 'text'    ): _("Decrease game speed"),
		(u'lbl_SPEED_UP'                 , 'text'    ): _("Increase game speed"),
		(u'lbl_TILE_OWNER_HIGHLIGHT'     , 'text'    ): _("Highlight tile ownership"),
		(u'lbl_TRANSLUCENCY'             , 'text'    ): _("Toggle translucency of ambient buildings"),
		(u'lbl_UP'                       , 'text'    ): _("Scroll up"),
		(u'okButton'                     , 'helptext'): _("Return"),
		},

	'hotkeys.xml' : {
		(u'reset_to_default'             , 'text'    ): _("Reset to default keys"),
		(u'labels_headline'              , 'text'    ): _("Actions"),
		(u'primary_buttons_headline'     , 'text'    ): _("Primary"),
		(u'secondary_buttons_headline'   , 'text'    ): _("Secondary"),
		(u'okButton'                     , 'helptext'): _("Exit to main menu"),
		(u'reset_to_default'             , 'helptext'): _("Reset to default"),
		(u'lbl_BUILD_TOOL'               , 'helptext'): _("Show build menu"),
		(u'lbl_CHAT'                     , 'helptext'): _("Chat"),
		(u'lbl_CONSOLE'                  , 'helptext'): _("Toggle showing FPS on/off"),
		(u'lbl_COORD_TOOLTIP'            , 'helptext'): _("Show coordinate values (Debug)"),
		(u'lbl_DESTROY_TOOL'             , 'helptext'): _("Enable destruct mode"),
		(u'lbl_DOWN'                     , 'helptext'): _("Scroll down"),
		(u'lbl_GRID'                     , 'helptext'): _("Toggle grid on/off"),
		(u'lbl_HEALTH_BAR'               , 'helptext'): _("Toggle health bars"),
		(u'lbl_HELP'                     , 'helptext'): _("Display help"),
		(u'lbl_LEFT'                     , 'helptext'): _("Scroll left"),
		(u'lbl_LOGBOOK'                  , 'helptext'): _("Toggle Captain's log"),
		(u'lbl_PAUSE'                    , 'helptext'): _("Pause game"),
		(u'lbl_PIPETTE'                  , 'helptext'): _("Enable pipette mode (clone buildings)"),
		(u'lbl_PLAYERS_OVERVIEW'         , 'helptext'): _("Show player scores"),
		(u'lbl_QUICKLOAD'                , 'helptext'): _("Quickload"),
		(u'lbl_QUICKSAVE'                , 'helptext'): _("Quicksave"),
		(u'lbl_REMOVE_SELECTED'          , 'helptext'): _("Remove selected units / buildings"),
		(u'lbl_RIGHT'                    , 'helptext'): _("Scroll right"),
		(u'lbl_ROAD_TOOL'                , 'helptext'): _("Enable road building mode"),
		(u'lbl_ROTATE_LEFT'              , 'helptext'): _("Rotate building or map counterclockwise"),
		(u'lbl_ROTATE_RIGHT'             , 'helptext'): _("Rotate building or map clockwise"),
		(u'lbl_SCREENSHOT'               , 'helptext'): _("Screenshot"),
		(u'lbl_SETTLEMENTS_OVERVIEW'     , 'helptext'): _("Show settlement list"),
		(u'lbl_SHIPS_OVERVIEW'           , 'helptext'): _("Show ship list"),
		(u'lbl_SHOW_SELECTED'            , 'helptext'): _("Focus camera on selection"),
		(u'lbl_SPEED_DOWN'               , 'helptext'): _("Decrease game speed"),
		(u'lbl_SPEED_UP'                 , 'helptext'): _("Increase game speed"),
		(u'lbl_TILE_OWNER_HIGHLIGHT'     , 'helptext'): _("Highlight tile ownership"),
		(u'lbl_TRANSLUCENCY'             , 'helptext'): _("Toggle translucency of ambient buildings"),
		(u'lbl_UP'                       , 'helptext'): _("Scroll up"),
		},

	'ingamemenu.xml' : {
		(u'help'                         , 'text'    ): _("Help"),
		(u'loadgame'                     , 'text'    ): _("Load game"),
		(u'quit'                         , 'text'    ): _("Cancel game"),
		(u'savegame'                     , 'text'    ): _("Save game"),
		(u'settings'                     , 'text'    ): _("Settings"),
		(u'start'                        , 'text'    ): _("Return to game"),
		},

	'loadingscreen.xml' : {
		(u'loading_label'                , 'text'    ): _("Loading ..."),
		},

	'mainmenu.xml' : {
		(u'credits_label'                , 'text'    ): _("Credits"),
		(u'editor_label'                 , 'text'    ): _("Editor"),
		(u'help_label'                   , 'text'    ): _("Help"),
		(u'load_label'                   , 'text'    ): _("Load game"),
		(u'multi_label'                  , 'text'    ): _("Multiplayer"),
		(u'quit_label'                   , 'text'    ): _("Quit"),
		(u'settings_label'               , 'text'    ): _("Settings"),
		(u'single_label'                 , 'text'    ): _("Singleplayer"),
		(u'version_label'                , 'text'    ): VERSION.string(),
		},

	'multiplayer_creategame.xml' : {
		(u'create_game_lbl'              , 'text'    ): _("Create game:"),
		(u'exit_to_mp_menu_lbl'          , 'text'    ): _("Back:"),
		(u'gamename_lbl'                 , 'text'    ): _("Name of the game:"),
		(u'headline'                     , 'text'    ): _("Choose a map:"),
		(u'headline'                     , 'text'    ): _("Create game - Multiplayer"),
		(u'mp_player_limit_lbl'          , 'text'    ): _("Player limit:"),
		(u'password_lbl'                 , 'text'    ): _("Password of the game:"),
		(u'cancel'                       , 'helptext'): _("Exit to multiplayer menu"),
		(u'create'                       , 'helptext'): _("Create this new game"),
		(u'gamename_lbl'                 , 'helptext'): _("This will be displayed to other players so they recognize the game."),
		(u'password_lbl'                 , 'helptext'): _("This game's password. Required to join this game."),
		},

	'multiplayer_gamelobby.xml' : {
		(u'exit_to_mp_menu_lbl'          , 'text'    ): _("Leave:"),
		(u'game_player_color'            , 'text'    ): _("Color"),
		(u'game_player_status'           , 'text'    ): _("Status"),
		(u'game_start_notice'            , 'text'    ): _("The game will start as soon as all players are ready."),
		(u'headline'                     , 'text'    ): _("Chat:"),
		(u'headline'                     , 'text'    ): _("Gamelobby"),
		(u'ready_lbl'                    , 'text'    ): _("Ready:"),
		(u'startmessage'                 , 'text'    ): _("Game details:"),
		(u'cancel'                       , 'helptext'): _("Exit gamelobby"),
		(u'ready_btn'                    , 'helptext'): _("Sets your state to ready (necessary for the game to start)"),
		},

	'multiplayermenu.xml' : {
		(u'create_game_lbl'              , 'text'    ): _("Create game:"),
		(u'exit_to_main_menu_lbl'        , 'text'    ): _("Main menu:"),
		(u'headline_active_games_lbl'    , 'text'    ): _("Active games:"),
		(u'headline_left'                , 'text'    ): _("New game - Multiplayer"),
		(u'join_game_lbl'                , 'text'    ): _("Join game"),
		(u'load_game_lbl'                , 'text'    ): _("Load game:"),
		(u'refr_gamelist_lbl'            , 'text'    ): _("Refresh list:"),
		(u'cancel'                       , 'helptext'): _("Exit to main menu"),
		(u'create'                       , 'helptext'): _("Create a new game"),
		(u'join'                         , 'helptext'): _("Join the selected game"),
		(u'load'                         , 'helptext'): _("Load a saved game"),
		(u'refresh'                      , 'helptext'): _("Refresh list of active games"),
		},

	'set_player_details.xml' : {
		(u'headline_set_player_details'  , 'text'    ): _("Change player details"),
		},

	'settings.xml' : {
		(u'reset_mouse_sensitivity'      , 'text'    ): _("Reset to default"),
		(u'auto_unload_label'            , 'text'    ): _("Auto-unload ship:"),
		(u'autosave_interval_label'      , 'text'    ): _("Autosave interval in minutes:"),
		(u'color_depth_label'            , 'text'    ): _("Color depth:"),
		(u'cursor_centered_zoom_label'   , 'text'    ): _("Cursor centered zoom:"),
		(u'debug_log_lbl'                , 'text'    ): _("Enable logging:"),
		(u'edge_scrolling_label'         , 'text'    ): _("Scroll at map edge:"),
		(u'effect_volume_label'          , 'text'    ): _("Effects volume:"),
		(u'fps_label'                    , 'text'    ): _("Frame rate limit:"),
		(u'headline_graphics'            , 'text'    ): _("Graphics"),
		(u'headline_language'            , 'text'    ): _("Language"),
		(u'headline_misc'                , 'text'    ): _("General"),
		(u'headline_mouse'               , 'text'    ): _("Mouse"),
		(u'headline_network'             , 'text'    ): _("Network"),
		(u'headline_saving'              , 'text'    ): _("Saving"),
		(u'headline_sound'               , 'text'    ): _("Sound"),
		(u'middle_mouse_pan_lbl'         , 'text'    ): _("Middle mouse button pan:"),
		(u'minimap_rotation_label'       , 'text'    ): _("Rotate minimap with map:"),
		(u'mouse_sensitivity_label'      , 'text'    ): _("Mouse sensitivity:"),
		(u'music_volume_label'           , 'text'    ): _("Music volume:"),
		(u'network_port_lbl'             , 'text'    ): _("Network port:"),
		(u'number_of_autosaves_label'    , 'text'    ): _("Number of autosaves:"),
		(u'number_of_quicksaves_label'   , 'text'    ): _("Number of quicksaves:"),
		(u'quote_type_label'             , 'text'    ): _("Choose a quote type:"),
		(u'screen_fullscreen_text'       , 'text'    ): _("Full screen:"),
		(u'screen_resolution_label'      , 'text'    ): _("Screen resolution:"),
		(u'scroll_speed_label'           , 'text'    ): _("Scroll delay:"),
		(u'show_resource_icons_lbl'      , 'text'    ): _("Production indicators:"),
		(u'sound_enable_opt_text'        , 'text'    ): _("Enable sound:"),
		(u'uninterrupted_building_label' , 'text'    ): _("Uninterrupted building:"),
		(u'use_renderer_label'           , 'text'    ): _("Used renderer:"),
		(u'cancelButton'                 , 'helptext'): _("Discard current changes"),
		(u'defaultButton'                , 'helptext'): _("Reset to default settings"),
		(u'okButton'                     , 'helptext'): _("Apply"),
		(u'auto_unload_label'            , 'helptext'): _("Whether to unload the ship after founding a settlement"),
		(u'color_depth_label'            , 'helptext'): _("If set to 0, use the driver default"),
		(u'cursor_centered_zoom_label'   , 'helptext'): _("When enabled, mouse wheel zoom will use the cursor position as new viewport center. When disabled, always zoom to current viewport center."),
		(u'debug_log_lbl'                , 'helptext'): _("Don't use in normal game session. Decides whether to write debug information in the logging directory of your user directory. Slows the game down."),
		(u'edge_scrolling_label'         , 'helptext'): _("Whether to move the viewport when the mouse pointer is close to map edges"),
		(u'fps_label'                    , 'helptext'): _("Set the maximum frame rate used. Default: 60 fps."),
		(u'middle_mouse_pan_lbl'         , 'helptext'): _("When enabled, dragging the middle mouse button will pan the camera"),
		(u'minimap_rotation_label'       , 'helptext'): _("Whether to also rotate the minimap whenever the regular map is rotated"),
		(u'mouse_sensitivity_label'      , 'helptext'): _("0 is default system settings"),
		(u'network_port_lbl'             , 'helptext'): _("If set to 0, use the router default"),
		(u'quote_type_label'             , 'helptext'): _("What kind of quote to display while loading a game"),
		(u'scroll_speed_label'           , 'helptext'): _("Higher values slow down scrolling."),
		(u'show_resource_icons_lbl'      , 'helptext'): _("Whether to show resource icons over buildings whenever they finish production"),
		(u'uninterrupted_building_label' , 'helptext'): _("When enabled, do not exit the build mode after successful construction"),
		(u'use_renderer_label'           , 'helptext'): _("SDL is only meant as unsupported fallback and might cause problems!"),
		},

	'select_savegame.xml' : {
		(u'enter_filename_label'         , 'text'    ): _("Enter filename:"),
		(u'gamename_lbl'                 , 'text'    ): _("Name of the game:"),
		(u'gamepassword_lbl'             , 'text'    ): _("Password of the game:"),
		(u'headline_details_label'       , 'text'    ): _("Details:"),
		(u'headline_saved_games_label'   , 'text'    ): _("Your saved games:"),
		(u'cancelButton'                 , 'helptext'): _("Cancel"),
		(u'deleteButton'                 , 'helptext'): _("Delete selected savegame"),
		(u'gamename_lbl'                 , 'helptext'): _("This will be displayed to other players so they recognize the game."),
		(u'gamepassword_lbl'             , 'helptext'): _("Password of the game. Required to join this game"),
		},

	'singleplayermenu.xml' : {
		(u'headline'                     , 'text'    ): _("New game - Singleplayer"),
		(u'main_menu_label'              , 'text'    ): _("Main menu:"),
		(u'start_game_label'             , 'text'    ): _("Start game:"),
		(u'free_maps'                    , 'text'    ): _("Free play"),
		(u'random'                       , 'text'    ): _("Random map"),
		(u'scenario'                     , 'text'    ): _("Scenario"),
		(u'cancel'                       , 'helptext'): _("Exit to main menu"),
		(u'okay'                         , 'helptext'): _("Start game"),
		},

	'sp_free_maps.xml' : {
		(u'headline_choose_map_lbl'      , 'text'    ): _("Choose a map to play:"),
		},

	'sp_random.xml' : {
		(u'headline_map_settings_lbl'    , 'text'    ): _("Map settings:"),
		(u'seed_string_lbl'              , 'text'    ): _("Seed:"),
		},

	'sp_scenario.xml' : {
		(u'choose_map_lbl'               , 'text'    ): _("Choose a map to play:"),
		(u'select_lang_lbl'              , 'text'    ): _("Select a language:"),
		},

	'aidataselection.xml' : {
		(u'ai_players_label'             , 'text'    ): _("AI players:"),
		},

	'game_settings.xml' : {
		(u'headline_game_settings_lbl'   , 'text'    ): _("Game settings:"),
		(u'lbl_disasters'                , 'text'    ): _("Disasters"),
		(u'lbl_free_trader'              , 'text'    ): _("Free Trader"),
		(u'lbl_pirates'                  , 'text'    ): _("Pirates"),
		},

	'playerdataselection.xml' : {
		(u'color_label'                  , 'text'    ): _("Color:"),
		(u'player_label'                 , 'text'    ): _("Player name:"),
		},

	'popup_230.xml' : {
		},

	'popup_290.xml' : {
		},

	'popup_350.xml' : {
		},

	'startup_error_popup.xml' : {
		},

	}
