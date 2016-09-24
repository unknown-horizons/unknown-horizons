# Encoding: utf-8
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
# ./development/extract_strings_from_xml.py  horizons/gui/translations.py
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
		('help'                         , 'text'    ): _("Help"),
		('loadgame'                     , 'text'    ): _("Load map"),
		('quit'                         , 'text'    ): _("Exit editor"),
		('savegame'                     , 'text'    ): _("Save map"),
		('settings'                     , 'text'    ): _("Settings"),
		('start'                        , 'text'    ): _("Return to editor"),
		},

	'editor_settings.xml' : {
		('cursor_hint'                  , 'text'    ): _("(right click to stop)"),
		('headline_brush_size'          , 'text'    ): _("Select brush size:"),
		('headline_terrain'             , 'text'    ): _("Select terrain:"),
		},

	'buildtab.xml' : {
		},

	'buildtab_no_settlement.xml' : {
		('headline'                     , 'text'    ): _("Game start"),
		('howto_1_need_warehouse'       , 'text'    ): _("You need to found a settlement before you can construct buildings!"),
		('howto_2_navigate_ship'        , 'text'    ): _("Select your ship and approach the coast via right-click."),
		('howto_3_build_warehouse'      , 'text'    ): _("Afterwards, press the large button in the ship overview tab."),
		},

	'place_building.xml' : {
		('headline'                     , 'text'    ): _("Build"),
		('running_costs_label'          , 'text'    ): _("Running costs:"),
		},

	'related_buildings.xml' : {
		('headline'                     , 'text'    ): _("Related buildings"),
		},

	'city_info.xml' : {
		('city_info_inhabitants'        , 'helptext'): _("Inhabitants"),
		},

	'messagewidget_icon.xml' : {
		},

	'messagewidget_message.xml' : {
		},

	'minimap.xml' : {
		('build'                        , 'helptext'): _("Build menu ({key})"),
		('destroy_tool'                 , 'helptext'): _("Destroy ({key})"),
		('diplomacyButton'              , 'helptext'): _("Diplomacy"),
		('gameMenuButton'               , 'helptext'): _("Game menu ({key})"),
		('logbook'                      , 'helptext'): _("Captain's log ({key})"),
		('rotateLeft'                   , 'helptext'): _("Rotate map counterclockwise ({key})"),
		('rotateRight'                  , 'helptext'): _("Rotate map clockwise ({key})"),
		('speedDown'                    , 'helptext'): _("Decrease game speed ({key})"),
		('speedUp'                      , 'helptext'): _("Increase game speed ({key})"),
		('zoomIn'                       , 'helptext'): _("Zoom in"),
		('zoomOut'                      , 'helptext'): _("Zoom out"),
		},

	'resource_overview_bar_entry.xml' : {
		},

	'resource_overview_bar_gold.xml' : {
		},

	'resource_overview_bar_stats.xml' : {
		},

	'change_name.xml' : {
		('enter_new_name_lbl'           , 'text'    ): _("Enter new name:"),
		('headline_change_name'         , 'text'    ): _("Change name"),
		('old_name_label'               , 'text'    ): _("Old name:"),
		('okButton'                     , 'helptext'): _("Apply the new name"),
		},

	'chat.xml' : {
		('chat_lbl'                     , 'text'    ): _("Enter your message:"),
		('headline'                     , 'text'    ): _("Chat"),
		},

	'barracks.xml' : {
		('UB_cancel_build_label'        , 'text'    ): _("Cancel building:"),
		('UB_cancel_warning_label'      , 'text'    ): _("(lose all resources)"),
		('UB_current_order'             , 'text'    ): _("Currently building:"),
		('UB_howto_build_lbl'           , 'text'    ): _("To build a groundunit, click on one of the class tabs, select the desired groundunit and confirm the order."),
		('UB_needed_res_label'          , 'text'    ): _("Resources still needed:"),
		('UB_progress_label'            , 'text'    ): _("Construction progress:"),
		('UB_cancel_button'             , 'helptext'): _("Cancel all building progress"),
		('running_costs_label'          , 'helptext'): _("Running costs"),
		('toggle_active_active'         , 'helptext'): _("Pause"),
		('toggle_active_inactive'       , 'helptext'): _("Resume"),
		},

	'barracks_confirm.xml' : {
		('BB_confirm_build_label'       , 'text'    ): _("Build groundunit:"),
		('BB_description_swordman'      , 'text'    ): _("Three-masted most common classified war ship with one gun deck."),
		('BB_needed_boards'             , 'text'    ): _("24t"),
		('BB_needed_boards+'            , 'text'    ): _(" + 24t"),
		('BB_needed_cannons'            , 'text'    ): _("06t"),
		('BB_needed_cannons+'           , 'text'    ): _(" + 06t"),
		('BB_needed_cloth'              , 'text'    ): _("14t"),
		('BB_needed_cloth+'             , 'text'    ): _(" + 14t"),
		('BB_needed_money'              , 'text'    ): _("2500"),
		('BB_needed_money+'             , 'text'    ): _(" + 1457"),
		('BB_needed_ropes'              , 'text'    ): _("06t"),
		('BB_needed_ropes+'             , 'text'    ): _(" + 06t"),
		('BB_upgrade_cannons'           , 'text'    ): _("Cannons"),
		('BB_upgrade_hull'              , 'text'    ): _("Hull"),
		('headline'                     , 'text'    ): _("Confirm order"),
		('headline_BB_builtgroundunit_label', 'text'    ): _("Sloop-o'-war"),
		('headline_upgrades'            , 'text'    ): _("Buy Upgrades"),
		('create_unit'                  , 'helptext'): _("Build this groundunit!"),
		},

	'barracks_showcase.xml' : {
		},

	'boatbuilder.xml' : {
		('UB_cancel_build_label'        , 'text'    ): _("Cancel building:"),
		('UB_cancel_warning_label'      , 'text'    ): _("(lose all resources)"),
		('UB_current_order'             , 'text'    ): _("Currently building:"),
		('UB_howto_build_lbl'           , 'text'    ): _("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
		('UB_needed_res_label'          , 'text'    ): _("Resources still needed:"),
		('UB_progress_label'            , 'text'    ): _("Construction progress:"),
		('UB_cancel_button'             , 'helptext'): _("Cancel all building progress"),
		('running_costs_label'          , 'helptext'): _("Running costs"),
		('toggle_active_active'         , 'helptext'): _("Pause"),
		('toggle_active_inactive'       , 'helptext'): _("Resume"),
		},

	'boatbuilder_confirm.xml' : {
		('BB_confirm_build_label'       , 'text'    ): _("Build ship:"),
		('BB_description_frigate'       , 'text'    ): _("Three-masted most common classified war ship with one gun deck."),
		('BB_needed_boards'             , 'text'    ): _("24t"),
		('BB_needed_boards+'            , 'text'    ): _(" + 24t"),
		('BB_needed_cannons'            , 'text'    ): _("06t"),
		('BB_needed_cannons+'           , 'text'    ): _(" + 06t"),
		('BB_needed_cloth'              , 'text'    ): _("14t"),
		('BB_needed_cloth+'             , 'text'    ): _(" + 14t"),
		('BB_needed_money'              , 'text'    ): _("2500"),
		('BB_needed_money+'             , 'text'    ): _(" + 1457"),
		('BB_needed_ropes'              , 'text'    ): _("06t"),
		('BB_needed_ropes+'             , 'text'    ): _(" + 06t"),
		('BB_upgrade_cannons'           , 'text'    ): _("Cannons"),
		('BB_upgrade_hull'              , 'text'    ): _("Hull"),
		('headline'                     , 'text'    ): _("Confirm order"),
		('headline_BB_builtship_label'  , 'text'    ): _("Sloop-o'-war"),
		('headline_upgrades'            , 'text'    ): _("Buy Upgrades"),
		('create_unit'                  , 'helptext'): _("Build this ship!"),
		},

	'boatbuilder_showcase.xml' : {
		},

	'diplomacy.xml' : {
		('ally_label'                   , 'text'    ): _("ally"),
		('enemy_label'                  , 'text'    ): _("enemy"),
		('neutral_label'                , 'text'    ): _("neutral"),
		},

	'overview_farm.xml' : {
		('headline'                     , 'text'    ): _("Building overview"),
		('capacity_utilization_label'   , 'helptext'): _("Capacity utilization"),
		('running_costs_label'          , 'helptext'): _("Running costs"),
		('capacity_utilization'         , 'helptext'): _("Capacity utilization"),
		('running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_war_groundunit.xml' : {
		},

	'island_inventory.xml' : {
		('headline'                     , 'text'    ): _("Settlement inventory"),
		},

	'mainsquare_inhabitants.xml' : {
		('headline'                     , 'text'    ): _("Settler overview"),
		('headline_happiness_per_house' , 'text'    ): _("Happiness per house"),
		('headline_residents_per_house' , 'text'    ): _("Residents per house"),
		('headline_residents_total'     , 'text'    ): _("Summary"),
		('houses'                       , 'text'    ): _("houses"),
		('residents'                    , 'text'    ): _("residents"),
		('tax_label'                    , 'text'    ): _("Taxes:"),
		('upgrades_lbl'                 , 'text'    ): _("Upgrade permissions:"),
		('avg_icon'                     , 'helptext'): _("satisfied"),
		('happiness_house_icon'         , 'helptext'): _("Amount of houses with this happiness"),
		('happy_icon'                   , 'helptext'): _("happy"),
		('houses_icon'                  , 'helptext'): _("Houses with this amount of inhabitants"),
		('inhabitants_icon'             , 'helptext'): _("Number of inhabitants per house"),
		('paid_taxes_icon'              , 'helptext'): _("Paid taxes"),
		('sad_icon'                     , 'helptext'): _("sad"),
		('tax_rate_icon'                , 'helptext'): _("Tax rate"),
		('tax_val_label'                , 'helptext'): _("Tax rate"),
		('taxes'                        , 'helptext'): _("Paid taxes"),
		},

	'overview_enemybuilding.xml' : {
		},

	'overview_enemyunit.xml' : {
		},

	'overview_enemywarehouse.xml' : {
		('buying_label'                 , 'text'    ): _("Buying"),
		('selling_label'                , 'text'    ): _("Selling"),
		},

	'overview_generic.xml' : {
		('headline'                     , 'text'    ): _("Building overview"),
		('name_label'                   , 'text'    ): _("Name:"),
		('running_costs_label'          , 'helptext'): _("Running costs"),
		('running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_groundunit.xml' : {
		('lbl_weapon_storage'           , 'text'    ): _("Weapons:"),
		},

	'overview_productionbuilding.xml' : {
		('capacity_utilization_label'   , 'helptext'): _("Capacity utilization"),
		('running_costs_label'          , 'helptext'): _("Running costs"),
		('capacity_utilization'         , 'helptext'): _("Capacity utilization"),
		('running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_resourcedeposit.xml' : {
		('headline'                     , 'text'    ): _("Resource deposit"),
		('res_dep_description_lbl'      , 'text'    ): _("This is a resource deposit where you can build a mine to dig up resources."),
		('res_dep_description_lbl2'     , 'text'    ): _("It contains these resources:"),
		},

	'overview_settler.xml' : {
		('needed_res_label'             , 'text'    ): _("Needed resources:"),
		('tax_label'                    , 'text'    ): _("Taxes:"),
		('happiness_label'              , 'helptext'): _("Happiness"),
		('paid_taxes_label'             , 'helptext'): _("Paid taxes"),
		('paid_taxes_label'             , 'helptext'): _("Tax rate"),
		('residents_label'              , 'helptext'): _("Residents"),
		('inhabitants'                  , 'helptext'): _("Residents"),
		('tax_val_label'                , 'helptext'): _("Tax rate"),
		('taxes'                        , 'helptext'): _("Paid taxes"),
		('happiness'                    , 'helptext'): _("Happiness"),
		},

	'overview_signalfire.xml' : {
		('signal_fire_description_lbl'  , 'text'    ): _("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods."),
		},

	'overview_tower.xml' : {
		('name_label'                   , 'text'    ): _("Name:"),
		('running_costs_label'          , 'helptext'): _("Running costs"),
		('running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_tradership.xml' : {
		('trader_description_lbl'       , 'text'    ): _("This is the free trader's ship. It will visit you from time to time to buy or sell goods."),
		},

	'overviewtab.xml' : {
		},

	'overview_select_multi.xml' : {
		},

	'unit_entry_widget.xml' : {
		},

	'overview_ship.xml' : {
		('configure_route'              , 'helptext'): _("Configure trading route"),
		('found_settlement'             , 'helptext'): _("Build settlement"),
		('trade'                        , 'helptext'): _("Trade"),
		},

	'overview_trade_ship.xml' : {
		('configure_route'              , 'helptext'): _("Configure trading route"),
		('discard_res'                  , 'helptext'): _("Discard all resources"),
		('found_settlement'             , 'helptext'): _("Build settlement"),
		('trade'                        , 'helptext'): _("Trade"),
		},

	'overview_war_ship.xml' : {
		('configure_route'              , 'helptext'): _("Configure trading route"),
		('found_settlement'             , 'helptext'): _("Build settlement"),
		('trade'                        , 'helptext'): _("Trade"),
		},

	'tradetab.xml' : {
		('buying_label'                 , 'text'    ): _("Buying"),
		('exchange_label'               , 'text'    ): _("Exchange:"),
		('headline'                     , 'text'    ): _("Trade"),
		('selling_label'                , 'text'    ): _("Selling"),
		('ship_label'                   , 'text'    ): _("Ship:"),
		('trade_with_label'             , 'text'    ): _("Trade partner:"),
		},

	'tab_base.xml' : {
		},

	'buysellmenu.xml' : {
		('headline'                     , 'text'    ): _("Buy or sell resources"),
		('headline_trade_history'       , 'text'    ): _("Trade history"),
		},

	'select_trade_resource.xml' : {
		('headline'                     , 'text'    ): _("Select resources:"),
		},

	'tab_account.xml' : {
		('buy_expenses_label'           , 'text'    ): _("Buying"),
		('headline_balance_label'       , 'text'    ): _("Balance:"),
		('headline_expenses_label'      , 'text'    ): _("Expenses:"),
		('headline_income_label'        , 'text'    ): _("Income:"),
		('running_costs_label'          , 'text'    ): _("Running costs"),
		('sell_income_label'            , 'text'    ): _("Sale"),
		('taxes_label'                  , 'text'    ): _("Taxes"),
		('collector_utilization_label'  , 'helptext'): _("Collector utilization"),
		('show_production_overview'     , 'helptext'): _("Show resources produced in this settlement"),
		('collector_utilization'        , 'helptext'): _("Collector utilization"),
		},

	'trade_single_slot.xml' : {
		},

	'overview_farmproductionline.xml' : {
		('toggle_active_active'         , 'helptext'): _("Pause production"),
		('toggle_active_inactive'       , 'helptext'): _("Start production"),
		},

	'overview_productionline.xml' : {
		('toggle_active_active'         , 'helptext'): _("Pause production"),
		('toggle_active_inactive'       , 'helptext'): _("Start production"),
		},

	'related_buildings_container.xml' : {
		},

	'resbar_resource_selection.xml' : {
		('headline'                     , 'text'    ): _("Select resource:"),
		('make_default_btn'             , 'helptext'): _("Save current resource configuration as default for all settlements."),
		('reset_default_btn'            , 'helptext'): _("Reset default resource configuration for all settlements."),
		('headline'                     , 'helptext'): _("The resource you select is displayed instead of the current one. Empty by clicking on X."),
		},

	'route_entry.xml' : {
		('delete_warehouse'             , 'helptext'): _("Delete entry"),
		('move_down'                    , 'helptext'): _("Move down"),
		('move_up'                      , 'helptext'): _("Move up"),
		},

	'trade_history_item.xml' : {
		},

	'traderoute_resource_selection.xml' : {
		('select_res_label'             , 'text'    ): _("Select a resource:"),
		},

	'captains_log.xml' : {
		('stats_players'                , 'text'    ): _("Players"),
		('stats_settlements'            , 'text'    ): _("My settlements"),
		('stats_ships'                  , 'text'    ): _("My ships"),
		('weird_button_1'               , 'text'    ): _("Whole world"),
		('weird_button_4'               , 'text'    ): _("Everybody"),
		('headline_chat'                , 'text'    ): _("Chat"),
		('headline_game_messages'       , 'text'    ): _("Game messages"),
		('headline_statistics'          , 'text'    ): _("Statistics"),
		('okButton'                     , 'helptext'): _("Return to game"),
		('weird_button_4'               , 'helptext'): _("Sends the chat messages to all players."),
		('backwardButton'               , 'helptext'): _("Read previous entries"),
		('forwardButton'                , 'helptext'): _("Read next entries"),
		},

	'configure_route.xml' : {
		('lbl_route_activity'           , 'text'    ): _("Route activity:"),
		('lbl_wait_at_load'             , 'text'    ): _("Wait at load:"),
		('lbl_wait_at_unload'           , 'text'    ): _("Wait at unload:"),
		('okButton'                     , 'helptext'): _("Exit"),
		('start_route'                  , 'helptext'): _("Start route"),
		},

	'healthwidget.xml' : {
		},

	'island_production.xml' : {
		('okButton'                     , 'helptext'): _("Close"),
		},

	'players_overview.xml' : {
		('building_score'               , 'text'    ): _("Buildings"),
		('headline'                     , 'text'    ): _("Player scores"),
		('land_score'                   , 'text'    ): _("Land"),
		('money_score'                  , 'text'    ): _("Money"),
		('player_name'                  , 'text'    ): _("Name"),
		('resource_score'               , 'text'    ): _("Resources"),
		('settler_score'                , 'text'    ): _("Settlers"),
		('total_score'                  , 'text'    ): _("Total"),
		('unit_score'                   , 'text'    ): _("Units"),
		('building_score'               , 'helptext'): _("Value of all the buildings in the player's settlement(s)"),
		('land_score'                   , 'helptext'): _("Value of usable land i.e Amount of Land that can be used to create buildings "),
		('money_score'                  , 'helptext'): _("Player's current treasury + income expected in near future"),
		('player_name'                  , 'helptext'): _("Player Name"),
		('resource_score'               , 'helptext'): _("Value of resources generated from all the possible sources in the player's settlement(s)"),
		('settler_score'                , 'helptext'): _("Value denoting the progress of the settlement(s) in terms of inhabitants, buildings and overall happiness"),
		('total_score'                  , 'helptext'): _("The total value from all individual entities or in short : Total Player Score"),
		('unit_score'                   , 'helptext'): _("Value of all the units owned by the player"),
		},

	'players_settlements.xml' : {
		('balance'                      , 'text'    ): _("Balance"),
		('inhabitants'                  , 'text'    ): _("Inhabitants"),
		('running_costs'                , 'text'    ): _("Running costs"),
		('settlement_name'              , 'text'    ): _("Name"),
		('taxes'                        , 'text'    ): _("Taxes"),
		},

	'ships_list.xml' : {
		('health'                       , 'text'    ): _("Health"),
		('ship_name'                    , 'text'    ): _("Name"),
		('ship_type'                    , 'text'    ): _("Type"),
		('status'                       , 'text'    ): _("Status"),
		('weapons'                      , 'text'    ): _("Weapons"),
		},

	'stancewidget.xml' : {
		('aggressive_stance'            , 'helptext'): _("Aggressive"),
		('flee_stance'                  , 'helptext'): _("Flee"),
		('hold_ground_stance'           , 'helptext'): _("Hold ground"),
		('none_stance'                  , 'helptext'): _("Passive"),
		},

	'credits.xml' : {
		},

	'editor_create_map.xml' : {
		('headline_choose_map_size_lbl' , 'text'    ): _("Choose a map size:"),
		},

	'editor_select_map.xml' : {
		('headline_choose_map_lbl'      , 'text'    ): _("Choose a map:"),
		},

	'editor_select_saved_game.xml' : {
		('headline_choose_saved_game'   , 'text'    ): _("Choose a saved game's map:"),
		},

	'editor_start_menu.xml' : {
		('headline'                     , 'text'    ): _("Select map source"),
		('create_new_map'               , 'text'    ): _("Create new map"),
		('load_existing_map'            , 'text'    ): _("Load existing map"),
		('load_saved_game_map'          , 'text'    ): _("Load saved game's map"),
		('cancel'                       , 'helptext'): _("Exit to main menu"),
		('okay'                         , 'helptext'): _("Start editor"),
		},

	'help.xml' : {
		('okButton'                     , 'helptext'): _("Return"),
		},

	'hotkeys.xml' : {
		('reset_to_default'             , 'text'    ): _("Reset to default keys"),
		('labels_headline'              , 'text'    ): _("Actions"),
		('primary_buttons_headline'     , 'text'    ): _("Primary"),
		('secondary_buttons_headline'   , 'text'    ): _("Secondary"),
		('okButton'                     , 'helptext'): _("Exit to main menu"),
		('reset_to_default'             , 'helptext'): _("Reset to default"),
		('lbl_BUILD_TOOL'               , 'helptext'): _("Show build menu"),
		('lbl_CHAT'                     , 'helptext'): _("Chat"),
		('lbl_CONSOLE'                  , 'helptext'): _("Toggle showing FPS on/off"),
		('lbl_COORD_TOOLTIP'            , 'helptext'): _("Show coordinate values (Debug)"),
		('lbl_DESTROY_TOOL'             , 'helptext'): _("Enable destruct mode"),
		('lbl_DOWN'                     , 'helptext'): _("Scroll down"),
		('lbl_GRID'                     , 'helptext'): _("Toggle grid on/off"),
		('lbl_HEALTH_BAR'               , 'helptext'): _("Toggle health bars"),
		('lbl_HELP'                     , 'helptext'): _("Display help"),
		('lbl_LEFT'                     , 'helptext'): _("Scroll left"),
		('lbl_LOGBOOK'                  , 'helptext'): _("Toggle Captain's log"),
		('lbl_PAUSE'                    , 'helptext'): _("Pause game"),
		('lbl_PIPETTE'                  , 'helptext'): _("Enable pipette mode (clone buildings)"),
		('lbl_PLAYERS_OVERVIEW'         , 'helptext'): _("Show player scores"),
		('lbl_QUICKLOAD'                , 'helptext'): _("Quickload"),
		('lbl_QUICKSAVE'                , 'helptext'): _("Quicksave"),
		('lbl_REMOVE_SELECTED'          , 'helptext'): _("Remove selected units / buildings"),
		('lbl_RIGHT'                    , 'helptext'): _("Scroll right"),
		('lbl_ROAD_TOOL'                , 'helptext'): _("Enable road building mode"),
		('lbl_ROTATE_LEFT'              , 'helptext'): _("Rotate building or map counterclockwise"),
		('lbl_ROTATE_RIGHT'             , 'helptext'): _("Rotate building or map clockwise"),
		('lbl_SCREENSHOT'               , 'helptext'): _("Screenshot"),
		('lbl_SETTLEMENTS_OVERVIEW'     , 'helptext'): _("Show settlement list"),
		('lbl_SHIPS_OVERVIEW'           , 'helptext'): _("Show ship list"),
		('lbl_SHOW_SELECTED'            , 'helptext'): _("Focus camera on selection"),
		('lbl_SPEED_DOWN'               , 'helptext'): _("Decrease game speed"),
		('lbl_SPEED_UP'                 , 'helptext'): _("Increase game speed"),
		('lbl_TILE_OWNER_HIGHLIGHT'     , 'helptext'): _("Highlight tile ownership"),
		('lbl_TRANSLUCENCY'             , 'helptext'): _("Toggle translucency of ambient buildings"),
		('lbl_UP'                       , 'helptext'): _("Scroll up"),
		('lbl_ZOOM_IN'                  , 'helptext'): _("Zoom in"),
		('lbl_ZOOM_OUT'                 , 'helptext'): _("Zoom out"),
		},

	'ingamemenu.xml' : {
		('help'                         , 'text'    ): _("Help"),
		('loadgame'                     , 'text'    ): _("Load game"),
		('quit'                         , 'text'    ): _("Cancel game"),
		('savegame'                     , 'text'    ): _("Save game"),
		('settings'                     , 'text'    ): _("Settings"),
		('start'                        , 'text'    ): _("Return to game"),
		},

	'loadingscreen.xml' : {
		('loading_label'                , 'text'    ): _("Loading…"),
		},

	'mainmenu.xml' : {
		('credits_label'                , 'text'    ): _("Credits"),
		('editor_label'                 , 'text'    ): _("Editor"),
		('help_label'                   , 'text'    ): _("Help"),
		('load_label'                   , 'text'    ): _("Load game"),
		('multi_label'                  , 'text'    ): _("Multiplayer"),
		('quit_label'                   , 'text'    ): _("Quit"),
		('settings_label'               , 'text'    ): _("Settings"),
		('single_label'                 , 'text'    ): _("Singleplayer"),
		('version_label'                , 'text'    ): VERSION.string(),
		},

	'multiplayer_creategame.xml' : {
		('gamename_lbl'                 , 'text'    ): _("Name of the game:"),
		('headline'                     , 'text'    ): _("Choose a map:"),
		('headline'                     , 'text'    ): _("Create game - Multiplayer"),
		('mp_player_limit_lbl'          , 'text'    ): _("Player limit:"),
		('password_lbl'                 , 'text'    ): _("Password of the game:"),
		('cancel'                       , 'helptext'): _("Exit to multiplayer menu"),
		('create'                       , 'helptext'): _("Create this new game"),
		('gamename_lbl'                 , 'helptext'): _("This will be displayed to other players so they recognize the game."),
		('password_lbl'                 , 'helptext'): _("This game's password. Required to join this game."),
		},

	'multiplayer_gamelobby.xml' : {
		('game_player_color'            , 'text'    ): _("Color"),
		('game_player_status'           , 'text'    ): _("Status"),
		('game_start_notice'            , 'text'    ): _("The game will start as soon as all players are ready."),
		('headline'                     , 'text'    ): _("Chat:"),
		('headline'                     , 'text'    ): _("Gamelobby"),
		('ready_lbl'                    , 'text'    ): _("Ready:"),
		('startmessage'                 , 'text'    ): _("Game details:"),
		('cancel'                       , 'helptext'): _("Exit gamelobby"),
		('ready_btn'                    , 'helptext'): _("Sets your state to ready (necessary for the game to start)"),
		},

	'multiplayermenu.xml' : {
		('create_game_lbl'              , 'text'    ): _("Create game:"),
		('headline_active_games_lbl'    , 'text'    ): _("Active games:"),
		('headline_left'                , 'text'    ): _("New game - Multiplayer"),
		('join_game_lbl'                , 'text'    ): _("Join game:"),
		('load_game_lbl'                , 'text'    ): _("Load game:"),
		('refr_gamelist_lbl'            , 'text'    ): _("Refresh list:"),
		('cancel'                       , 'helptext'): _("Exit to main menu"),
		('create'                       , 'helptext'): _("Create a new game"),
		('join'                         , 'helptext'): _("Join the selected game"),
		('load'                         , 'helptext'): _("Load a saved game"),
		('refresh'                      , 'helptext'): _("Refresh list of active games"),
		},

	'set_player_details.xml' : {
		('headline_set_player_details'  , 'text'    ): _("Change player details"),
		},

	'settings.xml' : {
		('auto_unload_label'            , 'text'    ): _("Auto-unload ship:"),
		('autosave_interval_label'      , 'text'    ): _("Autosave interval in minutes:"),
		('cursor_centered_zoom_label'   , 'text'    ): _("Cursor centered zoom:"),
		('debug_log_lbl'                , 'text'    ): _("Enable logging:"),
		('edge_scrolling_label'         , 'text'    ): _("Scroll at map edge:"),
		('effect_volume_label'          , 'text'    ): _("Effects volume:"),
		('fps_label'                    , 'text'    ): _("Frame rate limit:"),
		('headline_graphics'            , 'text'    ): _("Graphics"),
		('headline_language'            , 'text'    ): _("Language"),
		('headline_misc'                , 'text'    ): _("General"),
		('headline_mouse'               , 'text'    ): _("Mouse"),
		('headline_network'             , 'text'    ): _("Network"),
		('headline_saving'              , 'text'    ): _("Saving"),
		('headline_sound'               , 'text'    ): _("Sound"),
		('middle_mouse_pan_lbl'         , 'text'    ): _("Middle mouse button pan:"),
		('minimap_rotation_label'       , 'text'    ): _("Rotate minimap with map:"),
		('mouse_sensitivity_label'      , 'text'    ): _("Mouse sensitivity:"),
		('music_volume_label'           , 'text'    ): _("Music volume:"),
		('network_port_lbl'             , 'text'    ): _("Network port:"),
		('number_of_autosaves_label'    , 'text'    ): _("Number of autosaves:"),
		('number_of_quicksaves_label'   , 'text'    ): _("Number of quicksaves:"),
		('quote_type_label'             , 'text'    ): _("Choose a quote type:"),
		('screen_fullscreen_text'       , 'text'    ): _("Full screen:"),
		('screen_resolution_label'      , 'text'    ): _("Screen resolution:"),
		('scroll_speed_label'           , 'text'    ): _("Scroll delay:"),
		('show_resource_icons_lbl'      , 'text'    ): _("Production indicators:"),
		('sound_enable_opt_text'        , 'text'    ): _("Enable sound:"),
		('uninterrupted_building_label' , 'text'    ): _("Uninterrupted building:"),
		('cancelButton'                 , 'helptext'): _("Discard current changes"),
		('defaultButton'                , 'helptext'): _("Reset to default settings"),
		('okButton'                     , 'helptext'): _("Save changes"),
		('auto_unload_label'            , 'helptext'): _("Whether to unload the ship after founding a settlement"),
		('cursor_centered_zoom_label'   , 'helptext'): _("When enabled, mouse wheel zoom will use the cursor position as new viewport center. When disabled, always zoom to current viewport center."),
		('debug_log_lbl'                , 'helptext'): _("Don't use in normal game session. Decides whether to write debug information in the logging directory of your user directory. Slows the game down."),
		('edge_scrolling_label'         , 'helptext'): _("Whether to move the viewport when the mouse pointer is close to map edges"),
		('fps_label'                    , 'helptext'): _("Set the maximum frame rate used. Default: 60 fps."),
		('middle_mouse_pan_lbl'         , 'helptext'): _("When enabled, dragging the middle mouse button will pan the camera"),
		('minimap_rotation_label'       , 'helptext'): _("Whether to also rotate the minimap whenever the regular map is rotated"),
		('mouse_sensitivity_label'      , 'helptext'): _("0 is default system settings"),
		('network_port_lbl'             , 'helptext'): _("If set to 0, use the router default"),
		('quote_type_label'             , 'helptext'): _("What kind of quote to display while loading a game"),
		('scroll_speed_label'           , 'helptext'): _("Higher values slow down scrolling."),
		('show_resource_icons_lbl'      , 'helptext'): _("Whether to show resource icons over buildings whenever they finish production"),
		('uninterrupted_building_label' , 'helptext'): _("When enabled, do not exit the build mode after successful construction"),
		},

	'select_savegame.xml' : {
		('enter_filename_label'         , 'text'    ): _("Enter filename:"),
		('gamename_lbl'                 , 'text'    ): _("Name of the game:"),
		('gamepassword_lbl'             , 'text'    ): _("Password of the game:"),
		('headline_details_label'       , 'text'    ): _("Details:"),
		('headline_saved_games_label'   , 'text'    ): _("Your saved games:"),
		('cancelButton'                 , 'helptext'): _("Cancel"),
		('deleteButton'                 , 'helptext'): _("Delete selected savegame"),
		('gamename_lbl'                 , 'helptext'): _("This will be displayed to other players so they recognize the game."),
		('gamepassword_lbl'             , 'helptext'): _("Password of the game. Required to join this game"),
		},

	'singleplayermenu.xml' : {
		('headline'                     , 'text'    ): _("New game - Singleplayer"),
		('free_maps'                    , 'text'    ): _("Free play"),
		('random'                       , 'text'    ): _("Random map"),
		('scenario'                     , 'text'    ): _("Scenario"),
		('cancel'                       , 'helptext'): _("Exit to main menu"),
		('okay'                         , 'helptext'): _("Start game"),
		},

	'sp_free_maps.xml' : {
		('headline_choose_map_lbl'      , 'text'    ): _("Choose a map to play:"),
		},

	'sp_random.xml' : {
		('headline_map_settings_lbl'    , 'text'    ): _("Map settings:"),
		('seed_string_lbl'              , 'text'    ): _("Seed:"),
		},

	'sp_scenario.xml' : {
		('choose_map_lbl'               , 'text'    ): _("Choose a map to play:"),
		('select_lang_lbl'              , 'text'    ): _("Select a language:"),
		},

	'aidataselection.xml' : {
		('ai_players_label'             , 'text'    ): _("AI players:"),
		},

	'game_settings.xml' : {
		('headline_game_settings_lbl'   , 'text'    ): _("Game settings:"),
		('lbl_disasters'                , 'text'    ): _("Disasters"),
		('lbl_free_trader'              , 'text'    ): _("Free Trader"),
		('lbl_pirates'                  , 'text'    ): _("Pirates"),
		},

	'playerdataselection.xml' : {
		('color_label'                  , 'text'    ): _("Color:"),
		('player_label'                 , 'text'    ): _("Player name:"),
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
