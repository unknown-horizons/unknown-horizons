# Encoding: utf-8
# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from typing import Dict, Tuple

from horizons.constants import VERSION
from horizons.i18n import gettext as T

text_translations = {} # type: Dict[str, Dict[Tuple[str, str], str]]


def set_translations():
	global text_translations
	text_translations = {

	'stringpreviewwidget.xml' : {
		},

	'editor_pause_menu.xml' : {
		('help'                         , 'text'    ): T("Help"),
		('loadgame'                     , 'text'    ): T("Load map"),
		('quit'                         , 'text'    ): T("Exit editor"),
		('savegame'                     , 'text'    ): T("Save map"),
		('settings'                     , 'text'    ): T("Settings"),
		('start'                        , 'text'    ): T("Return to editor"),
		},

	'editor_settings.xml' : {
		('cursor_hint'                  , 'text'    ): T("(right click to stop)"),
		('headline_brush_size'          , 'text'    ): T("Select brush size:"),
		('headline_terrain'             , 'text'    ): T("Select terrain:"),
		},

	'buildtab.xml' : {
		},

	'buildtab_no_settlement.xml' : {
		('headline'                     , 'text'    ): T("Game start"),
		('howto_1_need_warehouse'       , 'text'    ): T("You need to found a settlement before you can construct buildings!"),
		('howto_2_navigate_ship'        , 'text'    ): T("Select your ship and approach the coast via right-click."),
		('howto_3_build_warehouse'      , 'text'    ): T("Afterwards, press the large button in the ship overview tab."),
		},

	'place_building.xml' : {
		('headline'                     , 'text'    ): T("Build"),
		('running_costs_label'          , 'text'    ): T("Running costs:"),
		},

	'related_buildings.xml' : {
		('headline'                     , 'text'    ): T("Related buildings"),
		},

	'city_info.xml' : {
		('city_info_inhabitants'        , 'helptext'): T("Inhabitants"),
		},

	'messagewidget_icon.xml' : {
		},

	'messagewidget_message.xml' : {
		},

	'minimap.xml' : {
		('build'                        , 'helptext'): T("Build menu ({key})"),
		('destroy_tool'                 , 'helptext'): T("Destroy ({key})"),
		('diplomacyButton'              , 'helptext'): T("Diplomacy"),
		('gameMenuButton'               , 'helptext'): T("Game menu ({key})"),
		('logbook'                      , 'helptext'): T("Captain's log ({key})"),
		('rotateLeft'                   , 'helptext'): T("Rotate map counterclockwise ({key})"),
		('rotateRight'                  , 'helptext'): T("Rotate map clockwise ({key})"),
		('speedDown'                    , 'helptext'): T("Decrease game speed ({key})"),
		('speedUp'                      , 'helptext'): T("Increase game speed ({key})"),
		('zoomIn'                       , 'helptext'): T("Zoom in"),
		('zoomOut'                      , 'helptext'): T("Zoom out"),
		},

	'resource_overview_bar_entry.xml' : {
		},

	'resource_overview_bar_gold.xml' : {
		},

	'resource_overview_bar_stats.xml' : {
		},

	'change_name.xml' : {
		('enter_new_name_lbl'           , 'text'    ): T("Enter new name:"),
		('headline_change_name'         , 'text'    ): T("Change name"),
		('old_name_label'               , 'text'    ): T("Old name:"),
		('okButton'                     , 'helptext'): T("Apply the new name"),
		},

	'chat.xml' : {
		('chat_lbl'                     , 'text'    ): T("Enter your message:"),
		('headline'                     , 'text'    ): T("Chat"),
		},

	'barracks.xml' : {
		('UB_cancel_build_label'        , 'text'    ): T("Cancel building:"),
		('UB_cancel_warning_label'      , 'text'    ): T("(lose all resources)"),
		('UB_current_order'             , 'text'    ): T("Currently building:"),
		('UB_howto_build_lbl'           , 'text'    ): T("To build a groundunit, click on one of the class tabs, select the desired groundunit and confirm the order."),
		('UB_needed_res_label'          , 'text'    ): T("Resources still needed:"),
		('UB_progress_label'            , 'text'    ): T("Construction progress:"),
		('UB_cancel_button'             , 'helptext'): T("Cancel all building progress"),
		('running_costs_label'          , 'helptext'): T("Running costs"),
		('toggle_active_active'         , 'helptext'): T("Pause"),
		('toggle_active_inactive'       , 'helptext'): T("Resume"),
		},

	'barracks_confirm.xml' : {
		('BB_confirm_build_label'       , 'text'    ): T("Build groundunit:"),
		('BB_description_swordman'      , 'text'    ): T("Three-masted most common classified war ship with one gun deck."),
		('BB_needed_boards'             , 'text'    ): T("24t"),
		('BB_needed_boards+'            , 'text'    ): T(" + 24t"),
		('BB_needed_cannons'            , 'text'    ): T("06t"),
		('BB_needed_cannons+'           , 'text'    ): T(" + 06t"),
		('BB_needed_cloth'              , 'text'    ): T("14t"),
		('BB_needed_cloth+'             , 'text'    ): T(" + 14t"),
		('BB_needed_money'              , 'text'    ): T("2500"),
		('BB_needed_money+'             , 'text'    ): T(" + 1457"),
		('BB_needed_ropes'              , 'text'    ): T("06t"),
		('BB_needed_ropes+'             , 'text'    ): T(" + 06t"),
		('BB_upgrade_cannons'           , 'text'    ): T("Cannons"),
		('BB_upgrade_hull'              , 'text'    ): T("Hull"),
		('headline'                     , 'text'    ): T("Confirm order"),
		('headline_BB_builtgroundunit_label', 'text'    ): T("Sloop-o'-war"),
		('headline_upgrades'            , 'text'    ): T("Buy Upgrades"),
		('create_unit'                  , 'helptext'): T("Build this groundunit!"),
		},

	'barracks_showcase.xml' : {
		},

	'boatbuilder.xml' : {
		('UB_cancel_build_label'        , 'text'    ): T("Cancel building:"),
		('UB_cancel_warning_label'      , 'text'    ): T("(lose all resources)"),
		('UB_current_order'             , 'text'    ): T("Currently building:"),
		('UB_howto_build_lbl'           , 'text'    ): T("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
		('UB_needed_res_label'          , 'text'    ): T("Resources still needed:"),
		('UB_progress_label'            , 'text'    ): T("Construction progress:"),
		('UB_cancel_button'             , 'helptext'): T("Cancel all building progress"),
		('running_costs_label'          , 'helptext'): T("Running costs"),
		('toggle_active_active'         , 'helptext'): T("Pause"),
		('toggle_active_inactive'       , 'helptext'): T("Resume"),
		},

	'boatbuilder_confirm.xml' : {
		('BB_confirm_build_label'       , 'text'    ): T("Build ship:"),
		('BB_description_frigate'       , 'text'    ): T("Three-masted most common classified war ship with one gun deck."),
		('BB_needed_boards'             , 'text'    ): T("24t"),
		('BB_needed_boards+'            , 'text'    ): T(" + 24t"),
		('BB_needed_cannons'            , 'text'    ): T("06t"),
		('BB_needed_cannons+'           , 'text'    ): T(" + 06t"),
		('BB_needed_cloth'              , 'text'    ): T("14t"),
		('BB_needed_cloth+'             , 'text'    ): T(" + 14t"),
		('BB_needed_money'              , 'text'    ): T("2500"),
		('BB_needed_money+'             , 'text'    ): T(" + 1457"),
		('BB_needed_ropes'              , 'text'    ): T("06t"),
		('BB_needed_ropes+'             , 'text'    ): T(" + 06t"),
		('BB_upgrade_cannons'           , 'text'    ): T("Cannons"),
		('BB_upgrade_hull'              , 'text'    ): T("Hull"),
		('headline'                     , 'text'    ): T("Confirm order"),
		('headline_BB_builtship_label'  , 'text'    ): T("Sloop-o'-war"),
		('headline_upgrades'            , 'text'    ): T("Buy Upgrades"),
		('create_unit'                  , 'helptext'): T("Build this ship!"),
		},

	'boatbuilder_showcase.xml' : {
		},

	'diplomacy.xml' : {
		('ally_label'                   , 'text'    ): T("ally"),
		('enemy_label'                  , 'text'    ): T("enemy"),
		('neutral_label'                , 'text'    ): T("neutral"),
		},

	'overview_farm.xml' : {
		('headline'                     , 'text'    ): T("Building overview"),
		('capacity_utilization_label'   , 'helptext'): T("Capacity utilization"),
		('running_costs_label'          , 'helptext'): T("Running costs"),
		('capacity_utilization'         , 'helptext'): T("Capacity utilization"),
		('running_costs'                , 'helptext'): T("Running costs"),
		},

	'overview_war_groundunit.xml' : {
		},

	'island_inventory.xml' : {
		('headline'                     , 'text'    ): T("Settlement inventory"),
		},

	'mainsquare_inhabitants.xml' : {
		('headline'                     , 'text'    ): T("Settler overview"),
		('headline_happiness_per_house' , 'text'    ): T("Happiness per house"),
		('headline_residents_per_house' , 'text'    ): T("Residents per house"),
		('headline_residents_total'     , 'text'    ): T("Summary"),
		('houses'                       , 'text'    ): T("houses"),
		('residents'                    , 'text'    ): T("residents"),
		('tax_label'                    , 'text'    ): T("Taxes:"),
		('upgrades_lbl'                 , 'text'    ): T("Upgrade permissions:"),
		('avg_icon'                     , 'helptext'): T("satisfied"),
		('happiness_house_icon'         , 'helptext'): T("Amount of houses with this happiness"),
		('happy_icon'                   , 'helptext'): T("happy"),
		('houses_icon'                  , 'helptext'): T("Houses with this amount of inhabitants"),
		('inhabitants_icon'             , 'helptext'): T("Number of inhabitants per house"),
		('paid_taxes_icon'              , 'helptext'): T("Paid taxes"),
		('sad_icon'                     , 'helptext'): T("sad"),
		('tax_rate_icon'                , 'helptext'): T("Tax rate"),
		('tax_val_label'                , 'helptext'): T("Tax rate"),
		('taxes'                        , 'helptext'): T("Paid taxes"),
		},

	'overview_barrier.xml' : {
		('barrier_description_lbl'      , 'text'    ): T("Provides security for your settlement."),
		},

	'overview_enemybuilding.xml' : {
		},

	'overview_enemyunit.xml' : {
		},

	'overview_enemywarehouse.xml' : {
		('buying_label'                 , 'text'    ): T("Buying"),
		('selling_label'                , 'text'    ): T("Selling"),
		},

	'overview_generic.xml' : {
		('headline'                     , 'text'    ): T("Building overview"),
		('name_label'                   , 'text'    ): T("Name:"),
		('running_costs_label'          , 'helptext'): T("Running costs"),
		('running_costs'                , 'helptext'): T("Running costs"),
		},

	'overview_groundunit.xml' : {
		('lbl_weapon_storage'           , 'text'    ): T("Weapons:"),
		},

	'overview_productionbuilding.xml' : {
		('capacity_utilization_label'   , 'helptext'): T("Capacity utilization"),
		('running_costs_label'          , 'helptext'): T("Running costs"),
		('capacity_utilization'         , 'helptext'): T("Capacity utilization"),
		('running_costs'                , 'helptext'): T("Running costs"),
		},

	'overview_resourcedeposit.xml' : {
		('headline'                     , 'text'    ): T("Resource deposit"),
		('res_dep_description_lbl'      , 'text'    ): T("This is a resource deposit where you can build a mine to dig up resources."),
		('res_dep_description_lbl2'     , 'text'    ): T("It contains these resources:"),
		},

	'overview_settler.xml' : {
		('needed_res_label'             , 'text'    ): T("Needed resources:"),
		('tax_label'                    , 'text'    ): T("Taxes:"),
		('happiness_label'              , 'helptext'): T("Happiness"),
		('paid_taxes_label'             , 'helptext'): T("Paid taxes"),
		('paid_taxes_label'             , 'helptext'): T("Tax rate"),
		('residents_label'              , 'helptext'): T("Residents"),
		('inhabitants'                  , 'helptext'): T("Residents"),
		('tax_val_label'                , 'helptext'): T("Tax rate"),
		('taxes'                        , 'helptext'): T("Paid taxes"),
		('happiness'                    , 'helptext'): T("Happiness"),
		},

	'overview_signalfire.xml' : {
		('signal_fire_description_lbl'  , 'text'    ): T("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods."),
		},

	'overview_tower.xml' : {
		('name_label'                   , 'text'    ): T("Name:"),
		('running_costs_label'          , 'helptext'): T("Running costs"),
		('running_costs'                , 'helptext'): T("Running costs"),
		},

	'overview_tradership.xml' : {
		('trader_description_lbl'       , 'text'    ): T("This is the free trader's ship. It will visit you from time to time to buy or sell goods."),
		},

	'overviewtab.xml' : {
		},

	'overview_select_multi.xml' : {
		},

	'unit_entry_widget.xml' : {
		},

	'overview_ship.xml' : {
		('configure_route'              , 'helptext'): T("Configure trading route"),
		('found_settlement'             , 'helptext'): T("Build settlement"),
		('trade'                        , 'helptext'): T("Trade"),
		},

	'overview_trade_ship.xml' : {
		('configure_route'              , 'helptext'): T("Configure trading route"),
		('discard_res'                  , 'helptext'): T("Discard all resources"),
		('found_settlement'             , 'helptext'): T("Build settlement"),
		('trade'                        , 'helptext'): T("Trade"),
		},

	'overview_war_ship.xml' : {
		('configure_route'              , 'helptext'): T("Configure trading route"),
		('found_settlement'             , 'helptext'): T("Build settlement"),
		('trade'                        , 'helptext'): T("Trade"),
		},

	'tradetab.xml' : {
		('buying_label'                 , 'text'    ): T("Buying"),
		('exchange_label'               , 'text'    ): T("Exchange:"),
		('headline'                     , 'text'    ): T("Trade"),
		('selling_label'                , 'text'    ): T("Selling"),
		('ship_label'                   , 'text'    ): T("Ship:"),
		('trade_with_label'             , 'text'    ): T("Trade partner:"),
		},

	'tab_base.xml' : {
		},

	'buysellmenu.xml' : {
		('headline'                     , 'text'    ): T("Buy or sell resources"),
		('headline_trade_history'       , 'text'    ): T("Trade history"),
		},

	'select_trade_resource.xml' : {
		('headline'                     , 'text'    ): T("Select resources:"),
		},

	'tab_account.xml' : {
		('buy_expenses_label'           , 'text'    ): T("Buying"),
		('headline_balance_label'       , 'text'    ): T("Balance:"),
		('headline_expenses_label'      , 'text'    ): T("Expenses:"),
		('headline_income_label'        , 'text'    ): T("Income:"),
		('running_costs_label'          , 'text'    ): T("Running costs"),
		('sell_income_label'            , 'text'    ): T("Sale"),
		('taxes_label'                  , 'text'    ): T("Taxes"),
		('collector_utilization_label'  , 'helptext'): T("Collector utilization"),
		('show_production_overview'     , 'helptext'): T("Show resources produced in this settlement"),
		('collector_utilization'        , 'helptext'): T("Collector utilization"),
		},

	'trade_single_slot.xml' : {
		},

	'overview_farmproductionline.xml' : {
		('toggle_active_active'         , 'helptext'): T("Pause production"),
		('toggle_active_inactive'       , 'helptext'): T("Start production"),
		},

	'overview_productionline.xml' : {
		('toggle_active_active'         , 'helptext'): T("Pause production"),
		('toggle_active_inactive'       , 'helptext'): T("Start production"),
		},

	'related_buildings_container.xml' : {
		},

	'resbar_resource_selection.xml' : {
		('headline'                     , 'text'    ): T("Select resource:"),
		('make_default_btn'             , 'helptext'): T("Save current resource configuration as default for all settlements."),
		('reset_default_btn'            , 'helptext'): T("Reset default resource configuration for all settlements."),
		('headline'                     , 'helptext'): T("The resource you select is displayed instead of the current one. Empty by clicking on X."),
		},

	'route_entry.xml' : {
		('delete_warehouse'             , 'helptext'): T("Delete entry"),
		('move_down'                    , 'helptext'): T("Move down"),
		('move_up'                      , 'helptext'): T("Move up"),
		},

	'scrollbar_resource_selection.xml' : {
		},

	'trade_history_item.xml' : {
		},

	'captains_log.xml' : {
		('stats_players'                , 'text'    ): T("Players"),
		('stats_settlements'            , 'text'    ): T("My settlements"),
		('stats_ships'                  , 'text'    ): T("My ships"),
		('weird_button_1'               , 'text'    ): T("Whole world"),
		('weird_button_4'               , 'text'    ): T("Everybody"),
		('headline_chat'                , 'text'    ): T("Chat"),
		('headline_game_messages'       , 'text'    ): T("Game messages"),
		('headline_statistics'          , 'text'    ): T("Statistics"),
		('okButton'                     , 'helptext'): T("Return to game"),
		('weird_button_4'               , 'helptext'): T("Sends the chat messages to all players."),
		('backwardButton'               , 'helptext'): T("Read previous entries"),
		('forwardButton'                , 'helptext'): T("Read next entries"),
		},

	'configure_route.xml' : {
		('lbl_route_activity'           , 'text'    ): T("Route activity:"),
		('lbl_wait_at_load'             , 'text'    ): T("Wait at load:"),
		('lbl_wait_at_unload'           , 'text'    ): T("Wait at unload:"),
		('player_name_label'            , 'text'    ): T("Player Name:"),
		('select_res_label'             , 'text'    ): T("Select a resource:"),
		('warehouse_name_label'         , 'text'    ): T("Island Name:"),
		('okButton'                     , 'helptext'): T("Exit"),
		('start_route'                  , 'helptext'): T("Start route"),
		},

	'healthwidget.xml' : {
		},

	'island_production.xml' : {
		('okButton'                     , 'helptext'): T("Close"),
		('backwardButton'               , 'helptext'): T("Go to previous page"),
		('forwardButton'                , 'helptext'): T("Go to next page"),
		},

	'players_overview.xml' : {
		('building_score'               , 'text'    ): T("Buildings"),
		('headline'                     , 'text'    ): T("Player scores"),
		('land_score'                   , 'text'    ): T("Land"),
		('money_score'                  , 'text'    ): T("Money"),
		('player_name'                  , 'text'    ): T("Name"),
		('resource_score'               , 'text'    ): T("Resources"),
		('settler_score'                , 'text'    ): T("Settlers"),
		('total_score'                  , 'text'    ): T("Total"),
		('unit_score'                   , 'text'    ): T("Units"),
		('building_score'               , 'helptext'): T("Value of all the buildings in the player's settlement(s)"),
		('land_score'                   , 'helptext'): T("Value of usable land i.e Amount of Land that can be used to create buildings "),
		('money_score'                  , 'helptext'): T("Player's current treasury + income expected in near future"),
		('player_name'                  , 'helptext'): T("Player Name"),
		('resource_score'               , 'helptext'): T("Value of resources generated from all the possible sources in the player's settlement(s)"),
		('settler_score'                , 'helptext'): T("Value denoting the progress of the settlement(s) in terms of inhabitants, buildings and overall happiness"),
		('total_score'                  , 'helptext'): T("The total value from all individual entities or in short : Total Player Score"),
		('unit_score'                   , 'helptext'): T("Value of all the units owned by the player"),
		},

	'players_settlements.xml' : {
		('balance'                      , 'text'    ): T("Balance"),
		('inhabitants'                  , 'text'    ): T("Inhabitants"),
		('running_costs'                , 'text'    ): T("Running costs"),
		('settlement_name'              , 'text'    ): T("Name"),
		('taxes'                        , 'text'    ): T("Taxes"),
		},

	'ships_list.xml' : {
		('health'                       , 'text'    ): T("Health"),
		('ship_name'                    , 'text'    ): T("Name"),
		('ship_type'                    , 'text'    ): T("Type"),
		('status'                       , 'text'    ): T("Status"),
		('weapons'                      , 'text'    ): T("Weapons"),
		},

	'stancewidget.xml' : {
		('aggressive_stance'            , 'helptext'): T("Aggressive"),
		('flee_stance'                  , 'helptext'): T("Flee"),
		('hold_ground_stance'           , 'helptext'): T("Hold ground"),
		('none_stance'                  , 'helptext'): T("Passive"),
		},

	'credits.xml' : {
		},

	'editor_create_map.xml' : {
		('headline_choose_map_size_lbl' , 'text'    ): T("Choose a map size:"),
		},

	'editor_select_map.xml' : {
		('headline_choose_map_lbl'      , 'text'    ): T("Choose a map:"),
		},

	'editor_select_saved_game.xml' : {
		('headline_choose_saved_game'   , 'text'    ): T("Choose a saved game's map:"),
		},

	'editor_start_menu.xml' : {
		('headline'                     , 'text'    ): T("Select map source"),
		('create_new_map'               , 'text'    ): T("Create new map"),
		('load_existing_map'            , 'text'    ): T("Load existing map"),
		('load_saved_game_map'          , 'text'    ): T("Load saved game's map"),
		('cancel'                       , 'helptext'): T("Exit to main menu"),
		('okay'                         , 'helptext'): T("Start editor"),
		},

	'help.xml' : {
		('okButton'                     , 'helptext'): T("Return"),
		},

	'hotkeys.xml' : {
		('reset_to_default'             , 'text'    ): T("Reset to default keys"),
		('labels_headline'              , 'text'    ): T("Actions"),
		('primary_buttons_headline'     , 'text'    ): T("Primary"),
		('secondary_buttons_headline'   , 'text'    ): T("Secondary"),
		('okButton'                     , 'helptext'): T("Exit to main menu"),
		('reset_to_default'             , 'helptext'): T("Reset to default"),
		('lbl_BUILD_TOOL'               , 'helptext'): T("Show build menu"),
		('lbl_CHAT'                     , 'helptext'): T("Chat"),
		('lbl_CONSOLE'                  , 'helptext'): T("Toggle showing FPS on/off"),
		('lbl_COORD_TOOLTIP'            , 'helptext'): T("Show coordinate values (Debug)"),
		('lbl_DESTROY_TOOL'             , 'helptext'): T("Enable destruct mode"),
		('lbl_DOWN'                     , 'helptext'): T("Scroll down"),
		('lbl_GRID'                     , 'helptext'): T("Toggle grid on/off"),
		('lbl_HEALTH_BAR'               , 'helptext'): T("Toggle health bars"),
		('lbl_HELP'                     , 'helptext'): T("Display help"),
		('lbl_LEFT'                     , 'helptext'): T("Scroll left"),
		('lbl_LOGBOOK'                  , 'helptext'): T("Toggle Captain's log"),
		('lbl_PAUSE'                    , 'helptext'): T("Pause game"),
		('lbl_PIPETTE'                  , 'helptext'): T("Enable pipette mode (clone buildings)"),
		('lbl_PLAYERS_OVERVIEW'         , 'helptext'): T("Show player scores"),
		('lbl_QUICKLOAD'                , 'helptext'): T("Quickload"),
		('lbl_QUICKSAVE'                , 'helptext'): T("Quicksave"),
		('lbl_REMOVE_SELECTED'          , 'helptext'): T("Remove selected units / buildings"),
		('lbl_RIGHT'                    , 'helptext'): T("Scroll right"),
		('lbl_ROAD_TOOL'                , 'helptext'): T("Enable road building mode"),
		('lbl_ROTATE_LEFT'              , 'helptext'): T("Rotate building or map counterclockwise"),
		('lbl_ROTATE_RIGHT'             , 'helptext'): T("Rotate building or map clockwise"),
		('lbl_SCREENSHOT'               , 'helptext'): T("Screenshot"),
		('lbl_SETTLEMENTS_OVERVIEW'     , 'helptext'): T("Show settlement list"),
		('lbl_SHIPS_OVERVIEW'           , 'helptext'): T("Show ship list"),
		('lbl_SHOW_SELECTED'            , 'helptext'): T("Focus camera on selection"),
		('lbl_SPEED_DOWN'               , 'helptext'): T("Decrease game speed"),
		('lbl_SPEED_UP'                 , 'helptext'): T("Increase game speed"),
		('lbl_TILE_OWNER_HIGHLIGHT'     , 'helptext'): T("Highlight tile ownership"),
		('lbl_TRANSLUCENCY'             , 'helptext'): T("Toggle translucency of ambient buildings"),
		('lbl_UP'                       , 'helptext'): T("Scroll up"),
		('lbl_ZOOM_IN'                  , 'helptext'): T("Zoom in"),
		('lbl_ZOOM_OUT'                 , 'helptext'): T("Zoom out"),
		},

	'ingamemenu.xml' : {
		('help'                         , 'text'    ): T("Help"),
		('loadgame'                     , 'text'    ): T("Load game"),
		('quit'                         , 'text'    ): T("Cancel game"),
		('savegame'                     , 'text'    ): T("Save game"),
		('settings'                     , 'text'    ): T("Settings"),
		('start'                        , 'text'    ): T("Return to game"),
		},

	'loadingscreen.xml' : {
		('loading_label'                , 'text'    ): T("Loading…"),
		},

	'mainmenu.xml' : {
		('changeBackground'             , 'text'    ): T("Change Background"),
		('credits_label'                , 'text'    ): T("Credits"),
		('editor_label'                 , 'text'    ): T("Editor"),
		('help_label'                   , 'text'    ): T("Help"),
		('load_label'                   , 'text'    ): T("Load game"),
		('multi_label'                  , 'text'    ): T("Multiplayer"),
		('quit_label'                   , 'text'    ): T("Quit"),
		('settings_label'               , 'text'    ): T("Settings"),
		('single_label'                 , 'text'    ): T("Singleplayer"),
		('version_label'                , 'text'    ): VERSION.string(),
		},

	'multiplayer_creategame.xml' : {
		('gamename_lbl'                 , 'text'    ): T("Name of the game:"),
		('headline'                     , 'text'    ): T("Choose a map:"),
		('headline'                     , 'text'    ): T("Create game - Multiplayer"),
		('mp_player_limit_lbl'          , 'text'    ): T("Player limit:"),
		('password_lbl'                 , 'text'    ): T("Password of the game:"),
		('cancel'                       , 'helptext'): T("Exit to multiplayer menu"),
		('create'                       , 'helptext'): T("Create this new game"),
		('gamename_lbl'                 , 'helptext'): T("This will be displayed to other players so they recognize the game."),
		('password_lbl'                 , 'helptext'): T("This game's password. Required to join this game."),
		},

	'multiplayer_gamelobby.xml' : {
		('game_player_color'            , 'text'    ): T("Color"),
		('game_player_status'           , 'text'    ): T("Status"),
		('game_start_notice'            , 'text'    ): T("The game will start as soon as all players are ready."),
		('headline'                     , 'text'    ): T("Chat:"),
		('headline'                     , 'text'    ): T("Gamelobby"),
		('ready_lbl'                    , 'text'    ): T("Ready:"),
		('startmessage'                 , 'text'    ): T("Game details:"),
		('cancel'                       , 'helptext'): T("Exit gamelobby"),
		('ready_btn'                    , 'helptext'): T("Sets your state to ready (necessary for the game to start)"),
		},

	'multiplayermenu.xml' : {
		('create_game_lbl'              , 'text'    ): T("Create game:"),
		('headline_active_games_lbl'    , 'text'    ): T("Active games:"),
		('headline_left'                , 'text'    ): T("New game - Multiplayer"),
		('join_game_lbl'                , 'text'    ): T("Join game:"),
		('load_game_lbl'                , 'text'    ): T("Load game:"),
		('refr_gamelist_lbl'            , 'text'    ): T("Refresh list:"),
		('cancel'                       , 'helptext'): T("Exit to main menu"),
		('create'                       , 'helptext'): T("Create a new game"),
		('join'                         , 'helptext'): T("Join the selected game"),
		('load'                         , 'helptext'): T("Load a saved game"),
		('refresh'                      , 'helptext'): T("Refresh list of active games"),
		},

	'set_player_details.xml' : {
		('headline_set_player_details'  , 'text'    ): T("Change player details"),
		},

	'settings.xml' : {
		('auto_unload_label'            , 'text'    ): T("Auto-unload ship:"),
		('autosave_interval_label'      , 'text'    ): T("Autosave interval in minutes:"),
		('cursor_centered_zoom_label'   , 'text'    ): T("Cursor centered zoom:"),
		('debug_log_lbl'                , 'text'    ): T("Enable logging:"),
		('edge_scrolling_label'         , 'text'    ): T("Scroll at map edge:"),
		('effect_volume_label'          , 'text'    ): T("Effects volume:"),
		('fps_label'                    , 'text'    ): T("Frame rate limit:"),
		('headline_graphics'            , 'text'    ): T("Graphics"),
		('headline_language'            , 'text'    ): T("Language"),
		('headline_misc'                , 'text'    ): T("General"),
		('headline_mouse'               , 'text'    ): T("Mouse"),
		('headline_network'             , 'text'    ): T("Network"),
		('headline_saving'              , 'text'    ): T("Saving"),
		('headline_sound'               , 'text'    ): T("Sound"),
		('middle_mouse_pan_lbl'         , 'text'    ): T("Middle mouse button pan:"),
		('mouse_sensitivity_label'      , 'text'    ): T("Mouse sensitivity:"),
		('music_volume_label'           , 'text'    ): T("Music volume:"),
		('network_port_lbl'             , 'text'    ): T("Network port:"),
		('number_of_autosaves_label'    , 'text'    ): T("Number of autosaves:"),
		('number_of_quicksaves_label'   , 'text'    ): T("Number of quicksaves:"),
		('quote_type_label'             , 'text'    ): T("Choose a quote type:"),
		('screen_fullscreen_text'       , 'text'    ): T("Full screen:"),
		('screen_resolution_label'      , 'text'    ): T("Screen resolution:"),
		('scroll_speed_label'           , 'text'    ): T("Scroll delay:"),
		('show_resource_icons_lbl'      , 'text'    ): T("Production indicators:"),
		('sound_enable_opt_text'        , 'text'    ): T("Enable sound:"),
		('uninterrupted_building_label' , 'text'    ): T("Uninterrupted building:"),
		('cancelButton'                 , 'helptext'): T("Discard current changes"),
		('defaultButton'                , 'helptext'): T("Reset to default settings"),
		('okButton'                     , 'helptext'): T("Save changes"),
		('auto_unload_label'            , 'helptext'): T("Whether to unload the ship after founding a settlement"),
		('cursor_centered_zoom_label'   , 'helptext'): T("When enabled, mouse wheel zoom will use the cursor position as new viewport center. When disabled, always zoom to current viewport center."),
		('debug_log_lbl'                , 'helptext'): T("Don't use in normal game session. Decides whether to write debug information in the logging directory of your user directory. Slows the game down."),
		('edge_scrolling_label'         , 'helptext'): T("Whether to move the viewport when the mouse pointer is close to map edges"),
		('fps_label'                    , 'helptext'): T("Set the maximum frame rate used. Default: 60 fps."),
		('middle_mouse_pan_lbl'         , 'helptext'): T("When enabled, dragging the middle mouse button will pan the camera"),
		('mouse_sensitivity_label'      , 'helptext'): T("0 is default system settings"),
		('network_port_lbl'             , 'helptext'): T("If set to 0, use the router default"),
		('quote_type_label'             , 'helptext'): T("What kind of quote to display while loading a game"),
		('scroll_speed_label'           , 'helptext'): T("Higher values slow down scrolling."),
		('show_resource_icons_lbl'      , 'helptext'): T("Whether to show resource icons over buildings whenever they finish production"),
		('uninterrupted_building_label' , 'helptext'): T("When enabled, do not exit the build mode after successful construction"),
		},

	'select_savegame.xml' : {
		('enter_filename_label'         , 'text'    ): T("Enter filename:"),
		('gamename_lbl'                 , 'text'    ): T("Name of the game:"),
		('gamepassword_lbl'             , 'text'    ): T("Password of the game:"),
		('headline_details_label'       , 'text'    ): T("Details:"),
		('headline_saved_games_label'   , 'text'    ): T("Your saved games:"),
		('cancelButton'                 , 'helptext'): T("Cancel"),
		('deleteButton'                 , 'helptext'): T("Delete selected savegame"),
		('gamename_lbl'                 , 'helptext'): T("This will be displayed to other players so they recognize the game."),
		('gamepassword_lbl'             , 'helptext'): T("Password of the game. Required to join this game"),
		},

	'singleplayermenu.xml' : {
		('headline'                     , 'text'    ): T("New game - Singleplayer"),
		('free_maps'                    , 'text'    ): T("Free play"),
		('random'                       , 'text'    ): T("Random map"),
		('scenario'                     , 'text'    ): T("Scenario"),
		('cancel'                       , 'helptext'): T("Exit to main menu"),
		('okay'                         , 'helptext'): T("Start game"),
		},

	'sp_free_maps.xml' : {
		('headline_choose_map_lbl'      , 'text'    ): T("Choose a map to play:"),
		},

	'sp_random.xml' : {
		('headline_map_settings_lbl'    , 'text'    ): T("Map settings:"),
		('seed_string_lbl'              , 'text'    ): T("Seed:"),
		},

	'sp_scenario.xml' : {
		('choose_map_lbl'               , 'text'    ): T("Choose a map to play:"),
		('select_lang_lbl'              , 'text'    ): T("Select a language:"),
		},

	'aidataselection.xml' : {
		('ai_players_label'             , 'text'    ): T("AI players:"),
		},

	'game_settings.xml' : {
		('headline_game_settings_lbl'   , 'text'    ): T("Game settings:"),
		('lbl_disasters'                , 'text'    ): T("Disasters"),
		('lbl_free_trader'              , 'text'    ): T("Free Trader"),
		('lbl_pirates'                  , 'text'    ): T("Pirates"),
		},

	'playerdataselection.xml' : {
		('color_label'                  , 'text'    ): T("Color:"),
		('player_label'                 , 'text'    ): T("Player name:"),
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
