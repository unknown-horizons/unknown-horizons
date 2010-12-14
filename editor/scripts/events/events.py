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

from fife import fife
import scripts
from fife.fife import IKeyListener, ICommandListener, IMouseListener, LayerChangeListener, MapChangeListener, ConsoleExecuter
from signal import Signal
import pdb

#--- Signals ---#
onPump = Signal()
preSave	= Signal(providing_args=["mapview"])
postSave = Signal(providing_args=["mapview"])
mapAdded = Signal(providing_args=["mapview"])
preMapShown = Signal(providing_args=["mapview"])
postMapShown = Signal(providing_args=["mapview"])
preMapClosed = Signal(providing_args=["mapview"])
postMapClosed = Signal(providing_args=["mapview"])
onInstancesSelected = Signal(providing_args=["instances"])
onObjectSelected = Signal(providing_args=["object"])
onObjectsImported = Signal(providing_args=[])

# Signals emitted by EventListener
onQuit			= Signal(providing_args=[])
keyPressed		= Signal(providing_args=["event"])
keyReleased		= Signal(providing_args=["event"])
mouseEntered	= Signal(providing_args=["event"])
mouseExited		= Signal(providing_args=["event"])
mousePressed	= Signal(providing_args=["event"])
mouseReleased	= Signal(providing_args=["event"])
mouseClicked	= Signal(providing_args=["event"])
mouseWheelMovedUp = Signal(providing_args=["event"])
mouseWheelMovedDown = Signal(providing_args=["event"])
mouseMoved		= Signal(providing_args=["event"])
mouseDragged	= Signal(providing_args=["event"])
onLayerChanged	= Signal(providing_args=["layer", "changedInstances"])
onInstanceCreate = Signal(providing_args=["layer", "instance"])
onInstanceDelete = Signal(providing_args=["layer", "instance"])
onMapChanged	= Signal(providing_args=["map", "changedLayers"])
onLayerCreate	= Signal(providing_args=["map", "layer"])
onLayerDelete	= Signal(providing_args=["map", "layer"])
onToolsClick	= Signal(providing_args=[])
onCommand		= Signal(providing_args=["command"])
onConsoleCommand= Signal(providing_args=["command"])

class KeySequence(object):
	def __init__(self):
		self.key = None
		self.modifiers = {"alt":False,"ctrl":False,"shift":False,"meta":False}
		self.signal = None

class EventListener:
	# NOTE: As FIFEdit currently covers the entire screen with widgets,
	#		FIFE doesn't receive any mouse or key events. Therefore we have to add
	#		mouse and key event tracking for the central widget
	
	def __init__(self, engine):
		self.engine = engine
		
		eventmanager = self.engine.getEventManager()
		self.keysequences = []
		
		self.keylistener			= _IKeyListener(engine)
		self.mouselistener			= _IMouseListener(engine)
		self.mapchangelistener		= _MapChangeListener(engine)
		self.layerchangelistener	= _LayerChangeListener(engine)
		self.commandlistener		= _ICommandListener(engine)
		self.consoleexecuter		= _ConsoleExecuter(engine)
		
		self.controlPressed = False
		self.altPressed		= False
		self.shiftPressed	= False
		self.metaPressed	= False
		
		eventmanager.addKeyListener(self.keylistener)
		eventmanager.addCommandListener(self.commandlistener)
		eventmanager.addMouseListener(self.mouselistener)
		self.engine.getGuiManager().getConsole().setConsoleExecuter(self.consoleexecuter)
		
		keyPressed.connect(self.keyPressed)
		keyReleased.connect(self.keyReleased)
		

	def getKeySequenceSignal(self, key, modifiers=[]):
		# Parse modifiers
		mods = {"alt":False,"ctrl":False,"shift":False,"meta":False}
		for m in modifiers:
			m = m.lower()
			if m in mods:
				mods[m] = True
			else:
				print "Unknown modifier:",m
		
		# Check if signal for keysequence has been created
		for k in self.keysequences:
			if k.key == key and k.modifiers == mods:
				return k.signal
				
		# Create keysequence and signal
		keysequence = KeySequence()
		keysequence.key = key
		keysequence.modifiers = mods
		keysequence.signal = Signal(providing_args=["event"])
		self.keysequences.append(keysequence)
		
		return keysequence.signal
		
	# IKeyListener
	def keyPressed(self, event):
		keyval = event.getKey().getValue()
		keystr = event.getKey().getAsString().lower()
		
		self.controlPressed = event.isControlPressed()
		self.altPressed		= event.isAltPressed()
		self.shiftPressed	= event.isShiftPressed()
		self.metaPressed	= event.isMetaPressed()
		
		if keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
			self.controlPressed = True
		elif keyval in (fife.Key.LEFT_SHIFT, fife.Key.RIGHT_SHIFT):
			self.shiftPressed = True
		elif keyval in (fife.Key.LEFT_ALT, fife.Key.RIGHT_ALT):
			self.altPressed = True
		elif keyval in (fife.Key.RIGHT_META, fife.Key.LEFT_META):
			self.metaPressed = True
	
		elif keyval == fife.Key.ESCAPE:
			scripts.editor.getEditor().quit()
		elif keyval == fife.Key.F10:
			self.engine.getGuiManager().getConsole().toggleShowHide()
		elif keystr == "d":
			pdb.set_trace()
			
		# Check keysequences
		for k in self.keysequences:
			if k.modifiers["alt"] != self.altPressed: continue
			if k.modifiers["ctrl"] != self.controlPressed: continue
			if k.modifiers["shift"]	!= self.shiftPressed: continue
			if k.modifiers["meta"] != self.metaPressed: continue
			if keyval != k.key: continue
			k.signal.send(sender=self, event=event)

	def keyReleased(self, event):
		keyval = event.getKey().getValue()
		
		self.controlPressed = event.isControlPressed()
		self.altPressed		= event.isAltPressed()
		self.shiftPressed	= event.isShiftPressed()
		self.metaPressed	= event.isMetaPressed()
		
		if keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
			self.controlPressed = False
		elif keyval in (fife.Key.LEFT_SHIFT, fife.Key.RIGHT_SHIFT):
			self.shiftPressed = False
		elif keyval in (fife.Key.LEFT_ALT, fife.Key.RIGHT_ALT):
			self.altPressed = False
		elif keyval in (fife.Key.RIGHT_META, fife.Key.LEFT_META):
			self.metaPressed = False

	
#--- Internal sublistener classes ---#
class _IKeyListener(IKeyListener):
	def __init__(self, engine):
		IKeyListener.__init__(self)
		self.engine = engine
		
	# IKeyListener
	def keyPressed(self, evt):
		keyPressed.send(sender=self.engine, event=evt)

	def keyReleased(self, evt):
		keyReleased.send(sender=self.engine, event=evt)

class _ICommandListener(ICommandListener):
	def __init__(self, engine):
		ICommandListener.__init__(self)
		self.engine = engine
		
	# ICommandListener
	def onCommand(self, command):
		if command.getCommandType() == fife.CMD_QUIT_GAME:
			scripts.editor.getEditor().quit()
		else:
			onCommand.send(sender=self.engine, command=command)
		
class _IMouseListener(IMouseListener):
	def __init__(self, engine):
		IMouseListener.__init__(self)
		self.engine = engine
		
	# IMouseListener
	def mouseEntered(self, evt):
		mouseEntered.send(sender=self.engine, event=evt)
	
	def mouseExited(self, evt):
		mouseExited.send(sender=self.engine, event=evt)
	
	def mousePressed(self, evt):
		mousePressed.send(sender=self.engine, event=evt)
	
	def mouseReleased(self, evt):
		mouseReleased.send(sender=self.engine, event=evt)
	
	def mouseClicked(self, evt):
		mouseClicked.send(sender=self.engine, event=evt)
	
	def mouseWheelMovedUp(self, evt):
		mouseWheelMovedUp.send(sender=self.engine, event=evt)
	
	def mouseWheelMovedDown(self, evt):
		mouseWheelMovedDown.send(sender=self.engine, event=evt)
	
	def mouseMoved(self, evt):
		mouseMoved.send(sender=self.engine, event=evt)
	
	def mouseDragged(self, evt):
		mouseDragged.send(sender=self.engine, event=evt)

class _MapChangeListener(MapChangeListener):
	def __init__(self, engine):
		MapChangeListener.__init__(self)
		self.engine = engine
		
	# MapChangeListener
	def onMapChanged(self, map, changedLayers):
		onMapChanged.send(sender=self.engine, map=map, changedLayers=changedLayers)
		
	def onLayerCreate(self, map, layer):
		onLayerCreate.send(sender=self.engine, map=map, layer=layer)
		
	def onLayerDelete(self, map, layer):
		onLayerDelete.send(sender=self.engine, map=map, layer=layer)
		
class _LayerChangeListener(LayerChangeListener):
	def __init__(self, engine):
		LayerChangeListener.__init__(self)
		self.engine = engine
		
	# LayerChangeListener
	def onLayerChanged(self, layer, changedInstances):
		onLayerChanged.send(sender=self.engine, layer=layer, changedInstances=changedInstances)
		
	def onInstanceCreate(self, layer, instance):
		onInstanceCreate.send(sender=self.engine, layer=layer, instance=instance)
		
	def onInstanceDelete(self, layer, instance):
		onInstanceDelete.send(sender=self.engine, layer=layer, instance=instance)
		
class _ConsoleExecuter(ConsoleExecuter):
	def __init__(self, engine):
		ConsoleExecuter.__init__(self)
		self.engine = engine
		
	# ConsoleExecuter
	def onToolsClick(self):
		onToolsClick.send(sender=self.engine)
		
	def onConsoleCommand(self, command):
		onConsoleCommand.send(sender=self.engine, command=command)
		
		