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
        (u'help'                         , 'text'    ): _(u"Help"),
        (u'loadgame'                     , 'text'    ): _(u"Load map"),
        (u'quit'                         , 'text'    ): _(u"Exit editor"),
        (u'savegame'                     , 'text'    ): _(u"Save map"),
        (u'settings'                     , 'text'    ): _(u"Settings"),
        (u'start'                        , 'text'    ): _(u"Return to editor"),
        },

    'editor_settings.xml' : {
        (u'cursor_hint'                  , 'text'    ): _(u"(right click to stop)"),
        (u'headline_brush_size'          , 'text'    ): _(u"Select brush size:"),
        (u'headline_terrain'             , 'text'    ): _(u"Select terrain:"),
        },

    'buildtab.xml' : {
        },

    'buildtab_no_settlement.xml' : {
        (u'headline'                     , 'text'    ): _(u"Game start"),
        (u'howto_1_need_warehouse'       , 'text'    ): _(u"You need to found a settlement before you can construct buildings!"),
        (u'howto_2_navigate_ship'        , 'text'    ): _(u"Select your ship and approach the coast via right-click."),
        (u'howto_3_build_warehouse'      , 'text'    ): _(u"Afterwards, press the large button in the ship overview tab."),
        },

    'place_building.xml' : {
        (u'headline'                     , 'text'    ): _(u"Build"),
        (u'running_costs_label'          , 'text'    ): _(u"Running costs:"),
        },

    'related_buildings.xml' : {
        (u'headline'                     , 'text'    ): _(u"Related buildings"),
        },

    'city_info.xml' : {
        (u'city_info_inhabitants'        , 'helptext'): _(u"Inhabitants"),
        },

    'messagewidget_icon.xml' : {
        },

    'messagewidget_message.xml' : {
        },

    'minimap.xml' : {
        (u'build'                        , 'helptext'): _(u"Build menu ({key})"),
        (u'destroy_tool'                 , 'helptext'): _(u"Destroy ({key})"),
        (u'diplomacyButton'              , 'helptext'): _(u"Diplomacy"),
        (u'gameMenuButton'               , 'helptext'): _(u"Game menu ({key})"),
        (u'logbook'                      , 'helptext'): _(u"Captain's log ({key})"),
        (u'rotateLeft'                   , 'helptext'): _(u"Rotate map counterclockwise ({key})"),
        (u'rotateRight'                  , 'helptext'): _(u"Rotate map clockwise ({key})"),
        (u'speedDown'                    , 'helptext'): _(u"Decrease game speed ({key})"),
        (u'speedUp'                      , 'helptext'): _(u"Increase game speed ({key})"),
        (u'zoomIn'                       , 'helptext'): _(u"Zoom in"),
        (u'zoomOut'                      , 'helptext'): _(u"Zoom out"),
        },

    'resource_overview_bar_entry.xml' : {
        },

    'resource_overview_bar_gold.xml' : {
        },

    'resource_overview_bar_stats.xml' : {
        },

    'change_name.xml' : {
        (u'enter_new_name_lbl'           , 'text'    ): _(u"Enter new name:"),
        (u'headline_change_name'         , 'text'    ): _(u"Change name"),
        (u'old_name_label'               , 'text'    ): _(u"Old name:"),
        (u'okButton'                     , 'helptext'): _(u"Apply the new name"),
        },

    'chat.xml' : {
        (u'chat_lbl'                     , 'text'    ): _(u"Enter your message:"),
        (u'headline'                     , 'text'    ): _(u"Chat"),
        },

    'boatbuilder.xml' : {
        (u'UB_cancel_build_label'        , 'text'    ): _(u"Cancel building:"),
        (u'UB_cancel_warning_label'      , 'text'    ): _(u"(lose all resources)"),
        (u'UB_current_order'             , 'text'    ): _(u"Currently building:"),
        (u'UB_howto_build_lbl'           , 'text'    ): _(u"To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
        (u'UB_needed_res_label'          , 'text'    ): _(u"Resources still needed:"),
        (u'UB_progress_label'            , 'text'    ): _(u"Construction progress:"),
        (u'UB_cancel_button'             , 'helptext'): _(u"Cancel all building progress"),
        (u'running_costs_label'          , 'helptext'): _(u"Running costs"),
        (u'toggle_active_active'         , 'helptext'): _(u"Pause"),
        (u'toggle_active_inactive'       , 'helptext'): _(u"Resume"),
        },

    'boatbuilder_showcase.xml' : {
        },

    'diplomacy.xml' : {
        (u'ally_label'                   , 'text'    ): _(u"ally"),
        (u'enemy_label'                  , 'text'    ): _(u"enemy"),
        (u'neutral_label'                , 'text'    ): _(u"neutral"),
        },

    'overview_farm.xml' : {
        (u'headline'                     , 'text'    ): _(u"Building overview"),
        (u'capacity_utilization_label'   , 'helptext'): _(u"Capacity utilization"),
        (u'running_costs_label'          , 'helptext'): _(u"Running costs"),
        (u'capacity_utilization'         , 'helptext'): _(u"Capacity utilization"),
        (u'running_costs'                , 'helptext'): _(u"Running costs"),
        },

    'overview_war_groundunit.xml' : {
        },

    'island_inventory.xml' : {
        (u'headline'                     , 'text'    ): _(u"Settlement inventory"),
        },

    'mainsquare_inhabitants.xml' : {
        (u'headline'                     , 'text'    ): _(u"Settler overview"),
        (u'headline_happiness_per_house' , 'text'    ): _(u"Happiness per house"),
        (u'headline_residents_per_house' , 'text'    ): _(u"Residents per house"),
        (u'headline_residents_total'     , 'text'    ): _(u"Summary"),
        (u'houses'                       , 'text'    ): _(u"houses"),
        (u'residents'                    , 'text'    ): _(u"residents"),
        (u'tax_label'                    , 'text'    ): _(u"Taxes:"),
        (u'upgrades_lbl'                 , 'text'    ): _(u"Upgrade permissions:"),
        (u'avg_icon'                     , 'helptext'): _(u"satisfied"),
        (u'happiness_house_icon'         , 'helptext'): _(u"Amount of houses with this happiness"),
        (u'happy_icon'                   , 'helptext'): _(u"happy"),
        (u'houses_icon'                  , 'helptext'): _(u"Houses with this amount of inhabitants"),
        (u'inhabitants_icon'             , 'helptext'): _(u"Number of inhabitants per house"),
        (u'paid_taxes_icon'              , 'helptext'): _(u"Paid taxes"),
        (u'sad_icon'                     , 'helptext'): _(u"sad"),
        (u'tax_rate_icon'                , 'helptext'): _(u"Tax rate"),
        (u'tax_val_label'                , 'helptext'): _(u"Tax rate"),
        (u'taxes'                        , 'helptext'): _(u"Paid taxes"),
        },

    'overview_enemybuilding.xml' : {
        },

    'overview_enemyunit.xml' : {
        },

    'overview_enemywarehouse.xml' : {
        (u'buying_label'                 , 'text'    ): _(u"Buying"),
        (u'selling_label'                , 'text'    ): _(u"Selling"),
        },

    'overview_generic.xml' : {
        (u'headline'                     , 'text'    ): _(u"Building overview"),
        (u'name_label'                   , 'text'    ): _(u"Name:"),
        (u'running_costs_label'          , 'helptext'): _(u"Running costs"),
        (u'running_costs'                , 'helptext'): _(u"Running costs"),
        },

    'overview_groundunit.xml' : {
        (u'lbl_weapon_storage'           , 'text'    ): _(u"Weapons:"),
        },

    'overview_productionbuilding.xml' : {
        (u'capacity_utilization_label'   , 'helptext'): _(u"Capacity utilization"),
        (u'running_costs_label'          , 'helptext'): _(u"Running costs"),
        (u'capacity_utilization'         , 'helptext'): _(u"Capacity utilization"),
        (u'running_costs'                , 'helptext'): _(u"Running costs"),
        },

    'overview_resourcedeposit.xml' : {
        (u'headline'                     , 'text'    ): _(u"Resource deposit"),
        (u'res_dep_description_lbl'      , 'text'    ): _(u"This is a resource deposit where you can build a mine to dig up resources."),
        (u'res_dep_description_lbl2'     , 'text'    ): _(u"It contains these resources:"),
        },

    'overview_settler.xml' : {
        (u'needed_res_label'             , 'text'    ): _(u"Needed resources:"),
        (u'tax_label'                    , 'text'    ): _(u"Taxes:"),
        (u'happiness_label'              , 'helptext'): _(u"Happiness"),
        (u'paid_taxes_label'             , 'helptext'): _(u"Paid taxes"),
        (u'paid_taxes_label'             , 'helptext'): _(u"Tax rate"),
        (u'residents_label'              , 'helptext'): _(u"Residents"),
        (u'inhabitants'                  , 'helptext'): _(u"Residents"),
        (u'tax_val_label'                , 'helptext'): _(u"Tax rate"),
        (u'taxes'                        , 'helptext'): _(u"Paid taxes"),
        (u'happiness'                    , 'helptext'): _(u"Happiness"),
        },

    'overview_signalfire.xml' : {
        (u'signal_fire_description_lbl'  , 'text'    ): _(u"The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods."),
        },

    'overview_tower.xml' : {
        (u'name_label'                   , 'text'    ): _(u"Name:"),
        (u'running_costs_label'          , 'helptext'): _(u"Running costs"),
        (u'running_costs'                , 'helptext'): _(u"Running costs"),
        },

    'overview_tradership.xml' : {
        (u'trader_description_lbl'       , 'text'    ): _(u"This is the free trader's ship. It will visit you from time to time to buy or sell goods."),
        },

    'overviewtab.xml' : {
        },

    'overview_select_multi.xml' : {
        },

    'unit_entry_widget.xml' : {
        },

    'overview_ship.xml' : {
        (u'configure_route'              , 'helptext'): _(u"Configure trading route"),
        (u'found_settlement'             , 'helptext'): _(u"Build settlement"),
        (u'trade'                        , 'helptext'): _(u"Trade"),
        },

    'overview_trade_ship.xml' : {
        (u'configure_route'              , 'helptext'): _(u"Configure trading route"),
        (u'discard_res'                  , 'helptext'): _(u"Discard all resources"),
        (u'found_settlement'             , 'helptext'): _(u"Build settlement"),
        (u'trade'                        , 'helptext'): _(u"Trade"),
        },

    'overview_war_ship.xml' : {
        (u'configure_route'              , 'helptext'): _(u"Configure trading route"),
        (u'found_settlement'             , 'helptext'): _(u"Build settlement"),
        (u'trade'                        , 'helptext'): _(u"Trade"),
        },

    'tradetab.xml' : {
        (u'buying_label'                 , 'text'    ): _(u"Buying"),
        (u'exchange_label'               , 'text'    ): _(u"Exchange:"),
        (u'headline'                     , 'text'    ): _(u"Trade"),
        (u'selling_label'                , 'text'    ): _(u"Selling"),
        (u'ship_label'                   , 'text'    ): _(u"Ship:"),
        (u'trade_with_label'             , 'text'    ): _(u"Trade partner:"),
        },

    'tab_base.xml' : {
        },

    'buysellmenu.xml' : {
        (u'headline'                     , 'text'    ): _(u"Buy or sell resources"),
        (u'headline_trade_history'       , 'text'    ): _(u"Trade history"),
        },

    'select_trade_resource.xml' : {
        (u'headline'                     , 'text'    ): _(u"Select resources:"),
        },

    'tab_account.xml' : {
        (u'buy_expenses_label'           , 'text'    ): _(u"Buying"),
        (u'headline_balance_label'       , 'text'    ): _(u"Balance:"),
        (u'headline_expenses_label'      , 'text'    ): _(u"Expenses:"),
        (u'headline_income_label'        , 'text'    ): _(u"Income:"),
        (u'running_costs_label'          , 'text'    ): _(u"Running costs"),
        (u'sell_income_label'            , 'text'    ): _(u"Sale"),
        (u'taxes_label'                  , 'text'    ): _(u"Taxes"),
        (u'collector_utilization_label'  , 'helptext'): _(u"Collector utilization"),
        (u'show_production_overview'     , 'helptext'): _(u"Show resources produced in this settlement"),
        (u'collector_utilization'        , 'helptext'): _(u"Collector utilization"),
        },

    'trade_single_slot.xml' : {
        },

    'overview_farmproductionline.xml' : {
        (u'toggle_active_active'         , 'helptext'): _(u"Pause production"),
        (u'toggle_active_inactive'       , 'helptext'): _(u"Start production"),
        },

    'overview_productionline.xml' : {
        (u'toggle_active_active'         , 'helptext'): _(u"Pause production"),
        (u'toggle_active_inactive'       , 'helptext'): _(u"Start production"),
        },

    'related_buildings_container.xml' : {
        },

    'resbar_resource_selection.xml' : {
        (u'headline'                     , 'text'    ): _(u"Select resource:"),
        (u'make_default_btn'             , 'helptext'): _(u"Save current resource configuration as default for all settlements."),
        (u'reset_default_btn'            , 'helptext'): _(u"Reset default resource configuration for all settlements."),
        (u'headline'                     , 'helptext'): _(u"The resource you select is displayed instead of the current one. Empty by clicking on X."),
        },

    'route_entry.xml' : {
        (u'delete_warehouse'             , 'helptext'): _(u"Delete entry"),
        (u'move_down'                    , 'helptext'): _(u"Move down"),
        (u'move_up'                      , 'helptext'): _(u"Move up"),
        },

    'trade_history_item.xml' : {
        },

    'traderoute_resource_selection.xml' : {
        (u'select_res_label'             , 'text'    ): _(u"Select a resource:"),
        },

    'captains_log.xml' : {
        (u'stats_players'                , 'text'    ): _(u"Players"),
        (u'stats_settlements'            , 'text'    ): _(u"My settlements"),
        (u'stats_ships'                  , 'text'    ): _(u"My ships"),
        (u'weird_button_1'               , 'text'    ): _(u"Whole world"),
        (u'weird_button_4'               , 'text'    ): _(u"Everybody"),
        (u'headline_chat'                , 'text'    ): _(u"Chat"),
        (u'headline_game_messages'       , 'text'    ): _(u"Game messages"),
        (u'headline_statistics'          , 'text'    ): _(u"Statistics"),
        (u'okButton'                     , 'helptext'): _(u"Return to game"),
        (u'weird_button_4'               , 'helptext'): _(u"Sends the chat messages to all players."),
        (u'backwardButton'               , 'helptext'): _(u"Read previous entries"),
        (u'forwardButton'                , 'helptext'): _(u"Read next entries"),
        },

    'configure_route.xml' : {
        (u'lbl_route_activity'           , 'text'    ): _(u"Route activity:"),
        (u'lbl_wait_at_load'             , 'text'    ): _(u"Wait at load:"),
        (u'lbl_wait_at_unload'           , 'text'    ): _(u"Wait at unload:"),
        (u'okButton'                     , 'helptext'): _(u"Exit"),
        (u'start_route'                  , 'helptext'): _(u"Start route"),
        },

    'healthwidget.xml' : {
        },

    'island_production.xml' : {
        (u'okButton'                     , 'helptext'): _(u"Close"),
        },

    'players_overview.xml' : {
        (u'building_score'               , 'text'    ): _(u"Buildings"),
        (u'headline'                     , 'text'    ): _(u"Player scores"),
        (u'land_score'                   , 'text'    ): _(u"Land"),
        (u'money_score'                  , 'text'    ): _(u"Money"),
        (u'player_name'                  , 'text'    ): _(u"Name"),
        (u'resource_score'               , 'text'    ): _(u"Resources"),
        (u'settler_score'                , 'text'    ): _(u"Settlers"),
        (u'total_score'                  , 'text'    ): _(u"Total"),
        (u'unit_score'                   , 'text'    ): _(u"Units"),
        (u'building_score'               , 'helptext'): _(u"Value of all the buildings in the player's settlement(s)"),
        (u'land_score'                   , 'helptext'): _(u"Value of usable land i.e Amount of Land that can be used to create buildings "),
        (u'money_score'                  , 'helptext'): _(u"Player's current treasury + income expected in near future"),
        (u'player_name'                  , 'helptext'): _(u"Player Name"),
        (u'resource_score'               , 'helptext'): _(u"Value of resources generated from all the possible sources in the player's settlement(s)"),
        (u'settler_score'                , 'helptext'): _(u"Value denoting the progress of the settlement(s) in terms of inhabitants, buildings and overall happiness"),
        (u'total_score'                  , 'helptext'): _(u"The total value from all individual entities or in short : Total Player Score"),
        (u'unit_score'                   , 'helptext'): _(u"Value of all the units owned by the player"),
        },

    'players_settlements.xml' : {
        (u'balance'                      , 'text'    ): _(u"Balance"),
        (u'inhabitants'                  , 'text'    ): _(u"Inhabitants"),
        (u'running_costs'                , 'text'    ): _(u"Running costs"),
        (u'settlement_name'              , 'text'    ): _(u"Name"),
        (u'taxes'                        , 'text'    ): _(u"Taxes"),
        },

    'ships_list.xml' : {
        (u'health'                       , 'text'    ): _(u"Health"),
        (u'ship_name'                    , 'text'    ): _(u"Name"),
        (u'ship_type'                    , 'text'    ): _(u"Type"),
        (u'status'                       , 'text'    ): _(u"Status"),
        (u'weapons'                      , 'text'    ): _(u"Weapons"),
        },

    'stancewidget.xml' : {
        (u'aggressive_stance'            , 'helptext'): _(u"Aggressive"),
        (u'flee_stance'                  , 'helptext'): _(u"Flee"),
        (u'hold_ground_stance'           , 'helptext'): _(u"Hold ground"),
        (u'none_stance'                  , 'helptext'): _(u"Passive"),
        },

    'credits.xml' : {
        },

    'editor_create_map.xml' : {
        (u'headline_choose_map_size_lbl' , 'text'    ): _(u"Choose a map size:"),
        },

    'editor_select_map.xml' : {
        (u'headline_choose_map_lbl'      , 'text'    ): _(u"Choose a map:"),
        },

    'editor_select_saved_game.xml' : {
        (u'headline_choose_saved_game'   , 'text'    ): _(u"Choose a saved game's map:"),
        },

    'editor_start_menu.xml' : {
        (u'headline'                     , 'text'    ): _(u"Select map source"),
        (u'create_new_map'               , 'text'    ): _(u"Create new map"),
        (u'load_existing_map'            , 'text'    ): _(u"Load existing map"),
        (u'load_saved_game_map'          , 'text'    ): _(u"Load saved game's map"),
        (u'cancel'                       , 'helptext'): _(u"Exit to main menu"),
        (u'okay'                         , 'helptext'): _(u"Start editor"),
        },

    'help.xml' : {
        (u'okButton'                     , 'helptext'): _(u"Return"),
        },

    'hotkeys.xml' : {
        (u'reset_to_default'             , 'text'    ): _(u"Reset to default keys"),
        (u'labels_headline'              , 'text'    ): _(u"Actions"),
        (u'primary_buttons_headline'     , 'text'    ): _(u"Primary"),
        (u'secondary_buttons_headline'   , 'text'    ): _(u"Secondary"),
        (u'okButton'                     , 'helptext'): _(u"Exit to main menu"),
        (u'reset_to_default'             , 'helptext'): _(u"Reset to default"),
        (u'lbl_BUILD_TOOL'               , 'helptext'): _(u"Show build menu"),
        (u'lbl_CHAT'                     , 'helptext'): _(u"Chat"),
        (u'lbl_CONSOLE'                  , 'helptext'): _(u"Toggle showing FPS on/off"),
        (u'lbl_COORD_TOOLTIP'            , 'helptext'): _(u"Show coordinate values (Debug)"),
        (u'lbl_DESTROY_TOOL'             , 'helptext'): _(u"Enable destruct mode"),
        (u'lbl_DOWN'                     , 'helptext'): _(u"Scroll down"),
        (u'lbl_GRID'                     , 'helptext'): _(u"Toggle grid on/off"),
        (u'lbl_HEALTH_BAR'               , 'helptext'): _(u"Toggle health bars"),
        (u'lbl_HELP'                     , 'helptext'): _(u"Display help"),
        (u'lbl_LEFT'                     , 'helptext'): _(u"Scroll left"),
        (u'lbl_LOGBOOK'                  , 'helptext'): _(u"Toggle Captain's log"),
        (u'lbl_PAUSE'                    , 'helptext'): _(u"Pause game"),
        (u'lbl_PIPETTE'                  , 'helptext'): _(u"Enable pipette mode (clone buildings)"),
        (u'lbl_PLAYERS_OVERVIEW'         , 'helptext'): _(u"Show player scores"),
        (u'lbl_QUICKLOAD'                , 'helptext'): _(u"Quickload"),
        (u'lbl_QUICKSAVE'                , 'helptext'): _(u"Quicksave"),
        (u'lbl_REMOVE_SELECTED'          , 'helptext'): _(u"Remove selected units / buildings"),
        (u'lbl_RIGHT'                    , 'helptext'): _(u"Scroll right"),
        (u'lbl_ROAD_TOOL'                , 'helptext'): _(u"Enable road building mode"),
        (u'lbl_ROTATE_LEFT'              , 'helptext'): _(u"Rotate building or map counterclockwise"),
        (u'lbl_ROTATE_RIGHT'             , 'helptext'): _(u"Rotate building or map clockwise"),
        (u'lbl_SCREENSHOT'               , 'helptext'): _(u"Screenshot"),
        (u'lbl_SETTLEMENTS_OVERVIEW'     , 'helptext'): _(u"Show settlement list"),
        (u'lbl_SHIPS_OVERVIEW'           , 'helptext'): _(u"Show ship list"),
        (u'lbl_SHOW_SELECTED'            , 'helptext'): _(u"Focus camera on selection"),
        (u'lbl_SPEED_DOWN'               , 'helptext'): _(u"Decrease game speed"),
        (u'lbl_SPEED_UP'                 , 'helptext'): _(u"Increase game speed"),
        (u'lbl_TILE_OWNER_HIGHLIGHT'     , 'helptext'): _(u"Highlight tile ownership"),
        (u'lbl_TRANSLUCENCY'             , 'helptext'): _(u"Toggle translucency of ambient buildings"),
        (u'lbl_UP'                       , 'helptext'): _(u"Scroll up"),
        (u'lbl_ZOOM_IN'                  , 'helptext'): _(u"Zoom in"),
        (u'lbl_ZOOM_OUT'                 , 'helptext'): _(u"Zoom out"),
        },

    'ingamemenu.xml' : {
        (u'help'                         , 'text'    ): _(u"Help"),
        (u'loadgame'                     , 'text'    ): _(u"Load game"),
        (u'quit'                         , 'text'    ): _(u"Cancel game"),
        (u'savegame'                     , 'text'    ): _(u"Save game"),
        (u'settings'                     , 'text'    ): _(u"Settings"),
        (u'start'                        , 'text'    ): _(u"Return to game"),
        },

    'loadingscreen.xml' : {
        (u'loading_label'                , 'text'    ): _(u"Loading…"),
        },

    'mainmenu.xml' : {
        (u'credits_label'                , 'text'    ): _(u"Credits"),
        (u'editor_label'                 , 'text'    ): _(u"Editor"),
        (u'help_label'                   , 'text'    ): _(u"Help"),
        (u'load_label'                   , 'text'    ): _(u"Load game"),
        (u'multi_label'                  , 'text'    ): _(u"Multiplayer"),
        (u'quit_label'                   , 'text'    ): _(u"Quit"),
        (u'settings_label'               , 'text'    ): _(u"Settings"),
        (u'single_label'                 , 'text'    ): _(u"Singleplayer"),
        (u'version_label'                , 'text'    ): VERSION.string(),
        },

    'multiplayer_creategame.xml' : {
        (u'gamename_lbl'                 , 'text'    ): _(u"Name of the game:"),
        (u'headline'                     , 'text'    ): _(u"Choose a map:"),
        (u'headline'                     , 'text'    ): _(u"Create game - Multiplayer"),
        (u'mp_player_limit_lbl'          , 'text'    ): _(u"Player limit:"),
        (u'password_lbl'                 , 'text'    ): _(u"Password of the game:"),
        (u'cancel'                       , 'helptext'): _(u"Exit to multiplayer menu"),
        (u'create'                       , 'helptext'): _(u"Create this new game"),
        (u'gamename_lbl'                 , 'helptext'): _(u"This will be displayed to other players so they recognize the game."),
        (u'password_lbl'                 , 'helptext'): _(u"This game's password. Required to join this game."),
        },

    'multiplayer_gamelobby.xml' : {
        (u'game_player_color'            , 'text'    ): _(u"Color"),
        (u'game_player_status'           , 'text'    ): _(u"Status"),
        (u'game_start_notice'            , 'text'    ): _(u"The game will start as soon as all players are ready."),
        (u'headline'                     , 'text'    ): _(u"Chat:"),
        (u'headline'                     , 'text'    ): _(u"Gamelobby"),
        (u'ready_lbl'                    , 'text'    ): _(u"Ready:"),
        (u'startmessage'                 , 'text'    ): _(u"Game details:"),
        (u'cancel'                       , 'helptext'): _(u"Exit gamelobby"),
        (u'ready_btn'                    , 'helptext'): _(u"Sets your state to ready (necessary for the game to start)"),
        },

    'multiplayermenu.xml' : {
        (u'create_game_lbl'              , 'text'    ): _(u"Create game:"),
        (u'headline_active_games_lbl'    , 'text'    ): _(u"Active games:"),
        (u'headline_left'                , 'text'    ): _(u"New game - Multiplayer"),
        (u'join_game_lbl'                , 'text'    ): _(u"Join game:"),
        (u'load_game_lbl'                , 'text'    ): _(u"Load game:"),
        (u'refr_gamelist_lbl'            , 'text'    ): _(u"Refresh list:"),
        (u'cancel'                       , 'helptext'): _(u"Exit to main menu"),
        (u'create'                       , 'helptext'): _(u"Create a new game"),
        (u'join'                         , 'helptext'): _(u"Join the selected game"),
        (u'load'                         , 'helptext'): _(u"Load a saved game"),
        (u'refresh'                      , 'helptext'): _(u"Refresh list of active games"),
        },

    'set_player_details.xml' : {
        (u'headline_set_player_details'  , 'text'    ): _(u"Change player details"),
        },

    'settings.xml' : {
        (u'auto_unload_label'            , 'text'    ): _(u"Auto-unload ship:"),
        (u'autosave_interval_label'      , 'text'    ): _(u"Autosave interval in minutes:"),
        (u'cursor_centered_zoom_label'   , 'text'    ): _(u"Cursor centered zoom:"),
        (u'debug_log_lbl'                , 'text'    ): _(u"Enable logging:"),
        (u'edge_scrolling_label'         , 'text'    ): _(u"Scroll at map edge:"),
        (u'effect_volume_label'          , 'text'    ): _(u"Effects volume:"),
        (u'fps_label'                    , 'text'    ): _(u"Frame rate limit:"),
        (u'headline_graphics'            , 'text'    ): _(u"Graphics"),
        (u'headline_language'            , 'text'    ): _(u"Language"),
        (u'headline_misc'                , 'text'    ): _(u"General"),
        (u'headline_mouse'               , 'text'    ): _(u"Mouse"),
        (u'headline_network'             , 'text'    ): _(u"Network"),
        (u'headline_saving'              , 'text'    ): _(u"Saving"),
        (u'headline_sound'               , 'text'    ): _(u"Sound"),
        (u'middle_mouse_pan_lbl'         , 'text'    ): _(u"Middle mouse button pan:"),
        (u'minimap_rotation_label'       , 'text'    ): _(u"Rotate minimap with map:"),
        (u'mouse_sensitivity_label'      , 'text'    ): _(u"Mouse sensitivity:"),
        (u'music_volume_label'           , 'text'    ): _(u"Music volume:"),
        (u'network_port_lbl'             , 'text'    ): _(u"Network port:"),
        (u'number_of_autosaves_label'    , 'text'    ): _(u"Number of autosaves:"),
        (u'number_of_quicksaves_label'   , 'text'    ): _(u"Number of quicksaves:"),
        (u'quote_type_label'             , 'text'    ): _(u"Choose a quote type:"),
        (u'screen_fullscreen_text'       , 'text'    ): _(u"Full screen:"),
        (u'screen_resolution_label'      , 'text'    ): _(u"Screen resolution:"),
        (u'scroll_speed_label'           , 'text'    ): _(u"Scroll delay:"),
        (u'show_resource_icons_lbl'      , 'text'    ): _(u"Production indicators:"),
        (u'sound_enable_opt_text'        , 'text'    ): _(u"Enable sound:"),
        (u'uninterrupted_building_label' , 'text'    ): _(u"Uninterrupted building:"),
        (u'cancelButton'                 , 'helptext'): _(u"Discard current changes"),
        (u'defaultButton'                , 'helptext'): _(u"Reset to default settings"),
        (u'okButton'                     , 'helptext'): _(u"Save changes"),
        (u'auto_unload_label'            , 'helptext'): _(u"Whether to unload the ship after founding a settlement"),
        (u'cursor_centered_zoom_label'   , 'helptext'): _(u"When enabled, mouse wheel zoom will use the cursor position as new viewport center. When disabled, always zoom to current viewport center."),
        (u'debug_log_lbl'                , 'helptext'): _(u"Don't use in normal game session. Decides whether to write debug information in the logging directory of your user directory. Slows the game down."),
        (u'edge_scrolling_label'         , 'helptext'): _(u"Whether to move the viewport when the mouse pointer is close to map edges"),
        (u'fps_label'                    , 'helptext'): _(u"Set the maximum frame rate used. Default: 60 fps."),
        (u'middle_mouse_pan_lbl'         , 'helptext'): _(u"When enabled, dragging the middle mouse button will pan the camera"),
        (u'minimap_rotation_label'       , 'helptext'): _(u"Whether to also rotate the minimap whenever the regular map is rotated"),
        (u'mouse_sensitivity_label'      , 'helptext'): _(u"0 is default system settings"),
        (u'network_port_lbl'             , 'helptext'): _(u"If set to 0, use the router default"),
        (u'quote_type_label'             , 'helptext'): _(u"What kind of quote to display while loading a game"),
        (u'scroll_speed_label'           , 'helptext'): _(u"Higher values slow down scrolling."),
        (u'show_resource_icons_lbl'      , 'helptext'): _(u"Whether to show resource icons over buildings whenever they finish production"),
        (u'uninterrupted_building_label' , 'helptext'): _(u"When enabled, do not exit the build mode after successful construction"),
        },

    'select_savegame.xml' : {
        (u'enter_filename_label'         , 'text'    ): _(u"Enter filename:"),
        (u'gamename_lbl'                 , 'text'    ): _(u"Name of the game:"),
        (u'gamepassword_lbl'             , 'text'    ): _(u"Password of the game:"),
        (u'headline_details_label'       , 'text'    ): _(u"Details:"),
        (u'headline_saved_games_label'   , 'text'    ): _(u"Your saved games:"),
        (u'cancelButton'                 , 'helptext'): _(u"Cancel"),
        (u'deleteButton'                 , 'helptext'): _(u"Delete selected savegame"),
        (u'gamename_lbl'                 , 'helptext'): _(u"This will be displayed to other players so they recognize the game."),
        (u'gamepassword_lbl'             , 'helptext'): _(u"Password of the game. Required to join this game"),
        },

    'singleplayermenu.xml' : {
        (u'headline'                     , 'text'    ): _(u"New game - Singleplayer"),
        (u'free_maps'                    , 'text'    ): _(u"Free play"),
        (u'random'                       , 'text'    ): _(u"Random map"),
        (u'scenario'                     , 'text'    ): _(u"Scenario"),
        (u'cancel'                       , 'helptext'): _(u"Exit to main menu"),
        (u'okay'                         , 'helptext'): _(u"Start game"),
        },

    'sp_free_maps.xml' : {
        (u'headline_choose_map_lbl'      , 'text'    ): _(u"Choose a map to play:"),
        },

    'sp_random.xml' : {
        (u'headline_map_settings_lbl'    , 'text'    ): _(u"Map settings:"),
        (u'seed_string_lbl'              , 'text'    ): _(u"Seed:"),
        },

    'sp_scenario.xml' : {
        (u'choose_map_lbl'               , 'text'    ): _(u"Choose a map to play:"),
        (u'select_lang_lbl'              , 'text'    ): _(u"Select a language:"),
        },

    'aidataselection.xml' : {
        (u'ai_players_label'             , 'text'    ): _(u"AI players:"),
        },

    'game_settings.xml' : {
        (u'headline_game_settings_lbl'   , 'text'    ): _(u"Game settings:"),
        (u'lbl_disasters'                , 'text'    ): _(u"Disasters"),
        (u'lbl_free_trader'              , 'text'    ): _(u"Free Trader"),
        (u'lbl_pirates'                  , 'text'    ): _(u"Pirates"),
        },

    'playerdataselection.xml' : {
        (u'color_label'                  , 'text'    ): _(u"Color:"),
        (u'player_label'                 , 'text'    ): _(u"Player name:"),
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
