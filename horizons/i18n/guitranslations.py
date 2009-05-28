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
		'hud_branch.xml' :
		{'buildingNameLabel'         : _('Branch office (Branch class ROMAN)')},
		'popupbox.xml' :
		{'okButton'                  : _('Ok')},
		'popupbox_with_cancel.xml' :
		{'cancelButton'              : _('Cancel'),
		 'okButton'                  : _('Ok')},
		'credits.xml' :
		{'creditsIntroText'          : _('These guys contributed to Unknown Horizons'),
		 'okButton'                  : _('You guys rock!')},
		'inventory.xml' :
		{'closeButton'               : _('Close'),
		 'islandInventoryLabel'      : _("That's your island-wide inventory."),
		 'CoinsLabel'                : _('Coins:'),
		 'LambWoolLabel'             : _('Lamb wool:'),
		 'TextileLabel'              : _('Textiles:'),
		 'BoardsLabel'               : _('Boards:'),
		 'FoodLabel'                 : _('Food:')},
		'hud_build_tab0.xml' :
		{'ServicesLabel'             : _('Services'),
		 'StorageLabel'              : _('Storage'),
		 'MainSquareLabel'           : _('Main Square'),
		 'ChurchLabel'               : _('Church'),
		 'SignalFireLabel'           : _('Signal Fire')},
		'hud_build_tab1.xml' :
		{'HudBuildTab1Residents'     : _('Residents'),
		 'HudBuildTab1Tent'          : _('Tent')},
		'hud_build_tab2.xml' :
		{'CompaniesLabel'            : _('Companies'),
		 'HunterLabel'               : _('Hunter'),
		 'FisherLabel'               : _('Fisher'),
		 'WeaverLabel'               : _('Weaver'),
		 'BoatBuilderLabel'          : _('Boat Builder'),
		 'LumberjackLabel'           : _('Lumberjack'),
		 'TreeLabel'                 : _('Tree'),
		 'HerderLabel'               : _('Herder'),
		 'FieldLabel'                : _('Field')},
		'hud_build_tab3.xml' :
		{'MilitaryLabel'             : _('Military'),
		 'LookoutLabel'              : _('Lookout'),
		 'RampartLabel'              : _('Rampart')},
		'hud_build_tab4.xml' :
		{'InfrastructureLabel'       : _('Infrastructure'),
		 'TrailLabel'                : _('Trail'),
		 'BridgeLabel'               : _('Bridge')},
		'hud_build_tab5.xml' :
		{'SpecialsLabel'             : _('Specials and Gifts'),
		 'CannotLabel'               : _('You can not build specials or gifts in this class')},
		'hud_tears_menu.xml' :
		{'ConfirmTearLabel'          : _('Do you want to remove this building?'),
		 'accept-1'                  : _('yes'),
		 'abort-1'                   : _('no')},
		'hud_builddetail.xml' :
		{'RunningCostsLabel'         : _('Running Costs')},
		'quitsession.xml' :
		{'ConfirmQuitLabel'          : _('Are you sure you want to abort the running session?'),
		 'cancelButton'              : _('Cancel'),
		 'okButton'                  : _('Ok')},
		'work_building_tab0.xml' :
		{'OverviewLabel'             : _('Overview:'),
		 'NameLabel'                 : _('Name:'),
		 'HealthLabel'               : _('Health:'),
		 'CostsLabel'                : _('Running Costs:'),
		 'BuySellLabel'              : _('Buy/Sell Resources:')},
		'work_building_tab1.xml' :
		{'StockLabel'                : _('stock')},
		'work_building_tab2.xml' :
		{'CombatLabel'               : _('combat')},
		'work_building_tab3.xml' :
		{'RouteLabel'                : _('route')},
		'work_building_tab4.xml' :
		{'ProductionLabel'           : _('production')},
		'work_building_tab5.xml' :
		{'ResearchLabel'             : _('research')},
		'production_building_overview.xml' :
		{'OverviewLabel'             : _('Overview:'),
		 'NameLabel'                 : _('Name:'),
		 'HealthLabel'               : _('Health:'),
		 'CostsLabel'                : _('Running Costs:'),
		 'ToogleActiveLabel'         : _('Toggle active:')},
		'hud_ship.xml' :
		{'buildingNameLabel'         : _('Ship name (Ship type)'),
		 'foundSettelment'           : _('New')},
		'load_disabled.xml' :
		{'SorryLabel'                : _("We're sorry, but the load function is not yet working."),
		 'okButton'                  : _('Ok')},
		'settings.xml' :
		{'okButton'                  : _('Ok'),
		 'cancelButton'              : _('Cancel'),
		 'sound_enable_opt'          : _('Enable Sound'),
		 'screen_fullscreen'         : _('Use the fullscreen mode'),
		 'settings_dialog_title'     : _('This is the Unknown Horizons settings dialog. Please make sure that you know, what you do.'),
		 'autosave_interval_label'   : _('Autosave interval:'),
		 'number_of_autosaves_label' : _('Number of saved autosaves:'),
		 'number_of_quicksaves_label': _('Number of saves quicksaves:'),
		 'screen_resolution_label'   : _('Screen resolution:'),
		 'use_renderer_label'          : _('Use renderer:'),
		 'color_depth_label'         : _('Color depth:'),
		 'music_volume_label'        : _('Music volume:'),
		 'effect_volume_label'       : _('Effects volume'),
		 'minutes_label'             : _('minutes'),
		 'language_label'            : _('Language:')},
		'ingame_save.xml' :
		{'enter_filename_label'      : _('Enter filename:'),
		 'deleteButton'              : _('Delete'),
		 'cancelButton'              : _('Cancel'),
		 'okButton'                  : _('Ok')},
		'changes_require_restart.xml' :
		{'require_restart_label'     : _('Some of your changes require a restart of Unknown Horizons.'),
		 'okButton'                  : _('Ok')},
		'loadingscreen.xml' :
		{'version_label'             : _('Unknown Horizons Alpha 2009.0'),
		 'loading_label'             : _('Loading ...')},
		'hud_buildinfo.xml' :
		{'buildingNameLabel'         : _('Building name (Building Class ROMAN)'),
		 'tiles_label'               : _('Tiles:')},
		'tab_stock.xml' :
		{'inventory_label'           : _('Inventory:')},
		'tab_overview_ship.xml' :
		{'overview_label'            : _('Overview'),
		 'name_label'                : _('Name:'),
		 'health_label'              : _('Health:'),
		 'new_settlement_label'      : _('Found new settlement')},
		'tab_overview.xml' :
		{'overview_label'            : _('Overview'),
		 'name_label'                : _('Name:'),
		 'health_label'              : _('Health:')},
		'tab_stock_ship.xml' :
		{'load_unload_label'         : _('Load/Unload:'),
		 'inventory_label'           : _('Inventory:')},
		'trade.xml' :
		{'trade_with_label'          : _('Trade with:'),
		 'excange_label'             : _('Excange:')},
		'mainmenu.xml' :
		{'version_label'             : _('Unknown Horizons Alpha 2009.0'),
		 'start'                     : _('Singleplayer'),
		 'start_multi'               : _('Multiplayer'),
		 'credits'                   : _(' Credits '),
		 'quit'                      : _(' Quit '),
		 'settings'                  : _(' Settings '),
		 'help'                      : _(' Help '),
		 'loadgame'                  : _(' Continue Game '),
		 'chimebell'                 : _(' Chime The Bell ')},
		'singleplayermenu.xml' :
		{'showRandom'                : _('Random '),
		 'showCampaign'              : _('Campaign '),
		 'player_label'              : _('Player:'),
		 'color_label'               : _('Color:'),
		 'playername'               : _('unknown player'),
		 'main_menu_label'           : _('Main menu:'),
		 'start_game_label'          : _('Start game:')},
		'chime.xml' :
		{'made_it_label'             : _('Yeah, you made it ...'),
		 'deadlink_label'            : _('But this is a deadlink, sorry.'),
		 'okButton'                  : _('Back to business ...')},
		'save_disabled.xml' :
		{'save_disabled'             : _("We're sorry, but the save function is not yet working."),
		 'okButton'                  : _('Ok')},
		'quitgame.xml' :
		{'quit_game_caption'         : _('Are you sure you want to Quit Unknown Horizons?'),
		 'cancelButton'              : _('Cancel'),
		 'okButton'                  : _('Ok')},
		'ingame_load.xml' :
		{'details_label'             : _('Details:'),
		 'deleteButton'              : _('Delete'),
		 'cancelButton'              : _('Cancel'),
		 'okButton'                  : _('Ok')},
		'gamemenu.xml' :
		{'start'                     : _('Return to Game'),
		 'quit'                      : _(' Cancel Game '),
		 'savegame'                  : _(' Save Game '),
		 'loadgame'                  : _(' Load Game '),
		 'help'                      : _(' Help '),
		 'chimebell'                 : _(' Chime The Bell '),
		 'settings'                  : _(' Settings ')},
		'serverlist.xml' :
		{'showInternet'              : _('Internet games'),
		 'showLAN'                   : _('LAN games'),
		 'showFavorites'             : _('Favorites')},
		'buysellmenu.xml' :
		{'buy_label'                 : _('Buy'),
		 'sell_label'                : _('Sell')},
		'help.xml' :
		{'okButton'                  : _('Close')},
		'hud_cityinfo.xml' :
		{'cityName'                  : _('City Name'),
		 'islandClass'               : _('Class ROMAN'),
		 'islandInhabitants'         : _('Inhabitants')},
		'hud_chat.xml' :
		{'chat_label'                : _('Chat'),
		 'message'                   : _('Enter your message'),
		 'sendButton'                : _('Send')},
		'serverlobby.xml' :
		{'player_label'              : _('Player:'),
		 'color_label'               : _('Color:'),
		 'playername'                : _('unknown player'),
		 'slots_label'               : _('Slots'),
		 'bots_label'                : _('Bots:'),
		 'chatinput'                 : _('Chat'),
		 'chatbutton'                : _('Chat')}

	}
