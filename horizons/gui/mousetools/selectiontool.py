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

from fife import fife

import horizons.main
from horizons.command.unit import Act
from horizons.util import WorldObject
from horizons.util.worldobject import WorldObjectNotFound
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.component.selectablecomponent import SelectableComponent
from horizons.constants import LAYERS

class SelectionTool(NavigationTool):
	_SELECTION_RECTANGLE_NAME = "_select" # GenericRenderer objects are sorted by name, so first char is important

	def __init__(self, session):
		super(SelectionTool, self).__init__(session)
		self.deselect_at_end = True # Set this to deselect selections while exiting SelectionTool
		self.session.gui.on_escape = self.session.gui.toggle_pause

	def remove(self):
		# Deselect if needed while exiting
		if self.deselect_at_end:
			selectables = self.filter_selectable( self.session.selected_instances )
			for i in self.filter_component(SelectableComponent, selectables):
				i.deselect()
		super(SelectionTool, self).remove()

	def is_selectable(self, entity):
		# also enemy entities are selectable, but the selection representation will differ
		return entity.has_component(SelectableComponent)

	def filter_component(self, component, instances):
		"""Only get specific component from a list of world objects"""
		return [instance.get_component(component) for instance in instances]

	def filter_selectable(self, instances):
		"""Only keeps selectables from a list of world objects"""
		return filter(self.is_selectable, instances)

	def is_owned_by_player(self, instance):
		"""Returns boolean if single world object is owned by local player"""
		return instance.owner is not None and \
			hasattr(instance.owner, "is_local_player") and \
			instance.owner.is_local_player

	def filter_owner(self, instances):
		"""Only keep instances belonging to the user. This is used for multiselection"""
		return [ i for i in instances if self.is_owned_by_player(i) ]

	def fife_instance_to_uh_instance(self, instance):
		"""Visual fife instance to uh game logic object or None"""
		i_id = instance.getId()
		if i_id != '':
			try:
				return WorldObject.get_object_by_id(int(i_id))
			except WorldObjectNotFound:
				return None
		else:
			return None

	def mouseDragged(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			do_multi = ((self.select_begin[0] - evt.getX()) ** 2 + (self.select_begin[1] - evt.getY()) ** 2) >= 10 # from 3px (3*3 + 1)
			self.session.view.renderer['GenericRenderer'].removeAll(self.__class__._SELECTION_RECTANGLE_NAME)
			if do_multi:
				# draw a rectangle
				a = fife.Point(min(self.select_begin[0], evt.getX()), \
											 min(self.select_begin[1], evt.getY()))
				b = fife.Point(max(self.select_begin[0], evt.getX()), \
											 min(self.select_begin[1], evt.getY()))
				c = fife.Point(max(self.select_begin[0], evt.getX()), \
											 max(self.select_begin[1], evt.getY()))
				d = fife.Point(min(self.select_begin[0], evt.getX()), \
											 max(self.select_begin[1], evt.getY()))
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(a), fife.RendererNode(b), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(b), fife.RendererNode(c), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(d), fife.RendererNode(c), 200, 200, 200)
				self.session.view.renderer['GenericRenderer'].addLine(self.__class__._SELECTION_RECTANGLE_NAME, \
				                                                      fife.RendererNode(a), fife.RendererNode(d), 200, 200, 200)

			instances = self.session.view.cam.getMatchingInstances(\
				fife.Rect(min(self.select_begin[0], evt.getX()), \
									min(self.select_begin[1], evt.getY()), \
									abs(evt.getX() - self.select_begin[0]), \
									abs(evt.getY() - self.select_begin[1])) if do_multi else fife.ScreenPoint(evt.getX(), evt.getY()),
			  self.session.view.layers[LAYERS.OBJECTS],
			  False) # False for accurate

			# get selection components
			instances = ( self.fife_instance_to_uh_instance(i) for i in instances )
			instances = [ i for i in instances if i is not None ]

			#we only consider selectable items when dragging a selection box
			instances = self.filter_selectable(instances)

			#if there's at least one of player unit, we don't select any enemies
			#applies both to buildings and ships
			if( any((self.is_owned_by_player(instance) for instance in instances))):
				instances = self.filter_owner(instances)

			self._update_selection( instances, do_multi )

		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseDragged(evt)
			return
		evt.consume()

	def mouseReleased(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and hasattr(self, 'select_begin'):
			self.apply_select()
			del self.select_begin, self.select_old
			self.session.view.renderer['GenericRenderer'].removeAll(self.__class__._SELECTION_RECTANGLE_NAME)
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			pass
		else:
			super(SelectionTool, self).mouseReleased(evt)
			return
		evt.consume()

	def apply_select(self):
		"""
		Called when selected instances changes. (Shows their menu)
		Does not do anything when nothing is selected, i.e. doesn't hide their menu.
		If one of the selected instances can attack, switch mousetool to AttackingTool.
		"""
		if self.session.world.health_visible_for_all_health_instances:
			self.session.world.toggle_health_for_all_health_instances()
		selected = self.session.selected_instances
		if len(selected) > 1 and all( i.is_unit for i in selected ):
			self.session.ingame_gui.show_multi_select_tab()
		elif len(selected) == 1:
			iter(selected).next().get_component(SelectableComponent).show_menu()

		#change session cursor to attacking tool if selected instances can attack
		from attackingtool import AttackingTool
		attacking_unit_found = False
		for i in selected:
			if hasattr(i, 'attack') and i.owner == self.session.world.player:
				attacking_unit_found = True
				self.deselect_at_end = False # Handover to AttackingTool without deselecting
				break

		if attacking_unit_found and not isinstance(self.session.cursor, AttackingTool):
			self.session.set_cursor('attacking')
		if not attacking_unit_found and isinstance(self.session.cursor, AttackingTool):
			self.session.set_cursor()
			horizons.main.fife.set_cursor_image('default')

	def mousePressed(self, evt):
		if evt.isConsumedByWidgets():
			super(SelectionTool, self).mousePressed(evt)
			return
		elif evt.getButton() == fife.MouseEvent.LEFT:
			if self.session.selected_instances is None:
				# this is a very odd corner case, it should only happen after the session has been ended
				# we can't allow to just let it crash however
				print 'WARNING: selected_instance is None. Please report this!'
				import traceback
				traceback.print_stack()
				print 'WARNING: selected_instance is None. Please report this!'
				return
			instances = self.get_hover_instances(evt)
			self.select_old = frozenset(self.session.selected_instances) if evt.isControlPressed() else frozenset()

			instances = filter(self.is_selectable, instances)
			#on single click only one building should be selected from the hover_instances
			#the if is for [] and [single_item] cases (they crashed)
			#it acts as user would expect (instances[0] selects buildings in front first)
			instances = instances if len(instances) <= 1 else [instances[0]]

			self._update_selection(instances)

			self.select_begin = (evt.getX(), evt.getY())
			self.session.ingame_gui.hide_menu()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			target_mapcoord = self.get_exact_world_location(evt)
			for i in self.session.selected_instances:
				if i.movable:
					Act(i, target_mapcoord.x, target_mapcoord.y).execute(self.session)
		else:
			super(SelectionTool, self).mousePressed(evt)
			return
		evt.consume()

	def _update_selection(self, instances, do_multi=False):
		"""
		self.select_old are old instances still relevant now (esp. on ctrl)
		@param instances: uh instances
		@param do_multi: true if selection rectangle on drag is used
		"""
		self.log.debug("update selection %s", [unicode(i) for i in instances])

		if do_multi: # add to selection
			instances = self.select_old.union(instances)
		else: # this is for deselecting among a selection with ctrl
			instances = self.select_old.symmetric_difference(instances)

		# sanity:
		# - if at least one unit, then only units
		if any( not instance.is_building for instance in instances ):
			instances = [ instance for instance in instances if not instance.is_building ]
		# - no multiple entities from enemy selected
		if len(instances) > 1:
			user_instances = self.filter_owner(instances)
			if user_instances: # check at least one remaining
				instances = user_instances
			else:
				instances = [iter(instances).next()]
		selectable = frozenset( self.filter_component(SelectableComponent, instances))

		# apply changes
		selected_components = set(self.filter_component(SelectableComponent,
					  self.filter_selectable(self.session.selected_instances)))
		for sel_comp in selected_components - selectable:
			sel_comp.deselect()
		for sel_comp in selectable - selected_components:
			sel_comp.select()

		self.session.selected_instances = set( i.instance for i in selectable )
