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

from fife.extensions import pychan
from fife.extensions.pychan import widgets, tools, attrs, internal
from fife.extensions.pychan.tools import callbackWithArguments
import scripts
import scripts.plugin as plugin
from scripts.events import *
from scripts.gui.action import Action
from fife import fife
from fife.fife import Color

# TODO:
# - Clean up code
# - Better event handling

_DEFAULT_BASE_COLOR = internal.DEFAULT_STYLE['default']['base_color']
_DEFAULT_SELECTION_COLOR = internal.DEFAULT_STYLE['default']['selection_color']
_DEFAULT_COLOR_STEP = Color(10, 10, 10)

class ObjectIcon(widgets.VBox):
	""" The ObjectIcon is used to represent the object in the object selector.
	"""	
	ATTRIBUTES = widgets.VBox.ATTRIBUTES + [ attrs.Attr("text"), attrs.Attr("image"), attrs.BoolAttr("selected") ]
	
	def __init__(self,callback,**kwargs):
		super(ObjectIcon,self).__init__(**kwargs)

		self.callback = callback	

		self.capture(self._mouseEntered, "mouseEntered")
		self.capture(self._mouseExited, "mouseExited")
		self.capture(self._mouseClicked, "mouseClicked")

		vbox = widgets.VBox(padding=3)

		# Icon
		self.icon = widgets.Icon(**kwargs)
		self.addChild(self.icon)

		# Label
		hbox = widgets.HBox(padding=1)
		self.addChild(hbox)
		self.label = widgets.Label(**kwargs)
		hbox.addChild(self.label)

	def _setText(self, text):
		self.label.text = text
		
	def _getText(self):
		return self.label.text
	text = property(_getText, _setText)

	def _setImage(self, image):
		self.icon.image = image

	def _getImage(self):
		return self.icon.image
	image = property(_getImage, _setImage)

	def _setSelected(self, enabled):
		if isinstance(self.parent, ObjectIconList):
			if enabled == True:
				self.parent.selected_item = self
			else:
				if self.selected:
					self.parent.selected_item = None
		
		if self.selected:
			self.base_color = _DEFAULT_SELECTION_COLOR
		else:
			self.base_color = _DEFAULT_BASE_COLOR

	def _isSelected(self):
		if isinstance(self.parent, ObjectIconList):
			return self == self.parent.selected_item
		return False
	selected = property(_isSelected, _setSelected)

	#--- Event handling ---#
	def _mouseEntered(self, event):
		self.base_color += _DEFAULT_COLOR_STEP

	def _mouseExited(self, event):
		self.base_color -= _DEFAULT_COLOR_STEP

	def _mouseClicked(self, event):
		self.selected = True
		self.callback()

class ObjectIconList(widgets.VBox):
	ATTRIBUTES = widgets.VBox.ATTRIBUTES
	
	def __init__(self,**kwargs):
		super(ObjectIconList, self).__init__(max_size=(5000,500000), **kwargs)
		self.base_color = self.background_color

		self.capture(self._keyPressed, "keyPressed")
		#self.capture(self._keyPressed, "keyReleased")
		self._selectedItem = None
		self.is_focusable = True

	def _keyPressed(self, event):
		print "KeyEvent", event

	def clear(self):
		for c in reversed(self.children):
			self.removeChild(c)

	def _setSelectedItem(self, item):
		if isinstance(item, ObjectIcon) or item is None:
			if self._selectedItem is not None:
				tmp = self._selectedItem
				self._selectedItem = item
				tmp.selected = False
			else:
				self._selectedItem = item
		#if item is not None:
		#	item.selected = True

	def _getSelectedItem(self):
		return self._selectedItem
	selected_item = property(_getSelectedItem, _setSelectedItem)
	
class ObjectSelector(plugin.Plugin):
	"""The ObjectSelector class offers a gui Widget that let's you select the object you
	wish to use to in the editor.
	@param engine: fife instance
	@param map: fife.Map instance containing your map
	@param selectNotify: callback function used to tell the editor you selected an object.
	"""
	def __init__(self):
		self.editor = None
		self.engine = None
		self.mode = 'list' # Other mode is 'preview'
		
		self._enabled = False
		self.object = None

	def enable(self):
		if self._enabled is True:
			return
			
		self.editor = scripts.editor.getEditor()
		self.engine = self.editor.getEngine()
			
		self._showAction = Action(u"Object selector", checkable=True)
		scripts.gui.action.activated.connect(self.toggle, sender=self._showAction)
		
		self.editor._tools_menu.addAction(self._showAction)
		
		events.postMapShown.connect(self.update_namespace)
		events.onObjectSelected.connect(self.setPreview)
		events.onObjectsImported.connect(self.update_namespace)
		
		self.buildGui()

	def disable(self):
		if self._enabled is False:
			return
			
		self.gui.hide()
		self.removeAllChildren()
		
		events.postMapShown.disconnect(self.update_namespace)
		events.onObjectSelected.disconnect(self.setPreview)
		events.onObjectsImported.disconnect(self.update_namespace)
		
		self.editor._tools_menu.removeAction(self._showAction)

	def isEnabled(self):
		return self._enabled;

	def getName(self):
		return "Object selector"
		

	def buildGui(self):
		self.gui = pychan.loadXML('gui/objectselector.xml')

		# Add search field
		self._searchfield = self.gui.findChild(name="searchField")
		self._searchfield.capture(self._search)
		self._searchfield.capture(self._search, "keyPressed")
		self.gui.findChild(name="searchButton").capture(self._search)
		
		# Add the drop down with list of namespaces
		self.namespaces = self.gui.findChild(name="namespaceDropdown")
		self.namespaces.items = self.engine.getModel().getNamespaces()
		self.namespaces.selected = 0

		# TODO: Replace with SelectionEvent, once pychan supports it
		self.namespaces.capture(self.update_namespace, "action")
		self.namespaces.capture(self.update_namespace, "mouseWheelMovedUp")
		self.namespaces.capture(self.update_namespace, "mouseWheelMovedDown")
		self.namespaces.capture(self.update_namespace, "keyReleased")

		# Object list
		self.mainScrollArea = self.gui.findChild(name="mainScrollArea")
		self.objects = None
		if self.mode == 'list':
			self.setTextList()
		else: # Assuming self.mode is 'preview'
			self.setImageList()

		# Action buttons
		self.gui.findChild(name="toggleModeButton").capture(self.toggleMode)
		self.gui.findChild(name="closeButton").capture(self.hide)

		# Preview area
		self.gui.findChild(name="previewScrollArea").background_color = self.gui.base_color
		self.preview = self.gui.findChild(name="previewIcon")
		

	def toggleMode(self):
		if self.mode == 'list':
			self.setImageList()
			self.mode = 'preview'
		elif self.mode == 'preview':
			self.setTextList()
			self.mode = 'list'
		self.update()


	def setImageList(self):
		"""Sets the mainScrollArea to contain a Vbox that can be used to fill in
		preview Images"""
		if self.objects is not None:
			self.mainScrollArea.removeChild(self.objects)
		self.objects = ObjectIconList(name='list', size=(200,1000))
		self.objects.base_color = self.mainScrollArea.background_color
		self.mainScrollArea.addChild(self.objects)

	def setTextList(self):
		"""Sets the mainScrollArea to contain a List that can be used to fill in
		Object names/paths"""
		if self.objects is not None:
			self.mainScrollArea.removeChild(self.objects)
		self.objects = widgets.ListBox(name='list')
		self.objects.capture(self.listEntrySelected)
		self.mainScrollArea.addChild(self.objects)

	def _search(self):
		self.search(self._searchfield.text)

	def search(self, str):
		results = []	
			
		# Format search terms
		terms = [term.lower() for term in str.split()]
		
		# Search
		if len(terms) > 0:
			namespaces = self.engine.getModel().getNamespaces()
			for namesp in namespaces:
				objects = self.engine.getModel().getObjects(namesp)
				for obj in objects:
					doAppend = True
					for term in terms:
						if obj.getId().lower().find(term) < 0:
							doAppend = False
							break
					if doAppend:
						results.append(obj)
		else:
			results = None
		
		if self.mode == 'list':
			self.fillTextList(results)
		elif self.mode == 'preview':
			self.fillPreviewList(results)

	def fillTextList(self, objects=None):
		if objects is None:
			if self.namespaces.selected_item is None:
				return
			objects = self.engine.getModel().getObjects(self.namespaces.selected_item)
		
		class _ListItem:
			def __init__( self, name, namespace ):
				self.name = name
				self.namespace = namespace
			def __str__( self ):
				return self.name
			
		
		self.objects.items = [_ListItem(obj.getId(), obj.getNamespace()) for obj in objects]
			
		if not self.object:
			if self.namespaces.selected_item:
				self.objects.selected = 0
				self.listEntrySelected()
		else:
			for i in range(0, len(self.objects.items)):
				if self.objects.items[i].name != self.object.getId(): continue
				if self.objects.items[i].namespace != self.object.getNamespace(): continue
				
				self.objects.selected = i
				break
				
				
		self.mainScrollArea.adaptLayout(False)
		scrollY = (self.objects.real_font.getHeight() + 0) * self.objects.selected
		self.mainScrollArea.real_widget.setVerticalScrollAmount(scrollY)

	def listEntrySelected(self):
		"""This function is used as callback for the TextList."""
		if self.objects.selected_item:
			object_id = self.objects.selected_item.name
			namespace = self.objects.selected_item.namespace
			obj = self.engine.getModel().getObject(object_id, namespace)
			self.objectSelected(obj)

	def fillPreviewList(self, objects=None):
		self.objects.clear()
		
		if objects is None:
			if self.namespaces.selected_item is None:
				return
			objects = self.engine.getModel().getObjects(self.namespaces.selected_item)
		
		for obj in objects:
			image = self._getImage(obj)
			if image is None:
				print 'No image available for selected object'
				image = ""

			callback = tools.callbackWithArguments(self.objectSelected, obj)	
			icon = ObjectIcon(callback=callback, image=image, text=unicode(obj.getId()))
			self.objects.addChild(icon)
			if obj == self.object:
				icon.selected = True
			
		if not self.object:
			if len(objects) > 0:
				self.objectSelected(objects[0])
				
		self.mainScrollArea.adaptLayout(False)
		self.mainScrollArea.real_widget.setVerticalScrollAmount(self.objects.selected_item.y)


	def objectSelected(self, obj):
		"""This is used as callback function to notify the editor that a new object has
		been selected.
		@param obj: fife.Object instance"""

		self.setPreview(obj)
		
		events.onObjectSelected.send(sender=self, object=obj)

		self.gui.adaptLayout(False)
		
	# Set preview image
	def setPreview(self, object):
		if not object: return
		if self.object and object == self.object:
			return
			
		self.object = object
		self.scrollToObject(object)
		self.preview.image = self._getImage(object)
		height = self.preview.image.getHeight();
		if height > 200: height = 200
		self.preview.parent.max_height = height
		
	def scrollToObject(self, object):
		# Select namespace
		names = self.namespaces
		if not names.selected_item: 
			self.namespaces.selected = 0
		
		if names.selected_item != object.getNamespace():
			for i in range(0, len(names.items)):
				if names.items[i] == object.getNamespace():
					self.namespaces.selected = i
					break
					
		self.update()

	def update_namespace(self):
		
		self.namespaces.items = self.engine.getModel().getNamespaces()
		if not self.namespaces.selected_item:
			self.namespaces.selected = 0
		if self.mode == 'list':
			self.setTextList()
		elif self.mode == 'preview':
			self.setImageList()
		self.update()

	def update(self):
		if self.mode == 'list':
			self.fillTextList()
		elif self.mode == 'preview':
			self.fillPreviewList()

		self.gui.adaptLayout(False)

	def _getImage(self, obj):
		""" Returns an image for the given object.
		@param: fife.Object for which an image is to be returned
		@return: fife.GuiImage"""
		visual = None
		try:
			visual = obj.get2dGfxVisual()
		except:
			print 'Visual Selection created for type without a visual?'
			raise

		# Try to find a usable image
		index = visual.getStaticImageIndexByAngle(0)
		image = None
		# if no static image available, try default action
		if index == -1:
			action = obj.getDefaultAction()
			if action:
				animation_id = action.get2dGfxVisual().getAnimationIndexByAngle(0)
				animation = self.engine.getAnimationPool().getAnimation(animation_id)
				image = animation.getFrameByTimestamp(0)
				index = image.getPoolId()

		# Construct the new GuiImage that is to be returned
		if index != -1:
			image = fife.GuiImage(index, self.engine.getImagePool())

		return image


	def show(self):
		self.update_namespace()
		self.gui.show()
		self._showAction.setChecked(True)

	def hide(self):
		self.gui.setDocked(False)
		self.gui.hide()
		self._showAction.setChecked(False)
		
	def toggle(self):
		if self.gui.isVisible() or self.gui.isDocked():
			self.hide()
		else:
			self.show()
