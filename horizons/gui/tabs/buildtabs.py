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

from horizons.entities import Entities
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.command.building import Build
from horizons.util import Callback, YamlCache, decorators
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.component.storagecomponent import StorageComponent
from horizons.messaging import NewPlayerSettlementHovered
from horizons.ext.enum import Enum

class InvalidBuildMenuFileFormat(Exception):
	pass

class BuildTab(TabInterface):
	"""
	Layout data is defined in image_data and text_data.
	Columns in the tabs are enumerated as follows:
	  01  11  21  31
	  02  12  22  32
	  03  13  23  33
	  04  14  24  34
	Boxes and Labels have the same number as their left upper icon.
	Check buildtab.xml for details. Icons without image are transparent.
	"""
	lazy_loading = True

	build_menus = [
	  "content/objects/gui_buildmenu/build_menu_per_increment.yaml",
	  "content/objects/gui_buildmenu/build_menu_per_type.yaml"
	  ]

	build_menu_config_per_increment = build_menus[0]
	build_menu_config_per_type = build_menus[1]

	default_build_menu_config = build_menu_config_per_increment

	cur_build_menu_config = default_build_menu_config

	# NOTE: check for occurences of this when adding one, you might want to
	#       add respective code there as well
	unlocking_strategies = Enum("tab_per_increment", # 1 tab per increment
	                            "single_per_increment" # each single building unlocked if increment is unlocked
	                            )

	last_active_build_tab = None

	def __init__(self, session, tabindex, data, build_callback, unlocking_strategy, build_menu_config):
		"""
		@param tabindex: position of tab
		@param data: data directly from yaml specifying the contents of this tab
		@param build_callback: called on clicks
		@param unlocking_strategy: element of unlocking_strategies
		@param build_menu_config: entry of build_menus where this definition originates from
		"""
		icon_path = None
		helptext = None
		headline = None
		rows = []
		for entry in data:
			if isinstance(entry, dict):
				# this is one key-value pair, e.g. "- icon: img/foo.png"
				if len(entry) != 1:
					raise InvalidBuildMenuFileFormat("Invalid entry in buildmenuconfig: %s" % entry)
				key, value = entry.items()[0]
				if key == "icon":
					icon_path = value
				elif key == "helptext":
					helptext = value[2:] if value.startswith('_ ') else value
				elif key == "headline":
					headline = value[2:] if value.startswith('_ ') else value
				else:
					raise InvalidBuildMenuFileFormat("Invalid key: %s\nMust be either icon, helptext or headline." % key)
			elif isinstance(entry, list):
				# this is a line of data
				rows.append(entry) # parse later on demand
			else:
				raise InvalidBuildMenuFileFormat("Invalid entry: %s" % entry)

		if not icon_path:
			raise InvalidBuildMenuFileFormat("icon_path definition is missing.")

		super(BuildTab, self).__init__(widget='buildtab.xml', icon_path=icon_path)
		self.session = session
		self.tabindex = tabindex
		self.build_callback = build_callback
		self.unlocking_strategy = unlocking_strategy
		if self.unlocking_strategy != self.__class__.unlocking_strategies.tab_per_increment:
			if not helptext and not headline:
				raise InvalidBuildMenuFileFormat("helptext definition is missing.")
		self.row_definitions = rows
		self.headline = _(headline) if headline else headline # don't translate None
		self.helptext = _(helptext) if helptext else self.headline
		self.build_menu_config = build_menu_config

	def _lazy_loading_init(self):
		super(BuildTab, self)._lazy_loading_init()
		self.init_gui()
		self.__current_settlement = None

	def init_gui(self):
		headline_lbl = self.widget.child_finder('headline')
		if self.headline: # prefer specific headline
			headline_lbl.text = self.headline
		elif self.unlocking_strategy == self.__class__.unlocking_strategies.tab_per_increment:
			headline_lbl.text = _(self.session.db.get_settler_name(self.tabindex))


	def set_content(self):
		"""Parses self.row_definitions and sets the content accordingly"""
		settlement = LastActivePlayerSettlementManager().get()
		def _set_entry(button, icon, building_id):
			"""Configure a single build menu button"""
			if self.unlocking_strategy == self.__class__.unlocking_strategies.single_per_increment and \
			   self.get_building_increments()[building_id] > self.session.world.player.settler_level:
				return

			building = Entities.buildings[building_id]
			button.helptext = self.session.db.get_building_tooltip(building_id)

			enough_res = False # don't show building by default
			if settlement is not None: # settlement is None when the mouse has left the settlement
				res_overview = self.session.ingame_gui.resource_overview
				button.mapEvents({
				  button.name+"/mouseEntered/buildtab" : Callback(res_overview.set_construction_mode, settlement, building.costs),
				  button.name+"/mouseExited/buildtab" : res_overview.close_construction_mode
				  })

				(enough_res, missing_res) = Build.check_resources({}, building.costs, settlement.owner, [settlement])
			#check whether to disable build menu icon (not enough res available)
			if enough_res:
				icon.image = "content/gui/images/buttons/buildmenu_button_bg.png"
				path = "content/gui/icons/buildmenu/{id:03d}{{mode}}.png".format(id=building_id)
				button.down_image = path.format(mode='_h')
				button.hover_image = path.format(mode='_h')
			else:
				icon.image = "content/gui/images/buttons/buildmenu_button_bg_bw.png"
				path = "content/gui/icons/buildmenu/greyscale/{id:03d}{{mode}}.png".format(id=building_id)
				button.down_image = path.format(mode='')
				button.hover_image = path.format(mode='')
			button.up_image = path.format(mode='')

			button.capture(Callback(self.build_callback, building_id))

		MAX_ROWS = 4
		MAX_COLS = 4
		for row_num, row in enumerate(self.row_definitions):
			# we have integers for building types, strings for headlines above slots and None as empty slots
			column = -1 # can't use enumerate, not always incremented
			for entry in row:
				column += 1
				position = (10*column) + (row_num+1) # legacy code, first row is 1, 11, 21
				if entry is None:
					continue
				elif (column + 1) > MAX_COLS: # out of 4x4 bounds
					err = "Invalid entry '%s': column %s does not exist." % (entry, column + 1)
					err += " Max. column amount in current layout is %s." % MAX_COLS
					raise InvalidBuildMenuFileFormat(err)
				elif row_num > MAX_ROWS: # out of 4x4 bounds
					err = "Invalid entry '%s': row %s does not exist." % (entry, row_num)
					err += " Max. row amount in current layout is %s." % MAX_ROWS
					raise InvalidBuildMenuFileFormat(err)
				elif isinstance(entry, basestring):
					column -= 1 # a headline does not take away a slot
					lbl = self.widget.child_finder('label_{position:02d}'.format(position=position))
					lbl.text = _(entry[2:]) if entry.startswith('_ ') else entry
				elif isinstance(entry, int):
					button = self.widget.child_finder('button_{position:02d}'.format(position=position))
					icon = self.widget.child_finder('icon_{position:02d}'.format(position=position))
					_set_entry(button, icon, entry)
				else:
					raise InvalidBuildMenuFileFormat("Invalid entry: %s" % entry)

	def refresh(self):
		self.set_content()

	def on_settlement_change(self, message):
		if message.settlement is not None:
			# only react to new actual settlements, else we have no res source
			self.refresh()

	def __remove_changelisteners(self):
		NewPlayerSettlementHovered.discard(self.on_settlement_change)
		if self.__current_settlement is not None:
			inventory = self.__current_settlement.get_component(StorageComponent).inventory
			inventory.discard_change_listener(self.refresh)

	def __add_changelisteners(self):
		NewPlayerSettlementHovered.subscribe(self.on_settlement_change)
		if self.__current_settlement is not None:
			inventory = self.__current_settlement.get_component(StorageComponent).inventory
			if not inventory.has_change_listener(self.refresh):
				inventory.add_change_listener(self.refresh)

	def show(self):
		self.__remove_changelisteners()
		self.__current_settlement = LastActivePlayerSettlementManager().get()
		self.__add_changelisteners()
		self.__class__.last_active_build_tab = self.tabindex
		super(BuildTab, self).show()

		button = self.widget.child_finder("switch_build_menu_config_button")
		self._set_switch_layout_button_image(button)
		button.capture(self._switch_build_menu_config)

	def hide(self):
		self.__remove_changelisteners()
		super(BuildTab, self).hide()

	def _set_switch_layout_button_image(self, button):
		image_path = "content/gui/icons/tabwidget/buildmenu/"
		if self.__class__.cur_build_menu_config is self.build_menu_config_per_type:
			button.up_image = image_path + "tier.png"
		else:
			button.up_image = image_path + "class.png"
		self.switch_layout_button_needs_update = False

	def _switch_build_menu_config(self):
		"""Sets next build menu config and recreates the gui"""
		cur_index = self.__class__.build_menus.index( self.cur_build_menu_config )
		new_index = (cur_index + 1) % len(self.__class__.build_menus)
		self.__class__.cur_build_menu_config = self.__class__.build_menus[ new_index ]

		# after switch set active tab to first
		self.__class__.last_active_build_tab = 0
		self.session.ingame_gui.show_build_menu(update=True)


	@classmethod
	def create_tabs(cls, session, build_callback):
		"""Create according to current build menu config
		@param build_callback: function to call to enable build mode, has to take building type parameter
		"""
		source = cls.cur_build_menu_config

		# parse
		data = YamlCache.get_file( source, game_data=True )
		if 'meta' not in data:
			raise InvalidBuildMenuFileFormat('File does not contain "meta" section')
		metadata = data['meta']
		if 'unlocking_strategy' not in metadata:
			raise InvalidBuildMenuFileFormat('"meta" section does not contain "unlocking_strategy"')
		try:
			unlocking_strategy = cls.unlocking_strategies.get_item_for_string( metadata['unlocking_strategy'] )
		except KeyError:
			raise InvalidBuildMenuFileFormat('Invalid entry for "unlocking_strategy"')

		# create tab instances
		tabs = []
		for tab, tabdata in sorted(data.iteritems()):
			if tab == "meta":
				continue # not a tab

			if unlocking_strategy == cls.unlocking_strategies.tab_per_increment and len(tabs) > session.world.player.settler_level:
				break

			try:
				tab = BuildTab(session, len(tabs), tabdata, build_callback, unlocking_strategy, source)
				tabs.append( tab )
			except Exception as e:
				to_add = "\nThis error happened in %s of %s ." % (tab, source)
				e.args = ( e.args[0] + to_add, ) + e.args[1:]
				e.message = ( e.message + to_add )
				raise

		return tabs

	@classmethod
	@decorators.cachedfunction
	def get_building_increments(cls):
		"""Returns a dictionary mapping building type ids to their increments
		@return cached dictionary (don't modifiy)"""
		building_increments = {}
		data = YamlCache.get_file( cls.build_menu_config_per_increment, game_data=True )
		increment = -1
		for tab, tabdata in sorted(data.iteritems()):
			if tab == "meta":
				continue # not a tab

			increment += 1

			for row in tabdata:
				if isinstance(row, list): # actual content
					for entry in row:
						if isinstance(entry, int): # actual building button
							building_increments[entry] = increment
		return building_increments


