# -*- coding: utf-8 -*-
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

__all__ = ['building', 'housing', 'nature', 'path', 'production', 'storages', 'settler', 'boatbuilder']

import logging

import horizons.main
from fife import fife

from horizons.util import ActionSetLoader
from horizons.i18n.objecttranslations import object_translations
from horizons.world.ingametype import IngameType

class BuildingClass(IngameType):
	log = logging.getLogger('world.building')

	basepackage = 'horizons.world.building.'
	classstring = 'Building['

	def __new__(self, db, id, yaml_data):
		return super(BuildingClass, self).__new__(self, id, yaml_data)

	def __init__(self, db, id, yaml_data):
		"""
		Final loading for the building class. Load a lot of attributes for the building classes
		@param id: building id.
		@param db: DbReader
		"""
		super(BuildingClass, self).__init__(id, yaml_data)

		self.settler_level = yaml_data['settler_level']
		try:
			# NOTE: tooltip texts are always untranslated here, use db.get_building_tooltip()
			self.tooltip_text = object_translations[yaml_data['yaml_file']]['tooltip_text']
		except KeyError: # not found => use value defined in yaml unless it is null
			tooltip_text = yaml_data['tooltip_text']
			if tooltip_text is not None:
				self.tooltip_text = tooltip_text
			else:
				self.tooltip_text = u''
		self.size = (int(yaml_data['size_x']), int(yaml_data['size_y']))
		self.inhabitants = int(yaml_data['inhabitants'])
		self.costs = yaml_data['buildingcosts']
		self.running_costs = yaml_data['cost']
		self.running_costs_inactive = yaml_data['cost_inactive']
		self.has_running_costs = (self.running_costs != 0)
		self.show_status_icons = yaml_data.get('show_status_icons', True)
		# for mines: on which deposit is it buildable
		buildable_on_deposit_type = db("SELECT deposit FROM mine WHERE mine = ?", self.id)
		if buildable_on_deposit_type:
			self.buildable_on_deposit_type = buildable_on_deposit_type[0][0]

	def __str__(self):
		return "Building[" + str(self.id) + "](" + self.name + ")"


	def _loadObject(cls):
		"""Loads building from the db.
		"""
		cls.log.debug("Loading building %s", cls.id)
		try:
			cls._real_object = horizons.main.fife.engine.getModel().createObject(str(cls.id), 'building')
		except RuntimeError:
			cls.log.debug("Already loaded building %s", cls.id)
			cls._real_object = horizons.main.fife.engine.getModel().getObject(str(cls.id), 'building')
			return
		all_action_sets = ActionSetLoader.get_sets()

		# NOTE: the code below is basically duplicated in UHObjectLoader._loadBuilding in the editor

		# cls.action_sets looks like this: {tier1: {set1: None, set2: preview2, ..}, ..}
		for action_set_list in cls.action_sets.itervalues():
			for action_set_id in action_set_list.iterkeys(): # set1, set2, ...
				for action_id in all_action_sets[action_set_id].iterkeys(): # idle, move, ...
					action = cls._real_object.createAction(action_id+"_"+str(action_set_id))
					fife.ActionVisual.create(action)
					for rotation in all_action_sets[action_set_id][action_id].iterkeys():
						if rotation == 45:
							command = 'left-32,bottom+' + str(cls.size[0] * 16)
						elif rotation == 135:
							command = 'left-' + str(cls.size[1] * 32) + ',bottom+16'
						elif rotation == 225:
							command = 'left-' + str((cls.size[0] + cls.size[1] - 1) * 32) + ',bottom+' + str(cls.size[1] * 16)
						elif rotation == 315:
							command = 'left-' + str(cls.size[0] * 32) + ',bottom+' + str((cls.size[0] + cls.size[1] - 1) * 16)
						else:
							assert False, "Bad rotation for action_set %(id)s: %(rotation)s for action: %(action_id)s" % \
								   { 'id':action_set_id, 'rotation': rotation, 'action_id': action_id }
						anim = horizons.main.fife.animationloader.loadResource(str(action_set_id)+"+"+str(action_id)+"+"+str(rotation) + ':shift:' + command)
						action.get2dGfxVisual().addAnimation(int(rotation), anim)
						action.setDuration(anim.getDuration())

