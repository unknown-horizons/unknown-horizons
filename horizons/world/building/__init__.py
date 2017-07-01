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

import logging

from fife import fife

import horizons.globals
from horizons.i18n import gettext as T
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.world.ingametype import IngameType
from horizons.world.production.producer import Producer


class BuildingClass(IngameType):
	log = logging.getLogger('world.building')

	basepackage = 'horizons.world.building.'
	classstring = 'Building[{id}]'

	def __new__(self, db, id, yaml_data):
		return super(BuildingClass, self).__new__(self, id, yaml_data)

	def __init__(self, db, id, yaml_data):
		"""
		Final loading for the building class. Load a lot of attributes for the building classes
		@param id: building id.
		@param db: DbReader
		"""
		super(BuildingClass, self).__init__(id, yaml_data)

		self.settler_level = yaml_data['tier']
		self.tooltip_text = self._strip_translation_marks(yaml_data['tooltip_text'])
		self.size = (int(yaml_data['size_x']), int(yaml_data['size_y']))
		self.width = self.size[0]
		self.height = self.size[1]
		self.inhabitants = int(yaml_data['inhabitants'])
		self.costs = yaml_data['buildingcosts']
		self.running_costs = yaml_data['cost']
		self.running_costs_inactive = yaml_data['cost_inactive']
		self.has_running_costs = bool(self.running_costs)
		self.show_status_icons = yaml_data.get('show_status_icons', True)
		self.translucent = yaml_data.get('translucent', False)
		# for mines: on which deposit is it buildable
		self.buildable_on_deposit_type = None
		try:
			component_template = self.get_component_template(Producer)
			self.buildable_on_deposit_type = component_template.get('is_mine_for')
		except KeyError:
			pass

	def __str__(self):
		return "Building[{id}]({name})".format(id=self.id, name=self.name)

	def _loadObject(cls):
		"""Loads building from the db.
		"""
		cls.log.debug("Loading building %s", cls.id)
		try:
			cls._real_object = horizons.globals.fife.engine.getModel().createObject(str(cls.id), 'building')
		except fife.NameClash:
			cls.log.debug("Already loaded building %s", cls.id)
			cls._real_object = horizons.globals.fife.engine.getModel().getObject(str(cls.id), 'building')
			return
		all_action_sets = ActionSetLoader.get_sets()

		# cls.action_sets looks like this: {tier1: {set1: None, set2: preview2, ..}, ..}
		for action_set_list in cls.action_sets.values():
			for action_set in action_set_list: # set1, set2, ...
				for action_id in all_action_sets[action_set]: # idle, move, ...
					cls._do_load(all_action_sets, action_set, action_id)

	def _do_load(cls, all_action_sets, action_set, action_id):
		params = {'id': action_set, 'action': action_id}
		action = cls._real_object.createAction('{action}_{id}'.format(**params))
		fife.ActionVisual.create(action)
		for rotation in all_action_sets[action_set][action_id]:
			params['rot'] = rotation
			# hacks to solve issue #1379
			if rotation == 45:
				# default values
				params['botm'] = 16 * cls.size[0]
				params['left'] = 32
				# hack for smeltery
				if cls.size[0] == 4 and cls.size[1] == 4:
					params["botm"] = 75
				elif cls.size[0] == 3:
					params["botm"] = 66
				# hack for charcoal_burning
				elif cls.size[0] == 2 and cls.size[1] == 3:
					params["botm"] = 55
					params["left"] = 25
				elif cls.size[0] == 2:
					params["botm"] = 40
				elif cls.size[0] == 1:
					params["botm"] = 29
			elif rotation == 135:
				# default values
				params['botm'] = 30
				params['left'] = 32 * cls.size[1]
				# hack for charcoal_burning
				if cls.size[0] == 2 and cls.size[1] == 3:
					params["botm"] = 35
					params["left"] = 65
			elif rotation == 225:
				# default values
				params['botm'] = 16 * cls.size[1]
				params['left'] = 32 * (cls.size[0] + cls.size[1] - 1)
				# hack for smeltery
				if cls.size[0] == 4 and cls.size[1] == 4:
					params["botm"] = 75
				elif cls.size[0] == 3:
					params["botm"] = 60
				# hack for brickyard
				elif cls.size[0] == 2 and cls.size[1] == 4:
					params["botm"] = 73
				# hack for charcoal_burning
				elif cls.size[0] == 2 and cls.size[1] == 3:
					params["botm"] = 42
					params["left"] = 130
				elif cls.size[0] == 2:
					params["botm"] = 40
				elif cls.size[0] == 1:
					params["botm"] = 29
			elif rotation == 315:
				# default values
				params['left'] = 32 * cls.size[0]
				params['botm'] = 16 * (cls.size[0] + cls.size[1] - 1)
				# hack for smeltery
				if cls.size[0] == 4 and cls.size[1] == 4:
					params["botm"] = 125
					params["left"] = 135
				elif cls.size[0] == 3:
					params["botm"] = 96
				# hack for brickyard
				elif cls.size[0] == 2 and cls.size[1] == 4:
					params["botm"] = 92
				# hack for charcoal_burning
				elif cls.size[0] == 2 and cls.size[1] == 3:
					params["botm"] = 75
					params["left"] = 100
				elif cls.size[0] == 2:
					params["botm"] = 56
				elif cls.size[0] == 1:
					params["botm"] = 30
			else:
				assert False, "Bad rotation for action_set {id}: {rot} for action: {action}".format(**params)
			path = '{id}+{action}+{rot}:shift:left-{left},bottom+{botm}'.format(**params)
			anim = horizons.globals.fife.animationloader.loadResource(path)
			action.get2dGfxVisual().addAnimation(int(rotation), anim)
			action.setDuration(anim.getDuration())

	def get_tooltip(self):
		"""Returns tooltip text of a building class.
		ATTENTION: This text is automatically translated when loaded
		already. DO NOT wrap the return value of this method in T()!
		@return: string tooltip_text
		"""
		# You usually do not need to change anything here when translating
		tooltip = T("{building}: {description}")
		return tooltip.format(building=self._name,
		                      description=self.tooltip_text)
