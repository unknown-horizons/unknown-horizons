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
		# (text of widget: help)
		(u'help'                         , 'text'    ): _("Help"),
		# (text of widget: loadgame)
		(u'loadgame'                     , 'text'    ): _("Load map"),
		# (text of widget: quit)
		(u'quit'                         , 'text'    ): _("Exit editor"),
		# (text of widget: savegame)
		(u'savegame'                     , 'text'    ): _("Save map"),
		# (text of widget: settings)
		(u'settings'                     , 'text'    ): _("Settings"),
		# (text of widget: start)
		(u'start'                        , 'text'    ): _("Return to editor"),
		},

	'editor_settings.xml' : {
		# (text of widget: cursor_hint)
		(u'cursor_hint'                  , 'text'    ): _("(right click to stop)"),
		# (text of widget: headline_brush_size)
		(u'headline_brush_size'          , 'text'    ): _("Select brush size:"),
		# (text of widget: headline_terrain)
		(u'headline_terrain'             , 'text'    ): _("Select terrain:"),
		},

	'buildtab.xml' : {
		},

	'buildtab_no_settlement.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Game start"),
		# (text of widget: howto_1_need_warehouse)
		(u'howto_1_need_warehouse'       , 'text'    ): _("You need to found a settlement before you can construct buildings!"),
		# (text of widget: howto_2_navigate_ship)
		(u'howto_2_navigate_ship'        , 'text'    ): _("Select your ship and approach the coast via right-click."),
		# (text of widget: howto_3_build_warehouse)
		(u'howto_3_build_warehouse'      , 'text'    ): _("Afterwards, press the large button in the ship overview tab."),
		},

	'place_building.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Build"),
		# (text of widget: running_costs_label)
		(u'running_costs_label'          , 'text'    ): _("Running costs:"),
		},

	'related_buildings.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Related buildings"),
		},

	'city_info.xml' : {
		# (helptext of widget: city_info_inhabitants)
		(u'city_info_inhabitants'        , 'helptext'): _("Inhabitants"),
		},

	'messagewidget_icon.xml' : {
		},

	'messagewidget_message.xml' : {
		},

	'minimap.xml' : {
		# (helptext of widget: build)
		(u'build'                        , 'helptext'): _("Build menu (B)"),
		# (helptext of widget: destroy_tool)
		(u'destroy_tool'                 , 'helptext'): _("Destroy (X)"),
		# (helptext of widget: diplomacyButton)
		(u'diplomacyButton'              , 'helptext'): _("Diplomacy"),
		# (helptext of widget: gameMenuButton)
		(u'gameMenuButton'               , 'helptext'): _("Game menu (Esc)"),
		# (helptext of widget: logbook)
		(u'logbook'                      , 'helptext'): _("Captain's log (L)"),
		# (helptext of widget: rotateLeft)
		(u'rotateLeft'                   , 'helptext'): _("Rotate map counterclockwise (,)"),
		# (helptext of widget: rotateRight)
		(u'rotateRight'                  , 'helptext'): _("Rotate map clockwise (.)"),
		# (helptext of widget: speedDown)
		(u'speedDown'                    , 'helptext'): _("Decrease game speed (-)"),
		# (helptext of widget: speedUp)
		(u'speedUp'                      , 'helptext'): _("Increase game speed (+)"),
		# (helptext of widget: zoomIn)
		(u'zoomIn'                       , 'helptext'): _("Zoom in"),
		# (helptext of widget: zoomOut)
		(u'zoomOut'                      , 'helptext'): _("Zoom out"),
		},

	'resource_overview_bar_entry.xml' : {
		},

	'resource_overview_bar_gold.xml' : {
		},

	'resource_overview_bar_stats.xml' : {
		},

	'change_name.xml' : {
		# (text of widget: enter_new_name_lbl)
		(u'enter_new_name_lbl'           , 'text'    ): _("Enter new name:"),
		# (text of widget: headline_change_name)
		(u'headline_change_name'         , 'text'    ): _("Change name"),
		# (text of widget: old_name_label)
		(u'old_name_label'               , 'text'    ): _("Old name:"),
		# (helptext of widget: okButton)
		(u'okButton'                     , 'helptext'): _("Apply the new name"),
		},

	'chat.xml' : {
		# (text of widget: chat_lbl)
		(u'chat_lbl'                     , 'text'    ): _("Enter your message:"),
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Chat"),
		},

	'boatbuilder.xml' : {
		# (text of widget: BB_cancel_build_label) abort construction of a ship, lose invested resources
		(u'BB_cancel_build_label'        , 'text'    ): _("Cancel building:"),
		# (text of widget: BB_cancel_warning_label) abort construction of a ship, lose invested resources
		(u'BB_cancel_warning_label'      , 'text'    ): _("(lose all resources)"),
		# (text of widget: BB_current_order) Information about the ship currently under construction at the boat builder
		(u'BB_current_order'             , 'text'    ): _("Currently building:"),
		# (text of widget: BB_howto_build_lbl)
		(u'BB_howto_build_lbl'           , 'text'    ): _("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
		# (text of widget: BB_needed_res_label)
		(u'BB_needed_res_label'          , 'text'    ): _("Resources still needed:"),
		# (text of widget: BB_progress_label) Refers to the resources still missing to complete the current boat builder task
		(u'BB_progress_label'            , 'text'    ): _("Construction progress:"),
		# (helptext of widget: BB_cancel_button) abort construction of a ship, lose invested resources
		(u'BB_cancel_button'             , 'helptext'): _("Cancel all building progress"),
		# (helptext of widget: running_costs_label)
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		# (helptext of widget: toggle_active_active) Pauses the current ship production, can be resumed later
		(u'toggle_active_active'         , 'helptext'): _("Pause"),
		# (helptext of widget: toggle_active_inactive) Resumes the currently paused ship production
		(u'toggle_active_inactive'       , 'helptext'): _("Resume"),
		},

	'boatbuilder_showcase.xml' : {
		},

	'diplomacy.xml' : {
		# (text of widget: ally_label) Diplomacy state of player
		(u'ally_label'                   , 'text'    ): _("ally"),
		# (text of widget: enemy_label) Diplomacy state of player
		(u'enemy_label'                  , 'text'    ): _("enemy"),
		# (text of widget: neutral_label) Diplomacy state of player
		(u'neutral_label'                , 'text'    ): _("neutral"),
		},

	'overview_farm.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Building overview"),
		# (helptext of widget: capacity_utilization_label)
		(u'capacity_utilization_label'   , 'helptext'): _("Capacity utilization"),
		# (helptext of widget: running_costs_label)
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		# (helptext of widget: capacity_utilization)
		(u'capacity_utilization'         , 'helptext'): _("Capacity utilization"),
		# (helptext of widget: running_costs)
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'island_inventory.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Settlement inventory"),
		},

	'mainsquare_inhabitants.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Settler overview"),
		# (text of widget: headline_happiness_per_house)
		(u'headline_happiness_per_house' , 'text'    ): _("Happiness per house"),
		# (text of widget: headline_residents_per_house)
		(u'headline_residents_per_house' , 'text'    ): _("Residents per house"),
		# (text of widget: headline_residents_total)
		(u'headline_residents_total'     , 'text'    ): _("Summary"),
		# (text of widget: houses)
		(u'houses'                       , 'text'    ): _("houses"),
		# (text of widget: residents)
		(u'residents'                    , 'text'    ): _("residents"),
		# (text of widget: tax_label)
		(u'tax_label'                    , 'text'    ): _("Taxes:"),
		# (text of widget: upgrades_lbl)
		(u'upgrades_lbl'                 , 'text'    ): _("Upgrade permissions:"),
		# (helptext of widget: avg_icon)
		(u'avg_icon'                     , 'helptext'): _("satisfied"),
		# (helptext of widget: happiness_house_icon)
		(u'happiness_house_icon'         , 'helptext'): _("Amount of houses with this happiness"),
		# (helptext of widget: happy_icon)
		(u'happy_icon'                   , 'helptext'): _("happy"),
		# (helptext of widget: houses_icon)
		(u'houses_icon'                  , 'helptext'): _("Houses with this amount of inhabitants"),
		# (helptext of widget: inhabitants_icon)
		(u'inhabitants_icon'             , 'helptext'): _("Number of inhabitants per house"),
		# (helptext of widget: paid_taxes_icon)
		(u'paid_taxes_icon'              , 'helptext'): _("Paid taxes"),
		# (helptext of widget: sad_icon)
		(u'sad_icon'                     , 'helptext'): _("sad"),
		# (helptext of widget: tax_rate_icon)
		(u'tax_rate_icon'                , 'helptext'): _("Tax rate"),
		# (helptext of widget: tax_val_label)
		(u'tax_val_label'                , 'helptext'): _("Tax rate"),
		# (helptext of widget: taxes)
		(u'taxes'                        , 'helptext'): _("Paid taxes"),
		},

	'overview_enemybuilding.xml' : {
		},

	'overview_enemyunit.xml' : {
		},

	'overview_enemywarehouse.xml' : {
		# (text of widget: buying_label)
		(u'buying_label'                 , 'text'    ): _("Buying"),
		# (text of widget: selling_label)
		(u'selling_label'                , 'text'    ): _("Selling"),
		},

	'overview_firestation.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Building overview"),
		# (text of widget: name_label)
		(u'name_label'                   , 'text'    ): _("Name:"),
		# (helptext of widget: running_costs_label)
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		# (helptext of widget: running_costs)
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_groundunit.xml' : {
		# (text of widget: lbl_weapon_storage)
		(u'lbl_weapon_storage'           , 'text'    ): _("Weapons:"),
		},

	'overview_productionbuilding.xml' : {
		# (helptext of widget: capacity_utilization_label)
		(u'capacity_utilization_label'   , 'helptext'): _("Capacity utilization"),
		# (helptext of widget: running_costs_label)
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		# (helptext of widget: capacity_utilization)
		(u'capacity_utilization'         , 'helptext'): _("Capacity utilization"),
		# (helptext of widget: running_costs)
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_resourcedeposit.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Resource deposit"),
		# (text of widget: res_dep_description_lbl)
		(u'res_dep_description_lbl'      , 'text'    ): _("This is a resource deposit where you can build a mine to dig up resources."),
		# (text of widget: res_dep_description_lbl2) It == The resource deposit
		(u'res_dep_description_lbl2'     , 'text'    ): _("It contains these resources:"),
		},

	'overview_settler.xml' : {
		# (text of widget: needed_res_label)
		(u'needed_res_label'             , 'text'    ): _("Needed resources:"),
		# (text of widget: tax_label)
		(u'tax_label'                    , 'text'    ): _("Taxes:"),
		# (helptext of widget: happiness_label)
		(u'happiness_label'              , 'helptext'): _("Happiness"),
		# (helptext of widget: paid_taxes_label)
		(u'paid_taxes_label'             , 'helptext'): _("Paid taxes"),
		# (helptext of widget: paid_taxes_label)
		(u'paid_taxes_label'             , 'helptext'): _("Tax rate"),
		# (helptext of widget: residents_label)
		(u'residents_label'              , 'helptext'): _("Residents"),
		# (helptext of widget: inhabitants)
		(u'inhabitants'                  , 'helptext'): _("Residents"),
		# (helptext of widget: tax_val_label)
		(u'tax_val_label'                , 'helptext'): _("Tax rate"),
		# (helptext of widget: taxes)
		(u'taxes'                        , 'helptext'): _("Paid taxes"),
		# (helptext of widget: happiness)
		(u'happiness'                    , 'helptext'): _("Happiness"),
		},

	'overview_signalfire.xml' : {
		# (text of widget: signal_fire_description_lbl)
		(u'signal_fire_description_lbl'  , 'text'    ): _("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods."),
		},

	'overview_tower.xml' : {
		# (text of widget: name_label)
		(u'name_label'                   , 'text'    ): _("Name:"),
		# (helptext of widget: running_costs_label)
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		# (helptext of widget: running_costs)
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overview_tradership.xml' : {
		# (text of widget: trader_description_lbl)
		(u'trader_description_lbl'       , 'text'    ): _("This is the free trader's ship. It will visit you from time to time to buy or sell goods."),
		},

	'overview_warehouse.xml' : {
		# (text of widget: name_label)
		(u'name_label'                   , 'text'    ): _("Name:"),
		# (helptext of widget: collector_utilization_label)
		(u'collector_utilization_label'  , 'helptext'): _("Collector utilization"),
		# (helptext of widget: running_costs_label)
		(u'running_costs_label'          , 'helptext'): _("Running costs"),
		# (helptext of widget: collector_utilization) Percentage describing how busy the collectors were (100% = always going for / already carrying full load of goods)
		(u'collector_utilization'        , 'helptext'): _("Collector utilization"),
		# (helptext of widget: running_costs)
		(u'running_costs'                , 'helptext'): _("Running costs"),
		},

	'overviewtab.xml' : {
		},

	'overview_select_multi.xml' : {
		},

	'unit_entry_widget.xml' : {
		},

	'overview_trade_ship.xml' : {
		# (helptext of widget: configure_route)
		(u'configure_route'              , 'helptext'): _("Configure trading route"),
		# (helptext of widget: found_settlement)
		(u'found_settlement'             , 'helptext'): _("Build settlement"),
		# (helptext of widget: trade)
		(u'trade'                        , 'helptext'): _("Trade"),
		},

	'overview_war_ship.xml' : {
		# (helptext of widget: configure_route)
		(u'configure_route'              , 'helptext'): _("Configure trading route"),
		# (helptext of widget: found_settlement)
		(u'found_settlement'             , 'helptext'): _("Build settlement"),
		# (helptext of widget: trade)
		(u'trade'                        , 'helptext'): _("Trade"),
		},

	'tradetab.xml' : {
		# (text of widget: buying_label)
		(u'buying_label'                 , 'text'    ): _("Buying"),
		# (text of widget: exchange_label)
		(u'exchange_label'               , 'text'    ): _("Exchange:"),
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Trade"),
		# (text of widget: selling_label)
		(u'selling_label'                , 'text'    ): _("Selling"),
		# (text of widget: ship_label)
		(u'ship_label'                   , 'text'    ): _("Ship:"),
		# (text of widget: trade_with_label)
		(u'trade_with_label'             , 'text'    ): _("Trade partner:"),
		},

	'tab_base.xml' : {
		},

	'buysellmenu.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Buy or sell resources"),
		# (text of widget: headline_trade_history)
		(u'headline_trade_history'       , 'text'    ): _("Trade history"),
		},

	'select_trade_resource.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Select resources:"),
		},

	'tab_account.xml' : {
		# (text of widget: buy_expenses_label)
		(u'buy_expenses_label'           , 'text'    ): _("Buying"),
		# (text of widget: headline_balance_label)
		(u'headline_balance_label'       , 'text'    ): _("Balance:"),
		# (text of widget: headline_expenses_label)
		(u'headline_expenses_label'      , 'text'    ): _("Expenses:"),
		# (text of widget: headline_income_label)
		(u'headline_income_label'        , 'text'    ): _("Income:"),
		# (text of widget: running_costs_label)
		(u'running_costs_label'          , 'text'    ): _("Running costs"),
		# (text of widget: sell_income_label)
		(u'sell_income_label'            , 'text'    ): _("Sale"),
		# (text of widget: taxes_label)
		(u'taxes_label'                  , 'text'    ): _("Taxes"),
		# (helptext of widget: show_production_overview)
		(u'show_production_overview'     , 'helptext'): _("Show resources produced in this settlement"),
		},

	'trade_single_slot.xml' : {
		},

	'overview_farmproductionline.xml' : {
		# (helptext of widget: toggle_active_active)
		(u'toggle_active_active'         , 'helptext'): _("Pause production"),
		# (helptext of widget: toggle_active_inactive)
		(u'toggle_active_inactive'       , 'helptext'): _("Start production"),
		},

	'overview_productionline.xml' : {
		# (helptext of widget: toggle_active_active)
		(u'toggle_active_active'         , 'helptext'): _("Pause production"),
		# (helptext of widget: toggle_active_inactive)
		(u'toggle_active_inactive'       , 'helptext'): _("Start production"),
		},

	'related_buildings_container.xml' : {
		},

	'resbar_resource_selection.xml' : {
		# (text of widget: headline) Please keep the translation similarly short and concise, else the tooltip is not well understood by players.
		(u'headline'                     , 'text'    ): _("Select resource:"),
		# (helptext of widget: make_default_btn)
		(u'make_default_btn'             , 'helptext'): _("Save current resource configuration as default for all settlements."),
		# (helptext of widget: reset_default_btn)
		(u'reset_default_btn'            , 'helptext'): _("Reset default resource configuration for all settlements."),
		# (helptext of widget: headline) Please keep the translation similarly short and concise, else the tooltip is not well understood by players.
		(u'headline'                     , 'helptext'): _("The resource you select is displayed instead of the current one. Empty by clicking on X."),
		},

	'route_entry.xml' : {
		# (helptext of widget: delete_warehouse) Trade route entry
		(u'delete_warehouse'             , 'helptext'): _("Delete entry"),
		# (helptext of widget: move_down) Trade route entry
		(u'move_down'                    , 'helptext'): _("Move down"),
		# (helptext of widget: move_up) Trade route entry
		(u'move_up'                      , 'helptext'): _("Move up"),
		},

	'trade_history_item.xml' : {
		},

	'traderoute_resource_selection.xml' : {
		# (text of widget: select_res_label)
		(u'select_res_label'             , 'text'    ): _("Select a resource:"),
		},

	'captains_log.xml' : {
		# (text of widget: stats_players)
		(u'stats_players'                , 'text'    ): _("Players"),
		# (text of widget: stats_settlements)
		(u'stats_settlements'            , 'text'    ): _("My settlements"),
		# (text of widget: stats_ships)
		(u'stats_ships'                  , 'text'    ): _("My ships"),
		# (text of widget: weird_button_1) Displays all notifications and game messages
		(u'weird_button_1'               , 'text'    ): _("Whole world"),
		# (text of widget: weird_button_4) Sends the chat messages to all players (default)
		(u'weird_button_4'               , 'text'    ): _("Everybody"),
		# (text of widget: headline_chat)
		(u'headline_chat'                , 'text'    ): _("Chat"),
		# (text of widget: headline_game_messages)
		(u'headline_game_messages'       , 'text'    ): _("Game messages"),
		# (text of widget: headline_statistics)
		(u'headline_statistics'          , 'text'    ): _("Statistics"),
		# (helptext of widget: okButton)
		(u'okButton'                     , 'helptext'): _("Return to game"),
		# (helptext of widget: weird_button_4) Sends the chat messages to all players (default)
		(u'weird_button_4'               , 'helptext'): _("Sends the chat messages to all players."),
		# (helptext of widget: backwardButton) Entry of Captain's Log (logbook/diary used in scenarios)
		(u'backwardButton'               , 'helptext'): _("Read previous entries"),
		# (helptext of widget: forwardButton) Entry of Captain's Log (logbook/diary used in scenarios)
		(u'forwardButton'                , 'helptext'): _("Read next entries"),
		},

	'configure_route.xml' : {
		# (text of widget: lbl_route_activity)
		(u'lbl_route_activity'           , 'text'    ): _("Route activity:"),
		# (text of widget: lbl_wait_at_load) Trade route setting: Whether to wait until all goods could be loaded.
		(u'lbl_wait_at_load'             , 'text'    ): _("Wait at load:"),
		# (text of widget: lbl_wait_at_unload) Trade route setting: Whether to wait until all goods could be unloaded.
		(u'lbl_wait_at_unload'           , 'text'    ): _("Wait at unload:"),
		# (helptext of widget: okButton)
		(u'okButton'                     , 'helptext'): _("Exit"),
		# (helptext of widget: start_route) Trade route
		(u'start_route'                  , 'helptext'): _("Start route"),
		},

	'healthwidget.xml' : {
		},

	'island_production.xml' : {
		# (helptext of widget: okButton)
		(u'okButton'                     , 'helptext'): _("Close"),
		},

	'players_overview.xml' : {
		# (text of widget: building_score)
		(u'building_score'               , 'text'    ): _("Buildings"),
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Player scores"),
		# (text of widget: land_score)
		(u'land_score'                   , 'text'    ): _("Land"),
		# (text of widget: money_score)
		(u'money_score'                  , 'text'    ): _("Money"),
		# (text of widget: player_name)
		(u'player_name'                  , 'text'    ): _("Name"),
		# (text of widget: resource_score)
		(u'resource_score'               , 'text'    ): _("Resources"),
		# (text of widget: settler_score)
		(u'settler_score'                , 'text'    ): _("Settlers"),
		# (text of widget: total_score)
		(u'total_score'                  , 'text'    ): _("Total"),
		# (text of widget: unit_score)
		(u'unit_score'                   , 'text'    ): _("Units"),
		# (helptext of widget: building_score)
		(u'building_score'               , 'helptext'): _("Value of all the buildings in the player's settlement(s)"),
		# (helptext of widget: land_score)
		(u'land_score'                   , 'helptext'): _("Value of usable land i.e Amount of Land that can be used to create buildings "),
		# (helptext of widget: money_score)
		(u'money_score'                  , 'helptext'): _("Player's current treasury + income expected in near future"),
		# (helptext of widget: player_name)
		(u'player_name'                  , 'helptext'): _("Player Name"),
		# (helptext of widget: resource_score)
		(u'resource_score'               , 'helptext'): _("Value of resources generated from all the possible sources in the player's settlement(s)"),
		# (helptext of widget: settler_score)
		(u'settler_score'                , 'helptext'): _("Value denoting the progress of the settlement(s) in terms of inhabitants, buildings and overall happiness"),
		# (helptext of widget: total_score)
		(u'total_score'                  , 'helptext'): _("The total value from all individual entities or in short : Total Player Score"),
		# (helptext of widget: unit_score)
		(u'unit_score'                   , 'helptext'): _("Value of all the units owned by the player"),
		},

	'players_settlements.xml' : {
		# (text of widget: balance)
		(u'balance'                      , 'text'    ): _("Balance"),
		# (text of widget: inhabitants)
		(u'inhabitants'                  , 'text'    ): _("Inhabitants"),
		# (text of widget: running_costs)
		(u'running_costs'                , 'text'    ): _("Running costs"),
		# (text of widget: settlement_name)
		(u'settlement_name'              , 'text'    ): _("Name"),
		# (text of widget: taxes)
		(u'taxes'                        , 'text'    ): _("Taxes"),
		},

	'ships_list.xml' : {
		# (text of widget: health)
		(u'health'                       , 'text'    ): _("Health"),
		# (text of widget: ship_name)
		(u'ship_name'                    , 'text'    ): _("Name"),
		# (text of widget: ship_type)
		(u'ship_type'                    , 'text'    ): _("Type"),
		# (text of widget: status)
		(u'status'                       , 'text'    ): _("Status"),
		# (text of widget: weapons)
		(u'weapons'                      , 'text'    ): _("Weapons"),
		},

	'stancewidget.xml' : {
		# (helptext of widget: aggressive_stance) Description of combat stance (how units behave when fighting)
		(u'aggressive_stance'            , 'helptext'): _("Aggressive"),
		# (helptext of widget: flee_stance) Description of combat stance (how units behave when fighting)
		(u'flee_stance'                  , 'helptext'): _("Flee"),
		# (helptext of widget: hold_ground_stance) Description of combat stance (how units behave when fighting)
		(u'hold_ground_stance'           , 'helptext'): _("Hold ground"),
		# (helptext of widget: none_stance) Description of combat stance (how units behave when fighting)
		(u'none_stance'                  , 'helptext'): _("Passive"),
		},

	'credits.xml' : {
		},

	'editor_create_map.xml' : {
		# (text of widget: headline_choose_map_size_lbl)
		(u'headline_choose_map_size_lbl' , 'text'    ): _("Choose a map size:"),
		},

	'editor_select_map.xml' : {
		# (text of widget: headline_choose_map_lbl)
		(u'headline_choose_map_lbl'      , 'text'    ): _("Choose a map:"),
		},

	'editor_select_saved_game.xml' : {
		# (text of widget: headline_choose_saved_game)
		(u'headline_choose_saved_game'   , 'text'    ): _("Choose a saved game's map:"),
		},

	'editor_start_menu.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Select map source"),
		# (text of widget: create_new_map)
		(u'create_new_map'               , 'text'    ): _("Create new map"),
		# (text of widget: load_existing_map)
		(u'load_existing_map'            , 'text'    ): _("Load existing map"),
		# (text of widget: load_saved_game_map)
		(u'load_saved_game_map'          , 'text'    ): _("Load saved game's map"),
		# (helptext of widget: cancel)
		(u'cancel'                       , 'helptext'): _("Exit to main menu"),
		# (helptext of widget: okay)
		(u'okay'                         , 'helptext'): _("Start editor"),
		},

	'help.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Key bindings"),
		# (text of widget: lbl_BUILD_TOOL)
		(u'lbl_BUILD_TOOL'               , 'text'    ): _("Show build menu"),
		# (text of widget: lbl_CHAT)
		(u'lbl_CHAT'                     , 'text'    ): _("Chat"),
		# (text of widget: lbl_CONSOLE)
		(u'lbl_CONSOLE'                  , 'text'    ): _("Display FPS counter"),
		# (text of widget: lbl_COORD_TOOLTIP)
		(u'lbl_COORD_TOOLTIP'            , 'text'    ): _("Show coordinate values (Debug)"),
		# (text of widget: lbl_DESTROY_TOOL)
		(u'lbl_DESTROY_TOOL'             , 'text'    ): _("Enable destruct mode"),
		# (text of widget: lbl_DOWN)
		(u'lbl_DOWN'                     , 'text'    ): _("Scroll down"),
		# (text of widget: lbl_ESCAPE)
		(u'lbl_ESCAPE'                   , 'text'    ): _("Close dialogs"),
		# (text of widget: lbl_GRID)
		(u'lbl_GRID'                     , 'text'    ): _("Toggle grid on/off"),
		# (text of widget: lbl_HEALTH_BAR)
		(u'lbl_HEALTH_BAR'               , 'text'    ): _("Toggle health bars"),
		# (text of widget: lbl_HELP)
		(u'lbl_HELP'                     , 'text'    ): _("Display help"),
		# (text of widget: lbl_LEFT)
		(u'lbl_LEFT'                     , 'text'    ): _("Scroll left"),
		# (text of widget: lbl_LOGBOOK)
		(u'lbl_LOGBOOK'                  , 'text'    ): _("Toggle Captain's log"),
		# (text of widget: lbl_PAUSE)
		(u'lbl_PAUSE'                    , 'text'    ): _("Pause game"),
		# (text of widget: lbl_PIPETTE)
		(u'lbl_PIPETTE'                  , 'text'    ): _("Enable pipette mode (clone buildings)"),
		# (text of widget: lbl_PLAYERS_OVERVIEW)
		(u'lbl_PLAYERS_OVERVIEW'         , 'text'    ): _("Show player scores"),
		# (text of widget: lbl_QUICKLOAD)
		(u'lbl_QUICKLOAD'                , 'text'    ): _("Quickload"),
		# (text of widget: lbl_QUICKSAVE)
		(u'lbl_QUICKSAVE'                , 'text'    ): _("Quicksave"),
		# (text of widget: lbl_REMOVE_SELECTED)
		(u'lbl_REMOVE_SELECTED'          , 'text'    ): _("Remove selected units / buildings"),
		# (text of widget: lbl_RIGHT)
		(u'lbl_RIGHT'                    , 'text'    ): _("Scroll right"),
		# (text of widget: lbl_ROAD_TOOL)
		(u'lbl_ROAD_TOOL'                , 'text'    ): _("Enable road building mode"),
		# (text of widget: lbl_ROTATE_LEFT)
		(u'lbl_ROTATE_LEFT'              , 'text'    ): _("Rotate building or map counterclockwise"),
		# (text of widget: lbl_ROTATE_RIGHT)
		(u'lbl_ROTATE_RIGHT'             , 'text'    ): _("Rotate building or map clockwise"),
		# (text of widget: lbl_SCREENSHOT)
		(u'lbl_SCREENSHOT'               , 'text'    ): _("Screenshot"),
		# (text of widget: lbl_SETTLEMENTS_OVERVIEW)
		(u'lbl_SETTLEMENTS_OVERVIEW'     , 'text'    ): _("Show settlement list"),
		# (text of widget: lbl_SHIFT)
		(u'lbl_SHIFT'                    , 'text'    ): _("Hold to place multiple buildings"),
		# (text of widget: lbl_SHIPS_OVERVIEW)
		(u'lbl_SHIPS_OVERVIEW'           , 'text'    ): _("Show ship list"),
		# (text of widget: lbl_SHOW_SELECTED)
		(u'lbl_SHOW_SELECTED'            , 'text'    ): _("Focus camera on selection"),
		# (text of widget: lbl_SPEED_DOWN)
		(u'lbl_SPEED_DOWN'               , 'text'    ): _("Decrease game speed"),
		# (text of widget: lbl_SPEED_UP)
		(u'lbl_SPEED_UP'                 , 'text'    ): _("Increase game speed"),
		# (text of widget: lbl_TILE_OWNER_HIGHLIGHT)
		(u'lbl_TILE_OWNER_HIGHLIGHT'     , 'text'    ): _("Highlight tile ownership"),
		# (text of widget: lbl_TRANSLUCENCY)
		(u'lbl_TRANSLUCENCY'             , 'text'    ): _("Toggle translucency of ambient buildings"),
		# (text of widget: lbl_UP)
		(u'lbl_UP'                       , 'text'    ): _("Scroll up"),
		# (helptext of widget: okButton)
		(u'okButton'                     , 'helptext'): _("Return"),
		},

	'hotkeys.xml' : {
		# (text of widget: reset_to_default)
		(u'reset_to_default'             , 'text'    ): _("Reset to default keys"),
		# (text of widget: labels_headline)
		(u'labels_headline'              , 'text'    ): _("Actions"),
		# (text of widget: primary_buttons_headline)
		(u'primary_buttons_headline'     , 'text'    ): _("Primary"),
		# (text of widget: secondary_buttons_headline)
		(u'secondary_buttons_headline'   , 'text'    ): _("Secondary"),
		# (helptext of widget: okButton)
		(u'okButton'                     , 'helptext'): _("Exit to main menu"),
		# (helptext of widget: reset_to_default)
		(u'reset_to_default'             , 'helptext'): _("Reset to default"),
		# (helptext of widget: lbl_BUILD_TOOL)
		(u'lbl_BUILD_TOOL'               , 'helptext'): _("Show build menu"),
		# (helptext of widget: lbl_CHAT)
		(u'lbl_CHAT'                     , 'helptext'): _("Chat"),
		# (helptext of widget: lbl_CONSOLE)
		(u'lbl_CONSOLE'                  , 'helptext'): _("Toggle showing FPS on/off"),
		# (helptext of widget: lbl_COORD_TOOLTIP)
		(u'lbl_COORD_TOOLTIP'            , 'helptext'): _("Show coordinate values (Debug)"),
		# (helptext of widget: lbl_DESTROY_TOOL)
		(u'lbl_DESTROY_TOOL'             , 'helptext'): _("Enable destruct mode"),
		# (helptext of widget: lbl_DOWN)
		(u'lbl_DOWN'                     , 'helptext'): _("Scroll down"),
		# (helptext of widget: lbl_GRID)
		(u'lbl_GRID'                     , 'helptext'): _("Toggle grid on/off"),
		# (helptext of widget: lbl_HEALTH_BAR)
		(u'lbl_HEALTH_BAR'               , 'helptext'): _("Toggle health bars"),
		# (helptext of widget: lbl_HELP)
		(u'lbl_HELP'                     , 'helptext'): _("Display help"),
		# (helptext of widget: lbl_LEFT)
		(u'lbl_LEFT'                     , 'helptext'): _("Scroll left"),
		# (helptext of widget: lbl_LOGBOOK)
		(u'lbl_LOGBOOK'                  , 'helptext'): _("Toggle Captain's log"),
		# (helptext of widget: lbl_PAUSE)
		(u'lbl_PAUSE'                    , 'helptext'): _("Pause game"),
		# (helptext of widget: lbl_PIPETTE)
		(u'lbl_PIPETTE'                  , 'helptext'): _("Enable pipette mode (clone buildings)"),
		# (helptext of widget: lbl_PLAYERS_OVERVIEW)
		(u'lbl_PLAYERS_OVERVIEW'         , 'helptext'): _("Show player scores"),
		# (helptext of widget: lbl_QUICKLOAD)
		(u'lbl_QUICKLOAD'                , 'helptext'): _("Quickload"),
		# (helptext of widget: lbl_QUICKSAVE)
		(u'lbl_QUICKSAVE'                , 'helptext'): _("Quicksave"),
		# (helptext of widget: lbl_REMOVE_SELECTED)
		(u'lbl_REMOVE_SELECTED'          , 'helptext'): _("Remove selected units / buildings"),
		# (helptext of widget: lbl_RIGHT)
		(u'lbl_RIGHT'                    , 'helptext'): _("Scroll right"),
		# (helptext of widget: lbl_ROAD_TOOL)
		(u'lbl_ROAD_TOOL'                , 'helptext'): _("Enable road building mode"),
		# (helptext of widget: lbl_ROTATE_LEFT)
		(u'lbl_ROTATE_LEFT'              , 'helptext'): _("Rotate building or map counterclockwise"),
		# (helptext of widget: lbl_ROTATE_RIGHT)
		(u'lbl_ROTATE_RIGHT'             , 'helptext'): _("Rotate building or map clockwise"),
		# (helptext of widget: lbl_SCREENSHOT)
		(u'lbl_SCREENSHOT'               , 'helptext'): _("Screenshot"),
		# (helptext of widget: lbl_SETTLEMENTS_OVERVIEW)
		(u'lbl_SETTLEMENTS_OVERVIEW'     , 'helptext'): _("Show settlement list"),
		# (helptext of widget: lbl_SHIPS_OVERVIEW)
		(u'lbl_SHIPS_OVERVIEW'           , 'helptext'): _("Show ship list"),
		# (helptext of widget: lbl_SHOW_SELECTED)
		(u'lbl_SHOW_SELECTED'            , 'helptext'): _("Focus camera on selection"),
		# (helptext of widget: lbl_SPEED_DOWN)
		(u'lbl_SPEED_DOWN'               , 'helptext'): _("Decrease game speed"),
		# (helptext of widget: lbl_SPEED_UP)
		(u'lbl_SPEED_UP'                 , 'helptext'): _("Increase game speed"),
		# (helptext of widget: lbl_TILE_OWNER_HIGHLIGHT)
		(u'lbl_TILE_OWNER_HIGHLIGHT'     , 'helptext'): _("Highlight tile ownership"),
		# (helptext of widget: lbl_TRANSLUCENCY)
		(u'lbl_TRANSLUCENCY'             , 'helptext'): _("Toggle translucency of ambient buildings"),
		# (helptext of widget: lbl_UP)
		(u'lbl_UP'                       , 'helptext'): _("Scroll up"),
		},

	'ingamemenu.xml' : {
		# (text of widget: help)
		(u'help'                         , 'text'    ): _("Help"),
		# (text of widget: loadgame)
		(u'loadgame'                     , 'text'    ): _("Load game"),
		# (text of widget: quit)
		(u'quit'                         , 'text'    ): _("Cancel game"),
		# (text of widget: savegame)
		(u'savegame'                     , 'text'    ): _("Save game"),
		# (text of widget: settings)
		(u'settings'                     , 'text'    ): _("Settings"),
		# (text of widget: start)
		(u'start'                        , 'text'    ): _("Return to game"),
		},

	'loadingscreen.xml' : {
		# (text of widget: loading_label)
		(u'loading_label'                , 'text'    ): _("Loading ..."),
		},

	'mainmenu.xml' : {
		# (text of widget: credits_label)
		(u'credits_label'                , 'text'    ): _("Credits"),
		# (text of widget: editor_label) Map editor
		(u'editor_label'                 , 'text'    ): _("Editor"),
		# (text of widget: help_label) Main / in-game menu entry
		(u'help_label'                   , 'text'    ): _("Help"),
		# (text of widget: load_label) Open a widget to select which game to load
		(u'load_label'                   , 'text'    ): _("Load game"),
		# (text of widget: multi_label) Opens widget to join or create multiplayer games
		(u'multi_label'                  , 'text'    ): _("Multiplayer"),
		# (text of widget: quit_label) Completely shut down UH
		(u'quit_label'                   , 'text'    ): _("Quit"),
		# (text of widget: settings_label) Main / in-game menu entry
		(u'settings_label'               , 'text'    ): _("Settings"),
		# (text of widget: single_label) Opens widget to create singleplayer games (scenarios, random maps, free play)
		(u'single_label'                 , 'text'    ): _("Singleplayer"),
		# (text of widget: version_label)
		(u'version_label'                , 'text'    ): VERSION.string(),
		},

	'multiplayer_creategame.xml' : {
		# (text of widget: create_game_lbl)
		(u'create_game_lbl'              , 'text'    ): _("Create game:"),
		# (text of widget: exit_to_mp_menu_lbl)
		(u'exit_to_mp_menu_lbl'          , 'text'    ): _("Back:"),
		# (text of widget: gamename_lbl)
		(u'gamename_lbl'                 , 'text'    ): _("Name of the game:"),
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Choose a map:"),
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Create game - Multiplayer"),
		# (text of widget: mp_player_limit_lbl)
		(u'mp_player_limit_lbl'          , 'text'    ): _("Player limit:"),
		# (text of widget: password_lbl)
		(u'password_lbl'                 , 'text'    ): _("Password of the game:"),
		# (helptext of widget: cancel)
		(u'cancel'                       , 'helptext'): _("Exit to multiplayer menu"),
		# (helptext of widget: create)
		(u'create'                       , 'helptext'): _("Create this new game"),
		# (helptext of widget: gamename_lbl)
		(u'gamename_lbl'                 , 'helptext'): _("This will be displayed to other players so they recognize the game."),
		# (helptext of widget: password_lbl)
		(u'password_lbl'                 , 'helptext'): _("This game's password. Required to join this game."),
		},

	'multiplayer_gamelobby.xml' : {
		# (text of widget: exit_to_mp_menu_lbl)
		(u'exit_to_mp_menu_lbl'          , 'text'    ): _("Leave:"),
		# (text of widget: game_player_color)
		(u'game_player_color'            , 'text'    ): _("Color"),
		# (text of widget: game_player_status)
		(u'game_player_status'           , 'text'    ): _("Status"),
		# (text of widget: game_start_notice)
		(u'game_start_notice'            , 'text'    ): _("The game will start as soon as all players are ready."),
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Chat:"),
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("Gamelobby"),
		# (text of widget: ready_lbl)
		(u'ready_lbl'                    , 'text'    ): _("Ready:"),
		# (text of widget: startmessage)
		(u'startmessage'                 , 'text'    ): _("Game details:"),
		# (helptext of widget: cancel)
		(u'cancel'                       , 'helptext'): _("Exit gamelobby"),
		# (helptext of widget: ready_btn)
		(u'ready_btn'                    , 'helptext'): _("Sets your state to ready (necessary for the game to start)"),
		},

	'multiplayermenu.xml' : {
		# (text of widget: create_game_lbl)
		(u'create_game_lbl'              , 'text'    ): _("Create game:"),
		# (text of widget: exit_to_main_menu_lbl)
		(u'exit_to_main_menu_lbl'        , 'text'    ): _("Main menu:"),
		# (text of widget: headline_active_games_lbl)
		(u'headline_active_games_lbl'    , 'text'    ): _("Active games:"),
		# (text of widget: headline_left)
		(u'headline_left'                , 'text'    ): _("New game - Multiplayer"),
		# (text of widget: join_game_lbl)
		(u'join_game_lbl'                , 'text'    ): _("Join game"),
		# (text of widget: load_game_lbl)
		(u'load_game_lbl'                , 'text'    ): _("Load game:"),
		# (text of widget: refr_gamelist_lbl)
		(u'refr_gamelist_lbl'            , 'text'    ): _("Refresh list:"),
		# (helptext of widget: cancel)
		(u'cancel'                       , 'helptext'): _("Exit to main menu"),
		# (helptext of widget: create)
		(u'create'                       , 'helptext'): _("Create a new game"),
		# (helptext of widget: join)
		(u'join'                         , 'helptext'): _("Join the selected game"),
		# (helptext of widget: load)
		(u'load'                         , 'helptext'): _("Load a saved game"),
		# (helptext of widget: refresh)
		(u'refresh'                      , 'helptext'): _("Refresh list of active games"),
		},

	'set_password.xml' : {
		# (text of widget: headline_set_password)
		(u'headline_set_password'        , 'text'    ): _("Password of the game"),
		# (text of widget: password_lbl)
		(u'password_lbl'                 , 'text'    ): _("Enter password:"),
		},

	'set_player_details.xml' : {
		# (text of widget: headline_set_player_details)
		(u'headline_set_player_details'  , 'text'    ): _("Change player details"),
		},

	'settings.xml' : {
		# (text of widget: reset_mouse_sensitivity)
		(u'reset_mouse_sensitivity'      , 'text'    ): _("Reset to default"),
		# (text of widget: auto_unload_label)
		(u'auto_unload_label'            , 'text'    ): _("Auto-unload ship:"),
		# (text of widget: autosave_interval_label)
		(u'autosave_interval_label'      , 'text'    ): _("Autosave interval in minutes:"),
		# (text of widget: color_depth_label)
		(u'color_depth_label'            , 'text'    ): _("Color depth:"),
		# (text of widget: cursor_centered_zoom_label)
		(u'cursor_centered_zoom_label'   , 'text'    ): _("Cursor centered zoom:"),
		# (text of widget: debug_log_lbl)
		(u'debug_log_lbl'                , 'text'    ): _("Enable logging:"),
		# (text of widget: edge_scrolling_label)
		(u'edge_scrolling_label'         , 'text'    ): _("Scroll at map edge:"),
		# (text of widget: effect_volume_label)
		(u'effect_volume_label'          , 'text'    ): _("Effects volume:"),
		# (text of widget: fps_label)
		(u'fps_label'                    , 'text'    ): _("Frame rate limit:"),
		# (text of widget: headline_graphics)
		(u'headline_graphics'            , 'text'    ): _("Graphics"),
		# (text of widget: headline_language)
		(u'headline_language'            , 'text'    ): _("Language"),
		# (text of widget: headline_misc)
		(u'headline_misc'                , 'text'    ): _("General"),
		# (text of widget: headline_mouse)
		(u'headline_mouse'               , 'text'    ): _("Mouse"),
		# (text of widget: headline_network)
		(u'headline_network'             , 'text'    ): _("Network"),
		# (text of widget: headline_saving)
		(u'headline_saving'              , 'text'    ): _("Saving"),
		# (text of widget: headline_sound)
		(u'headline_sound'               , 'text'    ): _("Sound"),
		# (text of widget: middle_mouse_pan_lbl)
		(u'middle_mouse_pan_lbl'         , 'text'    ): _("Middle mouse button pan:"),
		# (text of widget: minimap_rotation_label)
		(u'minimap_rotation_label'       , 'text'    ): _("Rotate minimap with map:"),
		# (text of widget: mouse_sensitivity_label)
		(u'mouse_sensitivity_label'      , 'text'    ): _("Mouse sensitivity:"),
		# (text of widget: music_volume_label)
		(u'music_volume_label'           , 'text'    ): _("Music volume:"),
		# (text of widget: network_port_lbl)
		(u'network_port_lbl'             , 'text'    ): _("Network port:"),
		# (text of widget: number_of_autosaves_label)
		(u'number_of_autosaves_label'    , 'text'    ): _("Number of autosaves:"),
		# (text of widget: number_of_quicksaves_label)
		(u'number_of_quicksaves_label'   , 'text'    ): _("Number of quicksaves:"),
		# (text of widget: quote_type_label)
		(u'quote_type_label'             , 'text'    ): _("Choose a quote type:"),
		# (text of widget: screen_fullscreen_text)
		(u'screen_fullscreen_text'       , 'text'    ): _("Full screen:"),
		# (text of widget: screen_resolution_label)
		(u'screen_resolution_label'      , 'text'    ): _("Screen resolution:"),
		# (text of widget: scroll_speed_label)
		(u'scroll_speed_label'           , 'text'    ): _("Scroll delay:"),
		# (text of widget: show_resource_icons_lbl)
		(u'show_resource_icons_lbl'      , 'text'    ): _("Production indicators:"),
		# (text of widget: sound_enable_opt_text)
		(u'sound_enable_opt_text'        , 'text'    ): _("Enable sound:"),
		# (text of widget: uninterrupted_building_label)
		(u'uninterrupted_building_label' , 'text'    ): _("Uninterrupted building:"),
		# (text of widget: use_renderer_label)
		(u'use_renderer_label'           , 'text'    ): _("Used renderer:"),
		# (helptext of widget: cancelButton)
		(u'cancelButton'                 , 'helptext'): _("Discard current changes"),
		# (helptext of widget: defaultButton)
		(u'defaultButton'                , 'helptext'): _("Reset to default settings"),
		# (helptext of widget: okButton)
		(u'okButton'                     , 'helptext'): _("Apply"),
		# (helptext of widget: auto_unload_label)
		(u'auto_unload_label'            , 'helptext'): _("Whether to unload the ship after founding a settlement"),
		# (helptext of widget: color_depth_label)
		(u'color_depth_label'            , 'helptext'): _("If set to 0, use the driver default"),
		# (helptext of widget: cursor_centered_zoom_label)
		(u'cursor_centered_zoom_label'   , 'helptext'): _("When enabled, mouse wheel zoom will use the cursor position as new viewport center. When disabled, always zoom to current viewport center."),
		# (helptext of widget: debug_log_lbl)
		(u'debug_log_lbl'                , 'helptext'): _("Don't use in normal game session. Decides whether to write debug information in the logging directory of your user directory. Slows the game down."),
		# (helptext of widget: edge_scrolling_label)
		(u'edge_scrolling_label'         , 'helptext'): _("Whether to move the viewport when the mouse pointer is close to map edges"),
		# (helptext of widget: fps_label)
		(u'fps_label'                    , 'helptext'): _("Set the maximum frame rate used. Default: 60 fps."),
		# (helptext of widget: middle_mouse_pan_lbl)
		(u'middle_mouse_pan_lbl'         , 'helptext'): _("When enabled, dragging the middle mouse button will pan the camera"),
		# (helptext of widget: minimap_rotation_label)
		(u'minimap_rotation_label'       , 'helptext'): _("Whether to also rotate the minimap whenever the regular map is rotated"),
		# (helptext of widget: mouse_sensitivity_label)
		(u'mouse_sensitivity_label'      , 'helptext'): _("0 is default system settings"),
		# (helptext of widget: network_port_lbl)
		(u'network_port_lbl'             , 'helptext'): _("If set to 0, use the router default"),
		# (helptext of widget: quote_type_label)
		(u'quote_type_label'             , 'helptext'): _("What kind of quote to display while loading a game"),
		# (helptext of widget: scroll_speed_label)
		(u'scroll_speed_label'           , 'helptext'): _("Higher values slow down scrolling."),
		# (helptext of widget: show_resource_icons_lbl)
		(u'show_resource_icons_lbl'      , 'helptext'): _("Whether to show resource icons over buildings whenever they finish production"),
		# (helptext of widget: uninterrupted_building_label)
		(u'uninterrupted_building_label' , 'helptext'): _("When enabled, do not exit the build mode after successful construction"),
		# (helptext of widget: use_renderer_label)
		(u'use_renderer_label'           , 'helptext'): _("SDL is only meant as unsupported fallback and might cause problems!"),
		},

	'select_savegame.xml' : {
		# (text of widget: enter_filename_label)
		(u'enter_filename_label'         , 'text'    ): _("Enter filename:"),
		# (text of widget: gamename_lbl)
		(u'gamename_lbl'                 , 'text'    ): _("Name of the game:"),
		# (text of widget: gamepassword_lbl)
		(u'gamepassword_lbl'             , 'text'    ): _("Password of the game:"),
		# (text of widget: headline_details_label) More text describing the savegame
		(u'headline_details_label'       , 'text'    ): _("Details:"),
		# (text of widget: headline_saved_games_label)
		(u'headline_saved_games_label'   , 'text'    ): _("Your saved games:"),
		# (helptext of widget: cancelButton)
		(u'cancelButton'                 , 'helptext'): _("Cancel"),
		# (helptext of widget: deleteButton)
		(u'deleteButton'                 , 'helptext'): _("Delete selected savegame"),
		# (helptext of widget: gamename_lbl)
		(u'gamename_lbl'                 , 'helptext'): _("This will be displayed to other players so they recognize the game."),
		# (helptext of widget: gamepassword_lbl)
		(u'gamepassword_lbl'             , 'helptext'): _("Password of the game. Required to join this game"),
		},

	'singleplayermenu.xml' : {
		# (text of widget: headline)
		(u'headline'                     , 'text'    ): _("New game - Singleplayer"),
		# (text of widget: main_menu_label)
		(u'main_menu_label'              , 'text'    ): _("Main menu:"),
		# (text of widget: start_game_label)
		(u'start_game_label'             , 'text'    ): _("Start game:"),
		# (text of widget: free_maps)
		(u'free_maps'                    , 'text'    ): _("Free play"),
		# (text of widget: random)
		(u'random'                       , 'text'    ): _("Random map"),
		# (text of widget: scenario)
		(u'scenario'                     , 'text'    ): _("Scenario"),
		# (helptext of widget: cancel)
		(u'cancel'                       , 'helptext'): _("Exit to main menu"),
		# (helptext of widget: okay)
		(u'okay'                         , 'helptext'): _("Start game"),
		},

	'sp_free_maps.xml' : {
		# (text of widget: headline_choose_map_lbl)
		(u'headline_choose_map_lbl'      , 'text'    ): _("Choose a map to play:"),
		},

	'sp_random.xml' : {
		# (text of widget: headline_map_settings_lbl)
		(u'headline_map_settings_lbl'    , 'text'    ): _("Map settings:"),
		# (text of widget: seed_string_lbl)
		(u'seed_string_lbl'              , 'text'    ): _("Seed:"),
		},

	'sp_scenario.xml' : {
		# (text of widget: choose_map_lbl)
		(u'choose_map_lbl'               , 'text'    ): _("Choose a map to play:"),
		# (text of widget: select_lang_lbl)
		(u'select_lang_lbl'              , 'text'    ): _("Select a language:"),
		},

	'aidataselection.xml' : {
		# (text of widget: ai_players_label)
		(u'ai_players_label'             , 'text'    ): _("AI players:"),
		},

	'game_settings.xml' : {
		# (text of widget: headline_game_settings_lbl)
		(u'headline_game_settings_lbl'   , 'text'    ): _("Game settings:"),
		# (text of widget: lbl_disasters) Whether there should be disasters in the game.
		(u'lbl_disasters'                , 'text'    ): _("Disasters"),
		# (text of widget: lbl_free_trader) Whether to create this kind of player in the game.
		(u'lbl_free_trader'              , 'text'    ): _("Free Trader"),
		# (text of widget: lbl_pirates) Whether to create this kind of player in the game.
		(u'lbl_pirates'                  , 'text'    ): _("Pirates"),
		},

	'playerdataselection.xml' : {
		# (text of widget: color_label)
		(u'color_label'                  , 'text'    ): _("Color:"),
		# (text of widget: player_label)
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
