# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

text_translations = dict()

def set_translations():
	global text_translations
	text_translations = {

	"stringpreviewwidget.xml" : {
		},

	"buildtab.xml" : {
		},

	"buildtab_no_settlement.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Game start"),
		# (text of widget: howto_1_need_warehouse)
		("howto_1_need_warehouse"      , "text"    ): _("You need to found a settlement before you can construct buildings!"),
		# (text of widget: howto_2_navigate_ship)
		("howto_2_navigate_ship"       , "text"    ): _("Select your ship and approach the coast via right-click."),
		# (text of widget: howto_3_build_warehouse)
		("howto_3_build_warehouse"     , "text"    ): _("Afterwards, press the large button in the ship overview tab."),
		},

	"place_building.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Build"),
		# (text of widget: running_costs_label)
		("running_costs_label"         , "text"    ): _("Running costs:"),
		},

	"city_info.xml" : {
		# (helptext of widget: city_info_inhabitants)
		("city_info_inhabitants"       , "helptext"): _("Inhabitants"),
		},

	"messagewidget_icon.xml" : {
		},

	"messagewidget_message.xml" : {
		},

	"minimap.xml" : {
		# (helptext of widget: build)
		("build"                       , "helptext"): _("Build menu (B)"),
		# (helptext of widget: destroy_tool)
		("destroy_tool"                , "helptext"): _("Destroy (X)"),
		# (helptext of widget: diplomacyButton)
		("diplomacyButton"             , "helptext"): _("Diplomacy"),
		# (helptext of widget: gameMenuButton)
		("gameMenuButton"              , "helptext"): _("Game menu (Esc)"),
		# (helptext of widget: logbook)
		("logbook"                     , "helptext"): _("Captain's log (L)"),
		# (helptext of widget: rotateLeft)
		("rotateLeft"                  , "helptext"): _("Rotate map counterclockwise (,)"),
		# (helptext of widget: rotateRight)
		("rotateRight"                 , "helptext"): _("Rotate map clockwise (.)"),
		# (helptext of widget: speedDown)
		("speedDown"                   , "helptext"): _("Decrease game speed (-)"),
		# (helptext of widget: speedUp)
		("speedUp"                     , "helptext"): _("Increase game speed (+)"),
		# (helptext of widget: zoomIn)
		("zoomIn"                      , "helptext"): _("Zoom in"),
		# (helptext of widget: zoomOut)
		("zoomOut"                     , "helptext"): _("Zoom out"),
		},

	"resource_overview_bar_entry.xml" : {
		},

	"resource_overview_bar_gold.xml" : {
		},

	"change_name.xml" : {
		# (text of widget: enter_new_name_lbl)
		("enter_new_name_lbl"          , "text"    ): _("Enter new name:"),
		# (text of widget: headline_change_name)
		("headline_change_name"        , "text"    ): _("Change name"),
		# (text of widget: old_name_label)
		("old_name_label"              , "text"    ): _("Old name:"),
		# (helptext of widget: okButton)
		("okButton"                    , "helptext"): _("Apply the new name"),
		},

	"chat.xml" : {
		# (text of widget: chat_lbl)
		("chat_lbl"                    , "text"    ): _("Enter your message:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Chat"),
		},

	"save_map.xml" : {
		# (text of widget: enter_new_name_lbl)
		("enter_new_name_lbl"          , "text"    ): _("Enter prefix:"),
		# (text of widget: headline_change_name)
		("headline_change_name"        , "text"    ): _("Save map"),
		# (helptext of widget: okButton)
		("okButton"                    , "helptext"): _("Save the map"),
		},

	"boatbuilder.xml" : {
		# (text of widget: BB_cancel_build_label) abort construction of a ship, lose invested resources
		("BB_cancel_build_label"       , "text"    ): _("Cancel building:"),
		# (text of widget: BB_cancel_warning_label) abort construction of a ship, lose invested resources
		("BB_cancel_warning_label"     , "text"    ): _("(lose all resources)"),
		# (text of widget: BB_current_order) Information about the ship currently under construction at the boat builder
		("BB_current_order"            , "text"    ): _("Currently building:"),
		# (text of widget: BB_howto_build_lbl)
		("BB_howto_build_lbl"          , "text"    ): _("To build a boat, click on one of the class tabs, select the desired ship and confirm the order."),
		# (text of widget: BB_progress_label) Refers to the resources still missing to complete the current boat builder task
		("BB_progress_label"           , "text"    ): _("Construction progress:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Building overview"),
		# (helptext of widget: BB_cancel_button) abort construction of a ship, lose invested resources
		("BB_cancel_button"            , "helptext"): _("Cancel all building progress"),
		# (helptext of widget: running_costs_label)
		("running_costs_label"         , "helptext"): _("Running costs"),
		# (helptext of widget: toggle_active_active) Pauses the current ship production, can be resumed later
		("toggle_active_active"        , "helptext"): _("Pause"),
		# (helptext of widget: toggle_active_inactive) Resumes the currently paused ship production
		("toggle_active_inactive"      , "helptext"): _("Resume"),
		},

	"boatbuilder_trade.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Trade boats"),
		# (text of widget: headline_BB_trade_ship1) The huker is a ship class mostly used for fishing. It is the starting ship of players in Unknown Horizons. If you are not sure how to translate, just leave the field empty and it will be called Huker.
		("headline_BB_trade_ship1"     , "text"    ): _("Huker"),
		# (helptext of widget: BB_build_trade_1)
		("BB_build_trade_1"            , "helptext"): _("Build this ship!"),
		# (helptext of widget: costs_001)
		("costs_001"                   , "helptext"): _("Money"),
		# (helptext of widget: costs_003)
		("costs_003"                   , "helptext"): _("Cloth"),
		# (helptext of widget: costs_004)
		("costs_004"                   , "helptext"): _("Boards"),
		# (helptext of widget: costs_006)
		("costs_006"                   , "helptext"): _("Tools"),
		},

	"boatbuilder_war1.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("War boats"),
		# (text of widget: headline_BB_war1_ship1)
		("headline_BB_war1_ship1"      , "text"    ): _("Frigate"),
		# (helptext of widget: BB_build_war1_1)
		("BB_build_war1_1"             , "helptext"): _("Build this ship!"),
		# (helptext of widget: costs_001)
		("costs_001"                   , "helptext"): _("Money"),
		# (helptext of widget: costs_003)
		("costs_003"                   , "helptext"): _("Cloth"),
		# (helptext of widget: costs_004)
		("costs_004"                   , "helptext"): _("Boards"),
		# (helptext of widget: costs_006)
		("costs_006"                   , "helptext"): _("Tools"),
		# (helptext of widget: costs_040)
		("costs_040"                   , "helptext"): _("Cannons"),
		},

	"diplomacy.xml" : {
		# (text of widget: ally_label) Diplomacy state of player
		("ally_label"                  , "text"    ): _("ally"),
		# (text of widget: enemy_label) Diplomacy state of player
		("enemy_label"                 , "text"    ): _("enemy"),
		# (text of widget: neutral_label) Diplomacy state of player
		("neutral_label"               , "text"    ): _("neutral"),
		},

	"overview_buildrelated.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Build fields"),
		},

	"overview_farm.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Building overview"),
		# (helptext of widget: capacity_utilisation_label)
		("capacity_utilisation_label"  , "helptext"): _("Capacity utilization"),
		# (helptext of widget: running_costs_label)
		("running_costs_label"         , "helptext"): _("Running costs"),
		# (helptext of widget: capacity_utilisation)
		("capacity_utilisation"        , "helptext"): _("Capacity utilization"),
		# (helptext of widget: running_costs)
		("running_costs"               , "helptext"): _("Running costs"),
		},

	"island_inventory.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Settlement inventory"),
		},

	"mainsquare_citizens.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Citizens"),
		# (text of widget: headline_residents_per_house)
		("headline_residents_per_house", "text"    ): _("Residents per house"),
		# (text of widget: headline_residents_total)
		("headline_residents_total"    , "text"    ): _("Summary"),
		# (text of widget: houses)
		("houses"                      , "text"    ): _("houses"),
		# (text of widget: resident_1)
		("resident_1"                  , "text"    ): _("1 resident"),
		# (text of widget: resident_2)
		("resident_2"                  , "text"    ): _("2 residents"),
		# (text of widget: resident_3)
		("resident_3"                  , "text"    ): _("3 residents"),
		# (text of widget: resident_4)
		("resident_4"                  , "text"    ): _("4 residents"),
		# (text of widget: resident_5)
		("resident_5"                  , "text"    ): _("5 residents"),
		# (text of widget: resident_6)
		("resident_6"                  , "text"    ): _("6 residents"),
		# (text of widget: resident_7)
		("resident_7"                  , "text"    ): _("7 residents"),
		# (text of widget: resident_8)
		("resident_8"                  , "text"    ): _("8 residents"),
		# (text of widget: residents)
		("residents"                   , "text"    ): _("residents"),
		# (text of widget: tax_label)
		("tax_label"                   , "text"    ): _("Taxes:"),
		# (text of widget: upgrades_lbl)
		("upgrades_lbl"                , "text"    ): _("Upgrade not possible:"),
		# (helptext of widget: allow_upgrades)
		("allow_upgrades"              , "helptext"): _("This is the current maximum increment!"),
		# (helptext of widget: paid_taxes_icon)
		("paid_taxes_icon"             , "helptext"): _("Paid taxes"),
		# (helptext of widget: tax_rate_icon)
		("tax_rate_icon"               , "helptext"): _("Tax rate"),
		# (helptext of widget: tax_val_label)
		("tax_val_label"               , "helptext"): _("Tax rate"),
		# (helptext of widget: taxes)
		("taxes"                       , "helptext"): _("Paid taxes"),
		},

	"mainsquare_inhabitants.xml" : {
		# (text of widget: avg_happiness_lbl)
		("avg_happiness_lbl"           , "text"    ): _("Average happiness:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Settler overview"),
		# (text of widget: most_needed_res_lbl)
		("most_needed_res_lbl"         , "text"    ): _("Most needed resource:"),
		},

	"mainsquare_pioneers.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Pioneers"),
		# (text of widget: headline_residents_per_house)
		("headline_residents_per_house", "text"    ): _("Residents per house"),
		# (text of widget: headline_residents_total)
		("headline_residents_total"    , "text"    ): _("Summary"),
		# (text of widget: houses)
		("houses"                      , "text"    ): _("houses"),
		# (text of widget: resident_1)
		("resident_1"                  , "text"    ): _("1 resident"),
		# (text of widget: resident_2)
		("resident_2"                  , "text"    ): _("2 residents"),
		# (text of widget: resident_3)
		("resident_3"                  , "text"    ): _("3 residents"),
		# (text of widget: residents)
		("residents"                   , "text"    ): _("residents"),
		# (text of widget: tax_label)
		("tax_label"                   , "text"    ): _("Taxes:"),
		# (text of widget: upgrades_lbl)
		("upgrades_lbl"                , "text"    ): _("Upgrade permissions:"),
		# (helptext of widget: paid_taxes_icon)
		("paid_taxes_icon"             , "helptext"): _("Paid taxes"),
		# (helptext of widget: tax_rate_icon)
		("tax_rate_icon"               , "helptext"): _("Tax rate"),
		# (helptext of widget: tax_val_label)
		("tax_val_label"               , "helptext"): _("Tax rate"),
		# (helptext of widget: taxes)
		("taxes"                       , "helptext"): _("Paid taxes"),
		},

	"mainsquare_sailors.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Sailors"),
		# (text of widget: headline_residents_per_house)
		("headline_residents_per_house", "text"    ): _("Residents per house"),
		# (text of widget: headline_residents_total)
		("headline_residents_total"    , "text"    ): _("Summary"),
		# (text of widget: houses)
		("houses"                      , "text"    ): _("houses"),
		# (text of widget: resident_1)
		("resident_1"                  , "text"    ): _("1 resident"),
		# (text of widget: resident_2)
		("resident_2"                  , "text"    ): _("2 residents"),
		# (text of widget: residents)
		("residents"                   , "text"    ): _("residents"),
		# (text of widget: tax_label)
		("tax_label"                   , "text"    ): _("Taxes:"),
		# (text of widget: upgrades_lbl)
		("upgrades_lbl"                , "text"    ): _("Upgrade permissions:"),
		# (helptext of widget: paid_taxes_icon)
		("paid_taxes_icon"             , "helptext"): _("Paid taxes"),
		# (helptext of widget: tax_rate_icon)
		("tax_rate_icon"               , "helptext"): _("Tax rate"),
		# (helptext of widget: tax_val_label)
		("tax_val_label"               , "helptext"): _("Tax rate"),
		# (helptext of widget: taxes)
		("taxes"                       , "helptext"): _("Paid taxes"),
		},

	"mainsquare_settlers.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Settlers"),
		# (text of widget: headline_residents_per_house)
		("headline_residents_per_house", "text"    ): _("Residents per house"),
		# (text of widget: headline_residents_total)
		("headline_residents_total"    , "text"    ): _("Summary"),
		# (text of widget: houses)
		("houses"                      , "text"    ): _("houses"),
		# (text of widget: resident_1)
		("resident_1"                  , "text"    ): _("1 resident"),
		# (text of widget: resident_2)
		("resident_2"                  , "text"    ): _("2 residents"),
		# (text of widget: resident_3)
		("resident_3"                  , "text"    ): _("3 residents"),
		# (text of widget: resident_4)
		("resident_4"                  , "text"    ): _("4 residents"),
		# (text of widget: resident_5)
		("resident_5"                  , "text"    ): _("5 residents"),
		# (text of widget: residents)
		("residents"                   , "text"    ): _("residents"),
		# (text of widget: tax_label)
		("tax_label"                   , "text"    ): _("Taxes:"),
		# (text of widget: upgrades_lbl)
		("upgrades_lbl"                , "text"    ): _("Upgrade permissions:"),
		# (helptext of widget: paid_taxes_icon)
		("paid_taxes_icon"             , "helptext"): _("Paid taxes"),
		# (helptext of widget: tax_rate_icon)
		("tax_rate_icon"               , "helptext"): _("Tax rate"),
		# (helptext of widget: tax_val_label)
		("tax_val_label"               , "helptext"): _("Tax rate"),
		# (helptext of widget: taxes)
		("taxes"                       , "helptext"): _("Paid taxes"),
		},

	"overview_enemybuilding.xml" : {
		},

	"overview_enemyunit.xml" : {
		},

	"overview_enemywarehouse.xml" : {
		# (text of widget: buying_label)
		("buying_label"                , "text"    ): _("Buying"),
		# (text of widget: selling_label)
		("selling_label"               , "text"    ): _("Selling"),
		},

	"overview_firestation.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Building overview"),
		# (text of widget: name_label)
		("name_label"                  , "text"    ): _("Name:"),
		# (helptext of widget: running_costs_label)
		("running_costs_label"         , "helptext"): _("Running costs"),
		# (helptext of widget: running_costs)
		("running_costs"               , "helptext"): _("Running costs"),
		},

	"overview_groundunit.xml" : {
		# (text of widget: lbl_weapon_storage)
		("lbl_weapon_storage"          , "text"    ): _("Weapons:"),
		},

	"overview_productionbuilding.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Building overview"),
		# (helptext of widget: capacity_utilisation_label)
		("capacity_utilisation_label"  , "helptext"): _("Capacity utilization"),
		# (helptext of widget: running_costs_label)
		("running_costs_label"         , "helptext"): _("Running costs"),
		# (helptext of widget: capacity_utilisation)
		("capacity_utilisation"        , "helptext"): _("Capacity utilization"),
		# (helptext of widget: running_costs)
		("running_costs"               , "helptext"): _("Running costs"),
		},

	"overview_resourcedeposit.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Resource deposit"),
		# (text of widget: res_dep_description_lbl)
		("res_dep_description_lbl"     , "text"    ): _("This is a resource deposit where you can build a mine to dig up resources."),
		# (text of widget: res_dep_description_lbl2) It == The resource deposit
		("res_dep_description_lbl2"    , "text"    ): _("It contains these resources:"),
		},

	"overview_settler.xml" : {
		# (text of widget: needed_res_label)
		("needed_res_label"            , "text"    ): _("Needed resources:"),
		# (text of widget: tax_label)
		("tax_label"                   , "text"    ): _("Taxes:"),
		# (helptext of widget: happiness_label)
		("happiness_label"             , "helptext"): _("Happiness"),
		# (helptext of widget: paid_taxes_label)
		("paid_taxes_label"            , "helptext"): _("Paid taxes"),
		# (helptext of widget: paid_taxes_label)
		("paid_taxes_label"            , "helptext"): _("Tax rate"),
		# (helptext of widget: residents_label)
		("residents_label"             , "helptext"): _("Residents"),
		# (helptext of widget: headline)
		("headline"                    , "helptext"): _("Click to change the name of your settlement"),
		# (helptext of widget: inhabitants)
		("inhabitants"                 , "helptext"): _("Residents"),
		# (helptext of widget: tax_val_label)
		("tax_val_label"               , "helptext"): _("Tax rate"),
		# (helptext of widget: taxes)
		("taxes"                       , "helptext"): _("Paid taxes"),
		# (helptext of widget: happiness)
		("happiness"                   , "helptext"): _("Happiness"),
		},

	"overview_signalfire.xml" : {
		# (text of widget: signal_fire_description_lbl)
		("signal_fire_description_lbl" , "text"    ): _("The signal fire shows the free trader how to reach your settlement in case you want to buy or sell goods."),
		},

	"overview_tower.xml" : {
		# (text of widget: name_label)
		("name_label"                  , "text"    ): _("Name:"),
		# (helptext of widget: running_costs_label)
		("running_costs_label"         , "helptext"): _("Running costs"),
		# (helptext of widget: headline)
		("headline"                    , "helptext"): _("Click to change the name of your settlement"),
		# (helptext of widget: running_costs)
		("running_costs"               , "helptext"): _("Running costs"),
		},

	"overview_tradership.xml" : {
		# (text of widget: trader_description_lbl)
		("trader_description_lbl"      , "text"    ): _("This is the free trader's ship. It will visit you from time to time to buy or sell goods."),
		},

	"overview_warehouse.xml" : {
		# (text of widget: name_label)
		("name_label"                  , "text"    ): _("Name:"),
		# (helptext of widget: collector_utilisation_label)
		("collector_utilisation_label" , "helptext"): _("Collector utilisation"),
		# (helptext of widget: running_costs_label)
		("running_costs_label"         , "helptext"): _("Running costs"),
		# (helptext of widget: collector_utilisation) Percentage describing how busy the collectors were (100% = always going for / already carrying full load of goods)
		("collector_utilisation"       , "helptext"): _("Collector utilisation"),
		# (helptext of widget: headline)
		("headline"                    , "helptext"): _("Click to change the name of your settlement"),
		# (helptext of widget: running_costs)
		("running_costs"               , "helptext"): _("Running costs"),
		},

	"overviewtab.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Overview"),
		# (text of widget: name_label)
		("name_label"                  , "text"    ): _("Name:"),
		},

	"overview_select_multi.xml" : {
		},

	"unit_entry_widget.xml" : {
		},

	"buy_sell_goods.xml" : {
		# (text of widget: buying_label)
		("buying_label"                , "text"    ): _("Buying"),
		# (text of widget: exchange_label)
		("exchange_label"              , "text"    ): _("Exchange:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Trade"),
		# (text of widget: selling_label)
		("selling_label"               , "text"    ): _("Selling"),
		# (text of widget: ship_label)
		("ship_label"                  , "text"    ): _("Ship:"),
		# (text of widget: trade_with_label)
		("trade_with_label"            , "text"    ): _("Trade partner:"),
		},

	"exchange_goods.xml" : {
		# (text of widget: exchange_label)
		("exchange_label"              , "text"    ): _("Exchange:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Trade"),
		# (text of widget: ship_label)
		("ship_label"                  , "text"    ): _("Ship:"),
		# (text of widget: trade_with_label)
		("trade_with_label"            , "text"    ): _("Trade partner:"),
		},

	"overview_trade_ship.xml" : {
		# (helptext of widget: name)
		("name"                        , "helptext"): _("Click to change the name of this ship"),
		# (helptext of widget: configure_route)
		("configure_route"             , "helptext"): _("Configure trading route"),
		# (helptext of widget: found_settlement)
		("found_settlement"            , "helptext"): _("Build settlement"),
		# (helptext of widget: trade)
		("trade"                       , "helptext"): _("Trade"),
		},

	"overview_war_ship.xml" : {
		# (helptext of widget: name)
		("name"                        , "helptext"): _("Click to change the name of this ship"),
		# (helptext of widget: configure_route)
		("configure_route"             , "helptext"): _("Configure trading route"),
		# (helptext of widget: found_settlement)
		("found_settlement"            , "helptext"): _("Build settlement"),
		# (helptext of widget: trade)
		("trade"                       , "helptext"): _("Trade"),
		},

	"tab_base.xml" : {
		},

	"buysellmenu.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Buy or sell resources"),
		# (text of widget: headline_trade_history)
		("headline_trade_history"      , "text"    ): _("Trade history"),
		},

	"select_trade_resource.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Select resources:"),
		},

	"tab_account.xml" : {
		# (text of widget: buy_expenses_label)
		("buy_expenses_label"          , "text"    ): _("Buying"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Account"),
		# (text of widget: headline_balance_label)
		("headline_balance_label"      , "text"    ): _("Balance:"),
		# (text of widget: headline_expenses_label)
		("headline_expenses_label"     , "text"    ): _("Expenses:"),
		# (text of widget: headline_income_label)
		("headline_income_label"       , "text"    ): _("Income:"),
		# (text of widget: running_costs_label)
		("running_costs_label"         , "text"    ): _("Running costs"),
		# (text of widget: sell_income_label)
		("sell_income_label"           , "text"    ): _("Sale"),
		# (text of widget: taxes_label)
		("taxes_label"                 , "text"    ): _("Taxes"),
		# (helptext of widget: show_production_overview)
		("show_production_overview"    , "helptext"): _("Show resources produced in this settlement"),
		},

	"trade_single_slot.xml" : {
		},

	"overview_farmproductionline.xml" : {
		# (helptext of widget: toggle_active_active)
		("toggle_active_active"        , "helptext"): _("Pause production"),
		# (helptext of widget: toggle_active_inactive)
		("toggle_active_inactive"      , "helptext"): _("Start production"),
		},

	"overview_productionline.xml" : {
		# (helptext of widget: toggle_active_active)
		("toggle_active_active"        , "helptext"): _("Pause production"),
		# (helptext of widget: toggle_active_inactive)
		("toggle_active_inactive"      , "helptext"): _("Start production"),
		},

	"relatedfields.xml" : {
		},

	"resbar_resource_selection.xml" : {
		# (text of widget: make_default_btn)
		("make_default_btn"            , "text"    ): _("Save as default"),
		# (text of widget: reset_default_btn)
		("reset_default_btn"           , "text"    ): _("Restore default"),
		# (text of widget: headline) Please keep the translation similarly short and concise, else the tooltip is not well understood by players.
		("headline"                    , "text"    ): _("Select resource:"),
		# (helptext of widget: make_default_btn)
		("make_default_btn"            , "helptext"): _("Save current resource configuration as default for all settlements."),
		# (helptext of widget: reset_default_btn)
		("reset_default_btn"           , "helptext"): _("Reset default resource configuration for all settlements."),
		# (helptext of widget: headline) Please keep the translation similarly short and concise, else the tooltip is not well understood by players.
		("headline"                    , "helptext"): _("The resource you select is displayed instead of the current one. Empty by clicking on X."),
		},

	"route_entry.xml" : {
		# (helptext of widget: delete_warehouse) Trade route entry
		("delete_warehouse"            , "helptext"): _("Delete entry"),
		# (helptext of widget: move_down) Trade route entry
		("move_down"                   , "helptext"): _("Move down"),
		# (helptext of widget: move_up) Trade route entry
		("move_up"                     , "helptext"): _("Move up"),
		},

	"trade_history_item.xml" : {
		},

	"captains_log.xml" : {
		# (text of widget: stats_players)
		("stats_players"               , "text"    ): _("Players"),
		# (text of widget: stats_settlements)
		("stats_settlements"           , "text"    ): _("My settlements"),
		# (text of widget: stats_ships)
		("stats_ships"                 , "text"    ): _("My ships"),
		# (text of widget: wb2) Only filter messages important for your own settlements (disasters, new increment, ...)
		("wb2"                         , "text"    ): _("Own settlements"),
		# (text of widget: wb5) Sends the chat message to all allied players.
		("wb5"                         , "text"    ): _("Allies"),
		# (text of widget: weird_button_1) Displays all notifications and game messages
		("weird_button_1"              , "text"    ): _("Whole world"),
		# (text of widget: weird_button_4) Sends the chat message to all players (default)
		("weird_button_4"              , "text"    ): _("Everybody"),
		# (text of widget: headline_chat)
		("headline_chat"               , "text"    ): _("Chat"),
		# (text of widget: headline_game_messages)
		("headline_game_messages"      , "text"    ): _("Game messages"),
		# (text of widget: headline_statistics)
		("headline_statistics"         , "text"    ): _("Statistics"),
		# (helptext of widget: okButton)
		("okButton"                    , "helptext"): _("Return to game"),
		# (helptext of widget: backwardButton) Entry of Captain's Log (logbook/diary used in scenarios)
		("backwardButton"              , "helptext"): _("Read previous entries"),
		# (helptext of widget: forwardButton) Entry of Captain's Log (logbook/diary used in scenarios)
		("forwardButton"               , "helptext"): _("Read next entries"),
		},

	"choose_next_scenario.xml" : {
		# (text of widget: head_left)
		("head_left"                   , "text"    ): _("Available Scenarios"),
		# (text of widget: head_right)
		("head_right"                  , "text"    ): _("Scenario description"),
		# (text of widget: scenario_details) More text describing the scenario
		("scenario_details"            , "text"    ): _("Details:"),
		# (helptext of widget: cancelButton) Players either select the next scenario they want to play or press this button
		("cancelButton"                , "helptext"): _("Continue playing"),
		# (helptext of widget: choose_scenario) Select which scenario to play
		("choose_scenario"             , "helptext"): _("Choose this scenario"),
		},

	"configure_route.xml" : {
		# (text of widget: lbl_route_activity)
		("lbl_route_activity"          , "text"    ): _("Route activity:"),
		# (text of widget: lbl_wait_at_load) Trade route setting: Whether to wait until all goods could be loaded.
		("lbl_wait_at_load"            , "text"    ): _("Wait at load:"),
		# (text of widget: lbl_wait_at_unload) Trade route setting: Whether to wait until all goods could be unloaded.
		("lbl_wait_at_unload"          , "text"    ): _("Wait at unload:"),
		# (helptext of widget: okButton)
		("okButton"                    , "helptext"): _("Exit"),
		# (helptext of widget: start_route) Trade route
		("start_route"                 , "helptext"): _("Start route"),
		},

	"healthwidget.xml" : {
		},

	"island_production.xml" : {
		# (helptext of widget: okButton)
		("okButton"                    , "helptext"): _("Close"),
		},

	"players_overview.xml" : {
		# (text of widget: building_score)
		("building_score"              , "text"    ): _("Buildings"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Player scores"),
		# (text of widget: land_score)
		("land_score"                  , "text"    ): _("Land"),
		# (text of widget: money_score)
		("money_score"                 , "text"    ): _("Money"),
		# (text of widget: player_name)
		("player_name"                 , "text"    ): _("Name"),
		# (text of widget: resource_score)
		("resource_score"              , "text"    ): _("Resources"),
		# (text of widget: settler_score)
		("settler_score"               , "text"    ): _("Settlers"),
		# (text of widget: total_score)
		("total_score"                 , "text"    ): _("Total"),
		# (text of widget: unit_score)
		("unit_score"                  , "text"    ): _("Units"),
		# (helptext of widget: building_score)
		("building_score"              , "helptext"): _("Value of all the buildings in the player's settlement(s)"),
		# (helptext of widget: land_score)
		("land_score"                  , "helptext"): _("Value of usable land i.e Amount of Land that can be used to create buildings "),
		# (helptext of widget: money_score)
		("money_score"                 , "helptext"): _("Player's current treasury + income expected in near future"),
		# (helptext of widget: player_name)
		("player_name"                 , "helptext"): _("Player Name"),
		# (helptext of widget: resource_score)
		("resource_score"              , "helptext"): _("Value of resources generated from all the possible sources in the player's settlement(s)"),
		# (helptext of widget: settler_score)
		("settler_score"               , "helptext"): _("Value denoting the progress of the settlement(s) in terms of inhabitants, buildings and overall happiness"),
		# (helptext of widget: total_score)
		("total_score"                 , "helptext"): _("The total value from all individual entities or in short : Total Player Score"),
		# (helptext of widget: unit_score)
		("unit_score"                  , "helptext"): _("Value of all the units owned by the player"),
		},

	"players_settlements.xml" : {
		# (text of widget: balance)
		("balance"                     , "text"    ): _("Balance"),
		# (text of widget: inhabitants)
		("inhabitants"                 , "text"    ): _("Inhabitants"),
		# (text of widget: running_costs)
		("running_costs"               , "text"    ): _("Running costs"),
		# (text of widget: settlement_name)
		("settlement_name"             , "text"    ): _("Name"),
		# (text of widget: taxes)
		("taxes"                       , "text"    ): _("Taxes"),
		},

	"ships_list.xml" : {
		# (text of widget: health)
		("health"                      , "text"    ): _("Health"),
		# (text of widget: ship_name)
		("ship_name"                   , "text"    ): _("Name"),
		# (text of widget: ship_type)
		("ship_type"                   , "text"    ): _("Type"),
		# (text of widget: status)
		("status"                      , "text"    ): _("Status"),
		# (text of widget: weapons)
		("weapons"                     , "text"    ): _("Weapons"),
		},

	"stancewidget.xml" : {
		# (helptext of widget: aggressive_stance) Description of combat stance (how units behave when fighting)
		("aggressive_stance"           , "helptext"): _("Aggressive"),
		# (helptext of widget: flee_stance) Description of combat stance (how units behave when fighting)
		("flee_stance"                 , "helptext"): _("Flee"),
		# (helptext of widget: hold_ground_stance) Description of combat stance (how units behave when fighting)
		("hold_ground_stance"          , "helptext"): _("Hold ground"),
		# (helptext of widget: none_stance) Description of combat stance (how units behave when fighting)
		("none_stance"                 , "helptext"): _("Passive"),
		},

	"tooltip.xml" : {
		},

	"call_for_support.xml" : {
		},

	"credits0.xml" : {
		},

	"credits1.xml" : {
		},

	"credits2.xml" : {
		},

	"credits3.xml" : {
		},

	"credits4.xml" : {
		},

	"help.xml" : {
		# (text of widget: fife_and_uh_team)
		("fife_and_uh_team"            , "text"    ): _("The FIFE and Unknown Horizons development teams"),
		# (text of widget: have_fun)
		("have_fun"                    , "text"    ): _("Have fun."),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Key bindings"),
		# (text of widget: lbl_BUILD_TOOL)
		("lbl_BUILD_TOOL"              , "text"    ): _("Show build menu"),
		# (text of widget: lbl_CHAT)
		("lbl_CHAT"                    , "text"    ): _("Chat"),
		# (text of widget: lbl_CONSOLE)
		("lbl_CONSOLE"                 , "text"    ): _("Toggle console on/off"),
		# (text of widget: lbl_COORD_TOOLTIP)
		("lbl_COORD_TOOLTIP"           , "text"    ): _("Show coordinate values (Debug)"),
		# (text of widget: lbl_DESTROY_TOOL)
		("lbl_DESTROY_TOOL"            , "text"    ): _("Enable destruct mode"),
		# (text of widget: lbl_DOWN)
		("lbl_DOWN"                    , "text"    ): _("Scroll down"),
		# (text of widget: lbl_GRID)
		("lbl_GRID"                    , "text"    ): _("Toggle grid on/off"),
		# (text of widget: lbl_HELP)
		("lbl_HELP"                    , "text"    ): _("Display help"),
		# (text of widget: lbl_LEFT)
		("lbl_LEFT"                    , "text"    ): _("Scroll left"),
		# (text of widget: lbl_LOGBOOK)
		("lbl_LOGBOOK"                 , "text"    ): _("Toggle Captain's log"),
		# (text of widget: lbl_PAUSE)
		("lbl_PAUSE"                   , "text"    ): _("Pause game"),
		# (text of widget: lbl_PLAYERS_OVERVIEW)
		("lbl_PLAYERS_OVERVIEW"        , "text"    ): _("Show player scores"),
		# (text of widget: lbl_QUICKLOAD)
		("lbl_QUICKLOAD"               , "text"    ): _("Quickload"),
		# (text of widget: lbl_QUICKSAVE)
		("lbl_QUICKSAVE"               , "text"    ): _("Quicksave"),
		# (text of widget: lbl_REMOVE_SELECTED)
		("lbl_REMOVE_SELECTED"         , "text"    ): _("Remove selected units / buildings"),
		# (text of widget: lbl_RIGHT)
		("lbl_RIGHT"                   , "text"    ): _("Scroll right"),
		# (text of widget: lbl_ROAD_TOOL)
		("lbl_ROAD_TOOL"               , "text"    ): _("Enable road building mode"),
		# (text of widget: lbl_ROTATE_LEFT)
		("lbl_ROTATE_LEFT"             , "text"    ): _("Rotate building or map counterclockwise"),
		# (text of widget: lbl_ROTATE_RIGHT)
		("lbl_ROTATE_RIGHT"            , "text"    ): _("Rotate building or map clockwise"),
		# (text of widget: lbl_SCREENSHOT)
		("lbl_SCREENSHOT"              , "text"    ): _("Screenshot"),
		# (text of widget: lbl_SETTLEMENTS_OVERVIEW)
		("lbl_SETTLEMENTS_OVERVIEW"    , "text"    ): _("Show settlement list"),
		# (text of widget: lbl_SHIFT)
		("lbl_SHIFT"                   , "text"    ): _("Hold to place multiple buildings"),
		# (text of widget: lbl_SHIPS_OVERVIEW)
		("lbl_SHIPS_OVERVIEW"          , "text"    ): _("Show ship list"),
		# (text of widget: lbl_SPEED_DOWN)
		("lbl_SPEED_DOWN"              , "text"    ): _("Decrease game speed"),
		# (text of widget: lbl_SPEED_UP)
		("lbl_SPEED_UP"                , "text"    ): _("Increase game speed"),
		# (text of widget: lbl_TILE_OWNER_HIGHLIGHT)
		("lbl_TILE_OWNER_HIGHLIGHT"    , "text"    ): _("Highlight tile ownership"),
		# (text of widget: lbl_TRANSLUCENCY)
		("lbl_TRANSLUCENCY"            , "text"    ): _("Toggle translucency of ambient buildings"),
		# (text of widget: lbl_UP)
		("lbl_UP"                      , "text"    ): _("Scroll up"),
		# (helptext of widget: okButton)
		("okButton"                    , "helptext"): _("Return"),
		},

	"ingamemenu.xml" : {
		# (text of widget: help)
		("help"                        , "text"    ): _("Help"),
		# (text of widget: loadgame)
		("loadgame"                    , "text"    ): _("Load game"),
		# (text of widget: quit)
		("quit"                        , "text"    ): _("Cancel game"),
		# (text of widget: savegame)
		("savegame"                    , "text"    ): _("Save game"),
		# (text of widget: settings)
		("settings"                    , "text"    ): _("Settings"),
		# (text of widget: start)
		("start"                       , "text"    ): _("Return to game"),
		},

	"loadingscreen.xml" : {
		# (text of widget: loading_label)
		("loading_label"               , "text"    ): _("Loading ..."),
		# (text of widget: version_label)
		("version_label"               , "text"    ): VERSION.string(),
		},

	"mainmenu.xml" : {
		# (text of widget: chimebell)
		("chimebell"                   , "text"    ): _("Attention please!"),
		# (text of widget: credits)
		("credits"                     , "text"    ): _("Credits"),
		# (text of widget: help) Main / in-game menu entry
		("help"                        , "text"    ): _("Help"),
		# (text of widget: loadgame) Open a widget to select which game to load
		("loadgame"                    , "text"    ): _("Load game"),
		# (text of widget: quit) Completely shut down UH
		("quit"                        , "text"    ): _("Quit"),
		# (text of widget: settings) Main / in-game menu entry
		("settings"                    , "text"    ): _("Settings"),
		# (text of widget: start) Opens widget to create singleplayer games (campaigns, scenarios, random maps, free play)
		("start"                       , "text"    ): _("Singleplayer"),
		# (text of widget: start_multi) Opens widget to join or create multiplayer games
		("start_multi"                 , "text"    ): _("Multiplayer"),
		# (text of widget: version_label)
		("version_label"               , "text"    ): VERSION.string(),
		},

	"multiplayer_creategame.xml" : {
		# (text of widget: create_game_lbl)
		("create_game_lbl"             , "text"    ): _("Create game:"),
		# (text of widget: exit_to_mp_menu_lbl)
		("exit_to_mp_menu_lbl"         , "text"    ): _("Back:"),
		# (text of widget: gamename_lbl)
		("gamename_lbl"                , "text"    ): _("Name of the game:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Choose a map:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Create game - Multiplayer"),
		# (text of widget: mp_player_limit_lbl)
		("mp_player_limit_lbl"         , "text"    ): _("Player limit:"),
		# (helptext of widget: cancel)
		("cancel"                      , "helptext"): _("Exit to multiplayer menu"),
		# (helptext of widget: create)
		("create"                      , "helptext"): _("Create this new game"),
		# (helptext of widget: gamename_lbl)
		("gamename_lbl"                , "helptext"): _("This will be displayed to other players so they recognise the game."),
		},

	"multiplayer_gamelobby.xml" : {
		# (text of widget: exit_to_mp_menu_lbl)
		("exit_to_mp_menu_lbl"         , "text"    ): _("Leave:"),
		# (text of widget: game_start_notice)
		("game_start_notice"           , "text"    ): _("The game will start as soon as enough players have joined."),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Chat:"),
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Gamelobby"),
		# (text of widget: startmessage)
		("startmessage"                , "text"    ): _("Game details:"),
		# (helptext of widget: cancel)
		("cancel"                      , "helptext"): _("Exit gamelobby"),
		},

	"multiplayermenu.xml" : {
		# (text of widget: active_games_lbl)
		("active_games_lbl"            , "text"    ): _("Active games:"),
		# (text of widget: create_game_lbl)
		("create_game_lbl"             , "text"    ): _("Create game:"),
		# (text of widget: exit_to_main_menu_lbl)
		("exit_to_main_menu_lbl"       , "text"    ): _("Main menu:"),
		# (text of widget: game_showonlyownversion)
		("game_showonlyownversion"     , "text"    ): _("Only show games with the same version:"),
		# (text of widget: headline_left)
		("headline_left"               , "text"    ): _("New game - Multiplayer"),
		# (text of widget: join_game_lbl)
		("join_game_lbl"               , "text"    ): _("Join game"),
		# (text of widget: load_game_lbl)
		("load_game_lbl"               , "text"    ): _("Load game:"),
		# (text of widget: refr_gamelist_lbl)
		("refr_gamelist_lbl"           , "text"    ): _("Refresh list:"),
		# (helptext of widget: cancel)
		("cancel"                      , "helptext"): _("Exit to main menu"),
		# (helptext of widget: create)
		("create"                      , "helptext"): _("Create a new game"),
		# (helptext of widget: join)
		("join"                        , "helptext"): _("Join the selected game"),
		# (helptext of widget: load)
		("load"                        , "helptext"): _("Load a saved game"),
		# (helptext of widget: refresh)
		("refresh"                     , "helptext"): _("Refresh list of active games"),
		},

	"settings.xml" : {
		# (text of widget: auto_unload_label)
		("auto_unload_label"           , "text"    ): _("Auto-unload ship:"),
		# (text of widget: autosave_interval_label)
		("autosave_interval_label"     , "text"    ): _("Autosave interval in minutes:"),
		# (text of widget: color_depth_label)
		("color_depth_label"           , "text"    ): _("Color depth:"),
		# (text of widget: debug_log_lbl)
		("debug_log_lbl"               , "text"    ): _("Enable logging"),
		# (text of widget: edge_scrolling_label)
		("edge_scrolling_label"        , "text"    ): _("Scroll at map edge:"),
		# (text of widget: effect_volume_label)
		("effect_volume_label"         , "text"    ): _("Effects volume:"),
		# (text of widget: fps_label)
		("fps_label"                   , "text"    ): _("Frame rate limit:"),
		# (text of widget: headline_graphics)
		("headline_graphics"           , "text"    ): _("Graphics"),
		# (text of widget: headline_language)
		("headline_language"           , "text"    ): _("Language"),
		# (text of widget: headline_mouse)
		("headline_mouse"              , "text"    ): _("Mouse"),
		# (text of widget: headline_network)
		("headline_network"            , "text"    ): _("Network"),
		# (text of widget: headline_saving)
		("headline_saving"             , "text"    ): _("Saving"),
		# (text of widget: headline_sound)
		("headline_sound"              , "text"    ): _("Sound"),
		# (text of widget: language_label)
		("language_label"              , "text"    ): _("Select language:"),
		# (text of widget: minimap_rotation_label)
		("minimap_rotation_label"      , "text"    ): _("Rotate minimap with map:"),
		# (text of widget: mouse_sensitivity_label)
		("mouse_sensitivity_label"     , "text"    ): _("Mouse sensitivity:"),
		# (text of widget: music_volume_label)
		("music_volume_label"          , "text"    ): _("Music volume:"),
		# (text of widget: network_port_lbl)
		("network_port_lbl"            , "text"    ): _("Network port:"),
		# (text of widget: number_of_autosaves_label)
		("number_of_autosaves_label"   , "text"    ): _("Number of autosaves:"),
		# (text of widget: number_of_quicksaves_label)
		("number_of_quicksaves_label"  , "text"    ): _("Number of quicksaves:"),
		# (text of widget: screen_fullscreen_text)
		("screen_fullscreen_text"      , "text"    ): _("Full screen:"),
		# (text of widget: screen_resolution_label)
		("screen_resolution_label"     , "text"    ): _("Screen resolution:"),
		# (text of widget: sound_enable_opt_text)
		("sound_enable_opt_text"       , "text"    ): _("Enable sound:"),
		# (text of widget: uninterrupted_building_label)
		("uninterrupted_building_label", "text"    ): _("Uninterrupted building:"),
		# (text of widget: use_renderer_label)
		("use_renderer_label"          , "text"    ): _("Used renderer:"),
		# (helptext of widget: cancelButton)
		("cancelButton"                , "helptext"): _("Return"),
		# (helptext of widget: defaultButton)
		("defaultButton"               , "helptext"): _("Reset to default settings"),
		# (helptext of widget: okButton)
		("okButton"                    , "helptext"): _("Apply"),
		# (helptext of widget: auto_unload_label)
		("auto_unload_label"           , "helptext"): _("Whether to unload the ship after founding a settlement"),
		# (helptext of widget: color_depth_label)
		("color_depth_label"           , "helptext"): _("If set to 0, use the driver default"),
		# (helptext of widget: debug_log_lbl)
		("debug_log_lbl"               , "helptext"): _("Don't use in normal game session. Decides whether to write debug information in the logging directory of your user directory. Slows the game down."),
		# (helptext of widget: edge_scrolling_label)
		("edge_scrolling_label"        , "helptext"): _("Whether to move the viewport when the mouse pointer is close to map edges"),
		# (helptext of widget: fps_label)
		("fps_label"                   , "helptext"): _("Set the maximum frame rate used. Default: 60 fps."),
		# (helptext of widget: minimap_rotation_label)
		("minimap_rotation_label"      , "helptext"): _("Whether to also rotate the minimap whenever the regular map is rotated"),
		# (helptext of widget: mouse_sensitivity_label)
		("mouse_sensitivity_label"     , "helptext"): _("0 is default system settings"),
		# (helptext of widget: network_port_lbl)
		("network_port_lbl"            , "helptext"): _("If set to 0, use the router default"),
		# (helptext of widget: uninterrupted_building_label)
		("uninterrupted_building_label", "helptext"): _("When enabled, do not exit the build mode after successful construction"),
		# (helptext of widget: use_renderer_label)
		("use_renderer_label"          , "helptext"): _("SDL is only meant as unsupported fallback and might cause problems!"),
		},

	"random_map_archive.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("Random map archive"),
		},

	"select_savegame.xml" : {
		# (text of widget: enter_filename_label)
		("enter_filename_label"        , "text"    ): _("Enter filename:"),
		# (text of widget: gamename_lbl)
		("gamename_lbl"                , "text"    ): _("Name of the game:"),
		# (text of widget: headline_details_label) More text describing the savegame
		("headline_details_label"      , "text"    ): _("Details:"),
		# (text of widget: headline_saved_games_label)
		("headline_saved_games_label"  , "text"    ): _("Your saved games:"),
		# (helptext of widget: cancelButton)
		("cancelButton"                , "helptext"): _("Cancel"),
		# (helptext of widget: deleteButton)
		("deleteButton"                , "helptext"): _("Delete selected savegame"),
		# (helptext of widget: gamename_lbl)
		("gamename_lbl"                , "helptext"): _("This will be displayed to other players so they recognise the game."),
		},

	"singleplayermenu.xml" : {
		# (text of widget: headline)
		("headline"                    , "text"    ): _("New game - Singleplayer"),
		# (text of widget: main_menu_label)
		("main_menu_label"             , "text"    ): _("Main menu:"),
		# (text of widget: start_game_label)
		("start_game_label"            , "text"    ): _("Start game:"),
		# (text of widget: campaign)
		("campaign"                    , "text"    ): _("Campaign"),
		# (text of widget: free_maps)
		("free_maps"                   , "text"    ): _("Free play"),
		# (text of widget: random)
		("random"                      , "text"    ): _("Random map"),
		# (text of widget: scenario)
		("scenario"                    , "text"    ): _("Scenario"),
		# (helptext of widget: cancel)
		("cancel"                      , "helptext"): _("Exit to main menu"),
		# (helptext of widget: okay)
		("okay"                        , "helptext"): _("Start game"),
		},

	"sp_campaign.xml" : {
		# (text of widget: choose_map_lbl)
		("choose_map_lbl"              , "text"    ): _("Choose a map to play:"),
		},

	"sp_free_maps.xml" : {
		# (text of widget: headline_choose_map_lbl)
		("headline_choose_map_lbl"     , "text"    ): _("Choose a map to play:"),
		},

	"sp_random.xml" : {
		# (text of widget: headline_map_settings_lbl)
		("headline_map_settings_lbl"   , "text"    ): _("Map settings:"),
		# (text of widget: seed_string_lbl)
		("seed_string_lbl"             , "text"    ): _("Seed:"),
		},

	"sp_scenario.xml" : {
		# (text of widget: choose_map_lbl)
		("choose_map_lbl"              , "text"    ): _("Choose a map to play:"),
		},

	"aidataselection.xml" : {
		# (text of widget: ai_players_label)
		("ai_players_label"            , "text"    ): _("AI players:"),
		},

	"game_settings.xml" : {
		# (text of widget: headline_game_settings_lbl)
		("headline_game_settings_lbl"  , "text"    ): _("Game settings:"),
		# (text of widget: lbl_disasters) Whether there should be disasters in the game.
		("lbl_disasters"               , "text"    ): _("Disasters"),
		# (text of widget: lbl_free_trader) Whether to create this kind of player in the game.
		("lbl_free_trader"             , "text"    ): _("Free Trader"),
		# (text of widget: lbl_pirates) Whether to create this kind of player in the game.
		("lbl_pirates"                 , "text"    ): _("Pirates"),
		},

	"playerdataselection.xml" : {
		# (text of widget: color_label)
		("color_label"                 , "text"    ): _("Color:"),
		# (text of widget: player_label)
		("player_label"                , "text"    ): _("Player name:"),
		},

	"popup_230.xml" : {
		},

	"popup_290.xml" : {
		},

	"popup_350.xml" : {
		},

	"startup_error_popup.xml" : {
		},
	}
