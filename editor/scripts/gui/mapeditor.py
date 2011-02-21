# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

"""
Visual Map Editor
=================

The map editor provides the user with an interface for editing
maps visually.

To edit a map through code, use MapController.

"""

import math
import os
import time
from datetime import date

from fife import fife
from fife.extensions import pychan
import fife.extensions.pychan.widgets as widgets
from fife.extensions import fife_utils

import scripts
import scripts.events as events
import action
from toolbar import ToolBar
from menubar import Menu, MenuBar
from action import Action, ActionGroup
from scripts.mapcontroller import MapController

class MapEditor:
	""" This class provides a basic user interface for map editing. It allows the user
		to visually edit a map.
	"""
	
	# Editor states
	SELECTING		= u"Selecting"
	INSERTING		= u"Inserting"
	REMOVING		= u"Removing"
	MOVING			= u"Moving"
	OBJECTPICKER	= u"Objectpicking"
	
	def __init__(self):
		""" Set up all variables and call some initial functions """
		self._ignoreToggles = False # A hack to avoid infinite recursion when toggling a button
		self._controller = None
		self._mode = MapEditor.SELECTING
		self._debug = False # TODO: We should have a central system for activating debug messages
		
		# GUI
		self._editor = scripts.editor.getEditor()
		self._eventlistener = self._editor.getEventListener()
		self._statusbar = self._editor.getStatusBar()
		self._toolbar = self._editor.getToolBar()
		self._toolbox = self._editor.getToolbox()
		
		# Currently selected object type
		self._object = None
		
		# Variables used for moving instances
		self._last_drag_pos = None
		self._last_drag_pos_exact = None
		
		self._selected_instances = []
		
		self._undogroup = False
		
		# Variables for scrolling the map
		self._dragx = 0
		self._dragy = 0
		self._scrollX = 0
		self._scrollY = 0
		
		self._initToolboxButtons()
		self._toolbox.show()
		
		events.postMapShown.connect(self._mapChanged)
		events.preMapClosed.connect(self._mapClosed)
		events.onObjectSelected.connect(self.setObject)
		
	def setObject(self, object):
		""" Set the object type to be paint onto map """
		self._object = object

	def getObject(self):
		""" Return the current object """
		return self._object

	def setController(self, controller):
		""" Set the controller to use. """
		if self._controller is not None:
			self._clear()
			
		self._controller = controller

		if self._controller is not None:
			self._init()
		
	def _init(self):
		""" Sets up the mapeditor to work with the selected controller """
		self._debug = self._controller.debug
		self._setMode(MapEditor.SELECTING)
		
		self._initToolbarbuttons()
		
		events.keyPressed.connect(self.keyPressed)
		events.keyReleased.connect(self.keyReleased)
		
		events.mousePressed.connect(self.mousePressed)
		events.mouseDragged.connect(self.mouseDragged)
		events.mouseReleased.connect(self.mouseReleased)
		events.mouseMoved.connect(self.mouseMoved)
		events.mouseEntered.connect(self.mouseEntered)
		events.mouseExited.connect(self.mouseExited)
		events.mouseWheelMovedUp.connect(self.mouseWheelMovedUp)
		events.mouseWheelMovedDown.connect(self.mouseWheelMovedDown)
		events.onPump.connect(self.pump)
		
	def _clear(self):
		""" Remove any functionality set up by _init """
		self._clearToolbarButtons()
		
		events.keyPressed.disconnect(self.keyPressed)
		events.keyReleased.disconnect(self.keyReleased)
		
		events.mousePressed.disconnect(self.mousePressed)
		events.mouseDragged.disconnect(self.mouseDragged)
		events.mouseReleased.disconnect(self.mouseReleased)
		events.mouseMoved.disconnect(self.mouseMoved)
		events.mouseExited.disconnect(self.mouseExited)
		events.mouseEntered.disconnect(self.mouseEntered)
		events.mouseWheelMovedUp.disconnect(self.mouseWheelMovedUp)
		events.mouseWheelMovedDown.disconnect(self.mouseWheelMovedDown)
		events.onPump.disconnect(self.pump)
		
	def _mapChanged(self, sender, mapview):
		""" Called when a new map is selected. 
			Sets the mapeditor to control the mapcontroller in the new map 
		"""
		self.setController(mapview.getController())
		
	def _mapClosed(self, sender, mapview):
		""" Called when a map is closed. """
		if mapview.getMap().getId() == self._controller.getMap().getId():
			self.setController(None)
		
	def _updateCursor(self):
		""" Updates the cursor to reflect the mode of the editor """
		engine = self._editor.getEngine()
		cursor = engine.getCursor()
		
		id = -1
		if self._mode == MapEditor.SELECTING:
			id = engine.getImagePool().addResourceFromFile("gui/icons/select_instance.png")
			image = engine.getImagePool().getImage(id)
			image.setXShift(-7)
			image.setYShift(-7)
			
		elif self._mode == MapEditor.INSERTING:
			id = engine.getImagePool().addResourceFromFile("gui/icons/add_instance.png")
			image = engine.getImagePool().getImage(id)
			image.setXShift(-2)
			image.setYShift(-20)
			
		elif self._mode == MapEditor.REMOVING:
			id = engine.getImagePool().addResourceFromFile("gui/icons/erase_instance.png")
			image = engine.getImagePool().getImage(id)
			image.setXShift(-2)
			image.setYShift(-19)
			
		elif self._mode == MapEditor.MOVING:
			id = engine.getImagePool().addResourceFromFile("gui/icons/move_instance.png")
			image = engine.getImagePool().getImage(id)
			image.setXShift(-11)
			image.setYShift(-11)
			
		elif self._mode == MapEditor.OBJECTPICKER:
			id = engine.getImagePool().addResourceFromFile("gui/icons/objectpicker.png")
			image = engine.getImagePool().getImage(id)
			image.setXShift(-0)
			image.setYShift(-22)
			
		if id < 0:
			self._resetCursor()
		else:
			cursor.set(fife.CURSOR_IMAGE, id)
			
	def _resetCursor(self):
		""" Reset the cursor to the standard native one """
		cursor = self._editor.getEngine().getCursor()
		cursor.set(fife.CURSOR_NATIVE, fife.NC_ARROW)
		
	def _initToolboxButtons(self):
		""" Sets up and connects buttons related to the toolbox """
		
		self._selectAction = Action(text=u"Select", icon="gui/icons/select_instance.png", checkable=True)
		self._drawAction = Action(text=u"Draw", icon="gui/icons/add_instance.png", checkable=True)
		self._removeAction = Action(text=u"Remove", icon="gui/icons/erase_instance.png", checkable=True)
		self._moveAction = Action(text=u"Move", icon="gui/icons/move_instance.png", checkable=True)
		self._objectpickerAction = Action(text=u"Pick object", icon="gui/icons/objectpicker.png", checkable=True)
		
		self._selectAction.helptext = u"Select cells on layer  (S)"
		self._moveAction.helptext = u"Moves instances   (M)"
		self._drawAction.helptext = u"Adds new instances based on currently selected object   (I)"
		self._removeAction.helptext = u"Deletes instances   (R)"
		self._objectpickerAction.helptext = u"Click an instance to set the current object to the one used by instance"
		
		action.toggled.connect(self._buttonToggled, sender=self._selectAction)
		action.toggled.connect(self._buttonToggled, sender=self._moveAction)
		action.toggled.connect(self._buttonToggled, sender=self._drawAction)
		action.toggled.connect(self._buttonToggled, sender=self._removeAction)
		action.toggled.connect(self._buttonToggled, sender=self._objectpickerAction)
		
		self._toolgroup = ActionGroup(exclusive=True, name=u"Tool group")
		self._toolgroup.addAction(self._selectAction)
		self._toolgroup.addAction(self._moveAction)
		self._toolgroup.addAction(self._drawAction)
		self._toolgroup.addAction(self._removeAction)
		self._toolgroup.addAction(self._objectpickerAction)
		
		self._toolbox.addAction(self._toolgroup)
		self._toolbox.adaptLayout()
		
		self._editor._edit_menu.addAction(self._toolgroup)
		
	def _initToolbarbuttons(self):
		""" Sets up and connects buttons related to the toolbar """
	
		rotateLeftAction = Action(text=u"Rotate counterclockwise", icon="gui/icons/rotate_countercw.png")
		rotateRightAction = Action(text=u"Rotate clockwise", icon="gui/icons/rotate_clockwise.png")
		zoomInAction = Action(text=u"Zoom in", icon="gui/icons/zoom_in.png")
		zoomOutAction = Action(text=u"Zoom out", icon="gui/icons/zoom_out.png")
		zoomResetAction = Action(text=u"Reset zoom", icon="gui/icons/zoom_default.png")
		screenshotAction = Action(text=u"Take screenshot", icon="gui/icons/take_screenshot.png")
		
		rotateLeftAction.helptext = u"Rotate counterclockwise by 90 degrees"
		rotateRightAction.helptext = u"Rotate clockwise by 90 degrees"
		zoomInAction.helptext = u"Zoom in   (CTRL + Mousewheel up)"
		zoomOutAction.helptext = u"Zoom out   (CTRL + Mousewheel down)"
		zoomResetAction.helptext = u"Reset zoom to default level"
		screenshotAction.helptext = u"Take screenshot   (F7)"
		
		action.activated.connect(self._rotateCounterClockwise, sender=rotateLeftAction)
		action.activated.connect(self._rotateClockwise, sender=rotateRightAction)
		action.activated.connect(self._zoomIn, sender=zoomInAction)
		action.activated.connect(self._zoomOut, sender=zoomOutAction)
		action.activated.connect(self._resetZoom, sender=zoomResetAction)
		action.activated.connect(self._captureScreen, sender=screenshotAction)
	
		self._viewGroup = ActionGroup(name=u"View group")
		self._viewGroup.addAction(rotateLeftAction)
		self._viewGroup.addAction(rotateRightAction)
		self._viewGroup.addAction(zoomInAction)
		self._viewGroup.addAction(zoomOutAction)
		self._viewGroup.addAction(zoomResetAction)
		self._viewGroup.addAction(screenshotAction)
		
		self._toolbar.addAction(self._viewGroup)
		self._toolbar.adaptLayout()
		
	def _clearToolbarButtons(self):
		""" Remove toolbar buttons """
		self._toolbar.removeAction(self._viewGroup)
		self._toolbar.adaptLayout()
		self._viewGroup = None
		
	def _setMode(self, mode):
		""" Set the editor mode """
		if (mode == MapEditor.INSERTING) and (not self._object):
			self._statusbar.setText(u'Please select object first')
			mode = self._mode

		self._ignoreToggles = True
		# Update toolbox buttons
		if (mode == MapEditor.INSERTING):
			self._drawAction.setChecked(True)
		elif mode == MapEditor.REMOVING:
			self._removeAction.setChecked(True)
		elif mode == MapEditor.MOVING:
			self._moveAction.setChecked(True)
		elif mode == MapEditor.OBJECTPICKER:
			self._objectpickerAction.setChecked(True)
		else:
			self._selectAction.setChecked(True)
		self._ignoreToggles = False

		self._mode = mode
		if self._debug: print "Entered mode " + mode
		self._statusbar.setText(mode)
		self._updateCursor()
		
	def _zoomIn(self, zoom=1.10):
		self._controller.setZoom(self._controller.getZoom()*zoom)
		
	def _zoomOut(self, zoom=1.10):
		self._controller.setZoom(self._controller.getZoom()/zoom)
		
	def _resetZoom(self):
		""" Resets zoom level to 1:1 """
		self._controller.setZoom(1)
		
	def _rotateCounterClockwise(self):
		""" Rotates map counterclockwise """
		self._controller.rotateCounterClockwise()
		
	def _rotateClockwise(self):
		""" Rotates map clockwise """
		self._controller.rotateClockwise()
		
	def _captureScreen(self):
		""" Saves a screenshot to the users data directory """
		userDir = fife_utils.getUserDataDirectory("fife", "editor")
		t = userDir+"/screenshots"
		if not os.path.isdir(t):
			os.makedirs(t)
		t += "/screen-%s-%s.png" % (date.today().strftime('%Y-%m-%d'),
									time.strftime('%H-%M-%S'))
		
		self._editor.getEngine().getRenderBackend().captureScreen(t)
		print "Saved screenshot to:", t		
		
	def _buttonToggled(self, sender, toggled):
		""" Called when a button controlling the editor mode was activated """
		if self._controller is None: return
		if self._ignoreToggles is True: return
	
		mode = MapEditor.SELECTING
		
		if toggled:
			if sender == self._selectAction:
				mode = MapEditor.SELECTING
			elif sender == self._moveAction:
				mode = MapEditor.MOVING
			elif sender == self._drawAction:
				mode = MapEditor.INSERTING
			elif sender == self._removeAction:
				mode = MapEditor.REMOVING
			elif sender == self._objectpickerAction:
				mode = MapEditor.OBJECTPICKER

		self._setMode(mode)
		
	def mousePressed(self, sender, event):
		if event.isConsumedByWidgets():
			return
			
		if not self._controller._layer:
			if self._debug: print 'No layers active. Cancelling map action'
			return

		realCoords = self._getRealCoords(sender, event)

		if event.getButton() == fife.MouseEvent.MIDDLE:
			self._dragx = realCoords[0]
			self._dragy = realCoords[1]
			
		else:
			if event.getButton() == fife.MouseEvent.RIGHT:
				self._controller.deselectSelection()
				
			if self._mode == MapEditor.SELECTING:
				if event.getButton() == fife.MouseEvent.LEFT:
					if self._eventlistener.shiftPressed:
						self._controller.deselectCell(realCoords[0], realCoords[1])
					else:
						if self._eventlistener.controlPressed is False:
							self._controller.deselectSelection()
						self._controller.selectCell(realCoords[0], realCoords[1])
					
				elif event.getButton() == fife.MouseEvent.RIGHT:
					self._controller.deselectSelection()
					
			elif self._mode == MapEditor.INSERTING:
				if event.getButton() == fife.MouseEvent.LEFT:
					self._controller.deselectSelection()
					self._controller.selectCell(realCoords[0], realCoords[1])
					self._controller.getUndoManager().startGroup("Inserted instances")
					self._undogroup = True
					
					position = self._controller._camera.toMapCoordinates(fife.ScreenPoint(realCoords[0], realCoords[1]), False)
					position = self._controller._layer.getCellGrid().toLayerCoordinates(position)
					
					self._controller.selectCell(realCoords[0], realCoords[1])
					self._controller.placeInstance(position, self._object)
				
			elif self._mode == MapEditor.REMOVING:
				if event.getButton() == fife.MouseEvent.LEFT:
					self._controller.deselectSelection()
					self._controller.selectCell(realCoords[0], realCoords[1])
					self._controller.getUndoManager().startGroup("Removed instances")
					self._undogroup = True
					
					self._controller.removeInstances(self._controller.getInstancesFromSelection())
				
			elif self._mode == MapEditor.MOVING:
				if event.getButton() == fife.MouseEvent.LEFT:
				
					position = self._controller._camera.toMapCoordinates(fife.ScreenPoint(realCoords[0], realCoords[1]), False)

					self._last_drag_pos = self._controller._layer.getCellGrid().toLayerCoordinates(position)
					self._last_drag_pos_exact = self._controller._layer.getCellGrid().toExactLayerCoordinates(position)
	
					for loc in self._controller._selection:
						if loc.getLayerCoordinates() == self._last_drag_pos:
							break
					else:
						self._controller.deselectSelection()
						self._controller.selectCell(realCoords[0], realCoords[1])
						
					self._selected_instances = self._controller.getInstancesFromSelection()
					
					self._controller.getUndoManager().startGroup("Moved instances")
					self._undogroup = True
					
			elif self._mode == MapEditor.OBJECTPICKER:
				position = self._controller._camera.toMapCoordinates(fife.ScreenPoint(realCoords[0], realCoords[1]), False)
				exact = self._controller._layer.getCellGrid().toExactLayerCoordinates(position)
				instances = self._controller.getInstancesFromPosition(exact)
				if len(instances) >= 1:
					object = instances[0].getObject()
					if object.getId() != self._object.getId() or object.getNamespace() != self._object.getNamespace():
						events.onObjectSelected.send(sender=self, object=object)

	def mouseDragged(self, sender, event):
		if event.isConsumedByWidgets():
			return
			
		if not self._controller._layer:
			if self._debug: print 'No layers active. Cancelling map action'
			return
			
		realCoords = self._getRealCoords(sender, event)
			
		if event.getButton() == fife.MouseEvent.MIDDLE:
			self._scrollX = (self._dragx-realCoords[0])/10.0
			self._scrollY = (self._dragy-realCoords[1])/10.0
			
		else:
			if self._mode != MapEditor.SELECTING:
				self._controller.deselectSelection()
				
			if self._mode == MapEditor.SELECTING:
				if event.getButton() == fife.MouseEvent.LEFT:
					if self._eventlistener.shiftPressed:
						self._controller.deselectCell(realCoords[0], realCoords[1])
					else:
						self._controller.selectCell(realCoords[0], realCoords[1])
					
			elif self._mode == MapEditor.INSERTING:
				position = self._controller._camera.toMapCoordinates(fife.ScreenPoint(realCoords[0], realCoords[1]), False)
				position = self._controller._layer.getCellGrid().toLayerCoordinates(position)
				
				self._controller.selectCell(realCoords[0], realCoords[1])
				self._controller.placeInstance(position, self._object)
				
			elif self._mode == MapEditor.REMOVING:
				self._controller.selectCell(realCoords[0], realCoords[1])
				self._controller.removeInstances(self._controller.getInstancesFromSelection())
				
			elif self._mode == MapEditor.MOVING:
				position = self._controller._camera.toMapCoordinates(fife.ScreenPoint(realCoords[0], realCoords[1]), False)
				
				positionExact = self._controller._layer.getCellGrid().toExactLayerCoordinates(position)
				position = self._controller._layer.getCellGrid().toLayerCoordinates(position)
				
				if self._eventlistener.shiftPressed:
					self._controller.moveInstances(self._selected_instances, positionExact-self._last_drag_pos_exact, True)
				else:
					self._controller.moveInstances(self._selected_instances, position-self._last_drag_pos, False)
				self._last_drag_pos = position
				self._last_drag_pos_exact = positionExact
				
				# Update selection
				self._controller.deselectSelection()
				
				for i in self._selected_instances:
					pos = i.getLocation().getMapCoordinates()
					pos = self._controller._camera.toScreenCoordinates(pos)
					self._controller.selectCell(pos.x, pos.y)
					
			elif self._mode == MapEditor.OBJECTPICKER:
				pass

	def mouseReleased(self, sender, event):
		if event.isConsumedByWidgets():
			return
			
		if not self._controller._layer:
			if self._debug: print 'No layers active. Cancelling map action'
			return
			
		if self._mode == MapEditor.SELECTING or self._mode == MapEditor.MOVING:
			instances = self._controller.getInstancesFromSelection()
			if len(instances) > 0:
				events.onInstancesSelected.send(sender=self, instances=instances)
			
		if event.getButton() == fife.MouseEvent.MIDDLE:
			self._scrollX = 0
			self._scrollY = 0
			
		realCoords = self._getRealCoords(sender, event)

		if self._undogroup:
			self._controller.getUndoManager().endGroup()
			self._undogroup = False

	def mouseMoved(self, sender, event):
		pass
		
	def mouseEntered(self, sender, event):
		# Mouse has entered map area. Set cursor to reflect current mode
		self._updateCursor()
		
	def mouseExited(self, sender, event):
		# Mouse has exited the map area. Set the cursor to native arrow
		self._resetCursor()
				
	def mouseWheelMovedUp(self, event):
		# Zoom in
		if self._eventlistener.controlPressed and self._controller._camera:
			self._controller._camera.setZoom(self._controller._camera.getZoom() * 1.10)

	def mouseWheelMovedDown(self, event):
		# Zoom out
		if self._eventlistener.controlPressed and self._controller._camera:
			self._controller._camera.setZoom(self._controller._camera.getZoom() / 1.10)

	def keyPressed(self, event):
		keyval = event.getKey().getValue()
		keystr = event.getKey().getAsString().lower()
		
		if keyval == fife.Key.LEFT:
			self._controller.moveCamera(50, 0)
		elif keyval == fife.Key.RIGHT:
			self._controller.moveCamera(-50, 0)
		elif keyval == fife.Key.UP:
			self._controller.moveCamera(0, 50)
		elif keyval == fife.Key.DOWN:
			self._controller.moveCamera(0, -50)
		
		elif keyval == fife.Key.INSERT:
			self._controller.fillSelection(self._object)

		elif keyval == fife.Key.DELETE:
			self._controller.clearSelection()
			
		elif keyval == fife.Key.F7:
			self.captureScreen()
			
		elif keystr == "s":
			self._setMode(MapEditor.SELECTING)
			
		elif keystr == "i":
			if self._mode != MapEditor.INSERTING:
				self._setMode(MapEditor.INSERTING)
			else:
				self._setMode(MapEditor.SELECTING)
			
		elif keystr == "r":
			if self._mode != MapEditor.REMOVING:
				self._setMode(MapEditor.REMOVING)
			else:
				self._setMode(MapEditor.SELECTING)

		elif keystr == 'm':
			if self._mode != MapEditor.MOVING:
				self._setMode(MapEditor.MOVING)
			else:
				self._setMode(MapEditor.SELECTING)

		elif keystr == 't':
			gridrenderer = self._controller._camera.getRenderer('GridRenderer')
			gridrenderer.setEnabled(not gridrenderer.isEnabled())

		elif keystr == 'b':
			blockrenderer = self._controller._camera.getRenderer('BlockingInfoRenderer')
			blockrenderer.setEnabled(not blockrenderer.isEnabled())

		elif keystr == 'c':
			self._editor.toggleCoordinates("Toggle Coordinates")
			
		elif keystr == 'z':
			if self._eventlistener.controlPressed:
				if self._eventlistener.altPressed:
					if self._eventlistener.shiftPressed:
						self._controller.getUndoManager().previousBranch()
					else:
						self._controller.getUndoManager().nextBranch()
				else:
					if self._eventlistener.shiftPressed:
						self._controller.redo()
					else:
						self._controller.undo()
			

	def keyReleased(self, event):		
		pass
		
	def _getRealCoords(self, sender, event):
		""" Converts relative widget coordinate to absolute coordinates """
		cw = sender
		offsetX = event.getX()
		offsetY = event.getY()
		
		parent = cw
		while parent is not None:
			if isinstance(parent, widgets.Widget):
				offsetX += parent.x
				offsetY += parent.y
				parent = parent.parent
			else:
				break
			
		return (offsetX, offsetY)
		
	def pump(self):
		""" Called each frame """
		# Scroll camera
		self._controller.moveCamera(self._scrollX, self._scrollY)