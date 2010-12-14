# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2010 by the FIFE team
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

""" a tool for FIFEdit to edit object and instance attributes """

from fife import fife
from fife.extensions import pychan
import fife.extensions.pychan.widgets as widgets
from fife.extensions.pychan.tools import callbackWithArguments as cbwa

from fife.extensions.fife_timer import Timer

import scripts
import scripts.plugin as plugin
from scripts.events import *
from scripts.gui.action import Action

import os
try:
	import xml.etree.cElementTree as ET
except:
	import xml.etree.ElementTree as ET

import math

WHITE = {
	"r"	:	205,
	"g"	:	205,
	"b"	:	205
}
OUTLINE_SIZE = 1

class ObjectEdit(plugin.Plugin):
	""" The B{ObjectEdit} module is a plugin for FIFedit and allows to edit
	attributes of an selected instance - like offset, instance id or rotation
	(namespaces and object id editing is excluded)
	
	current features:
		- click instance and get all known data
		- edit offsets, rotation, instance id
		- save offsets to object file
		- outline highlighting of the selected object
		- animation viewer
	"""
	def __init__(self):
		self.active = False
		self._camera = None
		self._layer = None
		self._anim_timer = None
		
		self._enabled = False
		
		self.imagepool = None
		self._animationpool = None
		
		self.guidata = {}
		self.objectdata = {}
		
		self._help_dialog = None

	def _reset(self):
		"""
			resets all dynamic vars, but leaves out static ones (e.g. camera, layer)

		"""
		if self._anim_timer:
			self._anim_timer.stop()
			# reset the ToggleButton
			if self._gui_anim_playback._isToggled():
				self._gui_anim_playback._setToggled(0)
		self._anim_timer = None
		
		self._object = None
		self._instances = None
		self._image = None
		self._image_default_x_offset = None
		self._image_default_y_offset = None
		self._animation = False
		self._anim_data = {}
		self._rotation = None
		self._avail_rotations = []
		self._namespace = None	
		self._object_blocking = 0
		self._instance_blocking = 0
		self._static = 0
		self._object_id = None	
		self._instance_id = None
		self._fixed_rotation = None
		
		if self._camera is not None:
			self.renderer.removeAllOutlines()			

	def enable(self):
		""" plugin method """
		if self._enabled is True:
			return
			
		self._editor = scripts.editor.getEditor()
		self.engine = self._editor.getEngine()
		
		self.imagepool = self.engine.getImagePool()
		self._animationpool = self.engine.getAnimationPool()
		
		self._showAction = Action(unicode(self.getName(),"utf-8"), checkable=True)
		scripts.gui.action.activated.connect(self.toggle_gui, sender=self._showAction)
	
		self._editor._tools_menu.addAction(self._showAction)
		
		events.onInstancesSelected.connect(self.input)
		events.preMapClosed.connect(self.hide)
		events.preMapShown.connect(self.hide)
		
		self._reset()		
		self.create_gui()

	def disable(self):
		""" plugin method """
		if self._enabled is False:
			return
			
		self._reset()
		self.container.hide()
		self.removeAllChildren()
		
		events.onInstancesSelected.disconnect(self.input)
		events.preMapClosed.disconnect(self.hide)
		events.preMapShown.disconnect(self.hide)
		
		self._editor._tools_menu.removeAction(self._showAction)

	def isEnabled(self):
		""" plugin method """
		return self._enabled;

	def getName(self):
		""" plugin method """
		return "Object editor"

	def _show_help(self):
		""" shows the help dialog """
		if self._help_dialog is not None:
			self._help_dialog.show()
			return
		
		self._help_dialog = pychan.loadXML("gui/help.xml")
		self._help_dialog.title = u"Help (Object Editor)"
		self._help_dialog.mapEvents({
			"closeButton" : self._help_dialog.hide,
		})
		
		# gimme some more space
		_SIZE = (320,400)
		scrollarea = self._help_dialog.findChildren(__class__=pychan.widgets.ScrollArea)[0]
		scrollarea.size = _SIZE
		scrollarea.min_size = _SIZE
		scrollarea.max_size = _SIZE
		
		f = open('lang/help_object_edit.txt', 'r')
		self._help_dialog.findChild(name="helpText").text = unicode(f.read())
		f.close()
		
		self._help_dialog.show()

	def create_gui(self):
		"""
			- creates the gui skeleton by loading the xml file
			- finds some important childs and saves their widget in the object
			
		FIXME:
			- move all dynamic widgets to dict
		"""
		self.container = pychan.loadXML('gui/objectedit.xml')
		self.container.mapEvents({
			'use_data'			: self.use_user_data,
			'change_data'		: self.save_user_data,
			
			'anim_left'			: self.previous_anim_frame,
			'anim_right'		: self.next_anim_frame,
			'anim_start_pos' 	: self.anim_start_frame,
			'anim_end_pos'		: self.anim_end_frame,
			
			'show_help'	: self._show_help,
		})
		
		self.container.findChild(name="x_offset_up").capture(self.change_offset, "mousePressed")
		self.container.findChild(name="x_offset_dn").capture(self.change_offset, "mousePressed")
		self._gui_x_offset = self.container.findChild(name="x_offset")
		self._gui_x_offset.capture(self.change_offset, "mouseWheelMovedUp")
		self._gui_x_offset.capture(self.change_offset, "mouseWheelMovedDown")

		self.container.findChild(name="y_offset_up").capture(self.change_offset, "mousePressed")
		self.container.findChild(name="y_offset_dn").capture(self.change_offset, "mousePressed")
		self._gui_y_offset = self.container.findChild(name="y_offset")
		self._gui_y_offset.capture(self.change_offset, "mouseWheelMovedUp")
		self._gui_y_offset.capture(self.change_offset, "mouseWheelMovedDown")

		self.container.findChild(name="object_blocking_toggle").capture(self.object_blocking_toggle, "mousePressed")
		self.container.findChild(name="instance_blocking_toggle").capture(self.instance_blocking_toggle, "mousePressed")

		self._gui_anim_panel_wrapper = self.container.findChild(name="animation_panel_wrapper")
		self._gui_anim_panel = self._gui_anim_panel_wrapper.findChild(name="animation_panel")
		
		self._gui_rotation_dropdown = self.container.findChild(name="select_rotations")
		self._gui_rotation_dropdown.capture(self.gui_rotate_instance,"mouseWheelMovedUp")
		self._gui_rotation_dropdown.capture(self.gui_rotate_instance,"mouseWheelMovedDown")
		self._gui_rotation_dropdown.capture(self.gui_rotate_instance,"action")	
		
		self._gui_anim_actions_dropdown = self._gui_anim_panel_wrapper.findChild(name="select_actions")	
		self._gui_anim_actions_dropdown.capture(self.eval_gui_anim_action,"mouseWheelMovedUp")
		self._gui_anim_actions_dropdown.capture(self.eval_gui_anim_action,"mouseWheelMovedDown")
		self._gui_anim_actions_dropdown.capture(self.eval_gui_anim_action,"action")	
		
		self._gui_anim_playback = self._gui_anim_panel_wrapper.findChild(name="anim_playback")
		self._gui_anim_playback.capture(self.anim_playback, "mousePressed")
		self._gui_anim_loop = self._gui_anim_panel_wrapper.findChild(name="anim_loop")

		self._gui_current_frame = self._gui_anim_panel_wrapper.findChild(name="anim_current_frame")
		self._gui_current_frame.capture(self.previous_anim_frame,"mouseWheelMovedUp")
		self._gui_current_frame.capture(self.next_anim_frame,"mouseWheelMovedDown")	
		
		self._gui_xoffset_textfield = self.container.findChild(name="x_offset")
		self._gui_yoffset_textfield = self.container.findChild(name="y_offset")
		
		self._gui_instance_id_textfield = self.container.findChild(name="instance_id")

	def anim_playback(self, widget):
		""" start / stop playback of an animation due to status of a gui ToggleButton
			Sets also two ivars of timer object (active & loop)
		"""
		if widget._isToggled():
			self._anim_timer.stop()
			self._anim_timer.active = False
		else:
			frame_delay = self._anim_data['obj'].getFrameDuration(self._anim_data['current'])
			self._anim_timer = Timer(delay=frame_delay,callback=self.next_anim_frame)
			self._anim_timer.active = True
			self._anim_timer.loop = self._gui_anim_loop._isMarked()
			self._anim_timer.start()
	
	def previous_anim_frame(self):
		""" show previous anim frame """
		if self._anim_data['current'] > 0:
			self._anim_data['current'] -= 1
		else:
			self._anim_data['current'] = self._anim_data['frames']

		self.update_gui()
		
	def next_anim_frame(self):
		""" show next anim frame and reset animation frame to 0 if playback looping is active"""
		if self._anim_data['current'] < self._anim_data['frames']:
			self._anim_data['current'] += 1
		else:
			self._anim_data['current'] = 0
			
		self.update_gui()
		
	def anim_start_frame(self):
		""" set start frame of animation """
		self._anim_data['current'] = 0
		self.update_gui()

	def anim_end_frame(self):
		""" set end frame of animation """		
		self._anim_data['current'] = self._anim_data['frames']
		self.update_gui()

	def update_gui(self):
		""" updates the gui widgets with current instance data """
		if self._instances is None: return
		
		# show the image we retrieved from an animated object
		if self._animation:
			if not self._gui_anim_panel_wrapper.findChild(name="animation_panel"):
				self._gui_anim_panel_wrapper.addChild(self._gui_anim_panel)			

			# get current selected image and update the icon widget				
			dur = 0
			for i in range(self._anim_data['frames']):
				dur += self._anim_data['obj'].getFrameDuration(i)
				
				# set new duration for the playback timer
				if self._anim_timer:
					frame_delay = self._anim_data['obj'].getFrameDuration(self._anim_data['current'])
				
				if i == self._anim_data['current']:
					# set new duration for the playback timer
					if self._anim_timer and self._anim_timer.active:
						self._anim_timer.setPeriod(self._anim_data['obj'].getFrameDuration(self._anim_data['current']))		
					break
											
			image = self._anim_data['obj'].getFrameByTimestamp(dur)	
			self.container.findChild(name="animTest").image = image.getResourceFile()
			self.container.findChild(name="animTest").size= (250,250)
			self.container.findChild(name="animTest").min_size= (250,250)
		
			self.container.distributeInitialData({
				'anim_current_frame'	:	unicode(str(self._anim_data['current'])),
				'anim_rotation'			:	unicode(str(self._anim_data['obj'].getDirection())),
			})	

		else:
			if self._gui_anim_panel_wrapper.findChild(name="animation_panel"):
				self._gui_anim_panel_wrapper.removeChild(self._gui_anim_panel)			
			
		if self._image is not None:
			x_offset = unicode( self._image.getXShift() )
			y_offset = unicode( self._image.getYShift() )
		else:
			x_offset = unicode( 0 )
			y_offset = unicode( 0 )

		if self._instances[0].isOverrideBlocking():
			self.container.findChild(name="override_blocking_toggle")._setMarked(True)
		else:
			self.container.findChild(name="override_blocking_toggle")._setMarked(False)

		self.container.distributeInitialData({
			'select_rotations' 	: self._avail_rotations,
			'instance_id'		: unicode( self._instances[0].getId() ),
			'object_id'			: unicode( self._object_id ),
			'x_offset'			: x_offset,
			'y_offset'			: y_offset,
			'instance_rotation' : unicode( self._instances[0].getRotation() ),
			'object_namespace'	: unicode( self._namespace ),
			'instance_blocking'	: unicode( self._instance_blocking ),
			'object_blocking'	: unicode( self._object_blocking ),
			'object_static'		: unicode( self._static ),
		})
		
		if not self._animation:
			if self._fixed_rotation in self._avail_rotations:
				index = self._avail_rotations.index( self._fixed_rotation )
				self._gui_rotation_dropdown._setSelected(index)
#			else:
#				print "Internal FIFE rotation: ", self._instances[0].getRotation()
#				print "Fixed rotation (cam rot) ", self._fixed_rotation + int(abs(self._camera.getRotation()))
#				print "Collected rots from object ", self._avail_rotations
				

		self.container.adaptLayout(False)			
		
	def toggle_gui(self):
		"""
			show / hide the gui
		"""
		if self.active is True:
			self.active = False
			if self.container.isVisible() or self.container.isDocked():
				self.container.setDocked(False)
				self.container.hide()
			self._showAction.setChecked(False)
		else:
			self.active = True
			self._showAction.setChecked(True)
	
	def highlight_selected_instance(self):
		""" highlights selected instance """
		self.renderer.removeAllOutlines() 
		self.renderer.addOutlined(self._instances[0], WHITE["r"], WHITE["g"], WHITE["b"], OUTLINE_SIZE)
			
	def change_offset(self, event, widget):
		""" widget callback: change the offset of an object 
		
		@type	event:	object
		@param	event:	FIFE mouseevent or keyevent
		@type	widget:	object
		@param	widget:	pychan widget
		"""
		if self._animation:
			self._editor.getStatusBar().setText(u"Offset changes of animations are not supported yet")
			return
		
		etype = event.getType()
		
		x = self._image.getXShift()
		y = self._image.getYShift()
		
		if etype == fife.MouseEvent.WHEEL_MOVED_UP or widget.name.endswith("up"):
			modifier = 1
		elif etype == fife.MouseEvent.WHEEL_MOVED_DOWN or widget.name.endswith("dn"):
			modifier = -1

		if widget.name.startswith("x"):
			x += modifier
		elif widget.name.startswith("y"):
			y += modifier

		self.set_offset(x, y)
		self.update_gui()

	def object_blocking_toggle(self, event, widget):
		""" widget callback: change the blocking of an instance 

		@type	event:	object
		@param	event:	FIFE mouseevent or keyevent
		@type	widget:	object
		@param	widget:	pychan widget
		"""
		self.check_override_blocking()
		object = self._instances[0].getObject()
		object_id = object.getId()
		blocking = not object.isBlocking()
		object.setBlocking(blocking)

		instances = self._layer.getInstances()
		for instance in instances:
			object = instance.getObject()
			if object.getId() == object_id:
				instance.setBlocking(blocking)

		self._object_blocking = int(blocking)
		self._instance_blocking = int(self._instances[0].isBlocking())

		self.update_gui()

	def instance_blocking_toggle(self, event, widget):
		""" widget callback: change the blocking of an instance 

		@type	event:	object
		@param	event:	FIFE mouseevent or keyevent
		@type	widget:	object
		@param	widget:	pychan widget
		"""
		self.check_override_blocking()
		instance = self._instances[0]
		instance.setBlocking(not instance.isBlocking())
		self._instance_blocking = int(instance.isBlocking())

		self.update_gui()

	def check_override_blocking(self):
		instance = self._instances[0]
		marked = self.container.findChild(name="override_blocking_toggle")._isMarked()
		if marked:
			instance.setOverrideBlocking(True)
		else:
			instance.setOverrideBlocking(False)

	def use_user_data(self):
		"""
			- takes the users values and applies them directly to the current ._instance
			- writes current data record
			- writes previous data record
			- updates gui
		
			FIXME:
			- parse user data in case user think strings are considered to be integer offset values...
		"""
		instance_id = str(self._gui_instance_id_textfield._getText())
		msg = ''
		
		if instance_id == "":
			instance_id = "None"

		if instance_id is not None and instance_id is not "None":
			existing_instances = self._editor.getActiveMapView().getController()._layer.getInstances(instance_id)
			if len(existing_instances) <= 0:
				self._instances[0].setId(instance_id)
				msg = unicode("Set new instance id: " + str(instance_id))
				self._editor.getStatusBar().setText(msg)
			else:
				self._editor.getStatusBar().setText(u"Instance ID is already in use.")

		if self._animation:
			msg = msg + "\n" + u"Editing offset and rotation of animated instances is not supported yet"
			self._editor.getStatusBar().setText(msg)
			return

		xoffset = self._gui_xoffset_textfield._getText()
		yoffset = self._gui_yoffset_textfield._getText()

		# update rotation
		angle = self.eval_gui_rotation()
		self.set_rotation(angle)
		
		# update offsets
		self.set_offset(int(xoffset), int(yoffset))

		self.update_gui()
		
	def save_user_data(self):
		""" saves the current object to its xml file 
		
			NOTE:
				- animations can't be saved for now
				
			FIXME:
				- add missing object attributes to saving routine		
		"""
		if self._object is None:
			return
		if self._animation:
			return
		
		file = self._object.getResourceFile()	
		self.tree = ET.parse(file)
		
		img_lst = self.tree.findall("image")

		# apply changes to the XML structure due to current user settings in the gui
		for img_tag in img_lst:
			if img_tag.attrib["direction"] == str(self._avail_rotations[self._gui_rotation_dropdown._getSelected()]):
				img_tag.attrib["x_offset"] = self._gui_xoffset_textfield._getText()
				img_tag.attrib["y_offset"] = self._gui_yoffset_textfield._getText()
				break

		block = self.tree.getroot()
		block.attrib["blocking"] = str(int(self._object_blocking))

		xmlcontent = ET.tostring(self.tree.getroot())

		# save xml data beneath the <?fife type="object"?> definition into the object file
		tmp = open(file, 'w')
		tmp.write('<?fife type="object"?>\n')
		tmp.write(xmlcontent + "\n")
		tmp.close()
		
	def gui_rotate_instance(self):
		""" rotate an instance due to selected angle """
		angle = self.eval_gui_rotation()
		self.set_rotation(angle)
		
	def eval_gui_rotation(self):
		""" prepare rotation from gui and apply it to the current selected instance """
		index = self._gui_rotation_dropdown._getSelected()
		angle = int( self._avail_rotations[index] )
	
		if angle == 360:
			angle = 0
			
		return angle
		
	def eval_gui_anim_action(self):	
		""" check the selected action of an animation and update the gui accordingly """
		if not self._anim_data['actions']: return
		
		index = self._gui_anim_actions_dropdown._getSelected()
		action = self._anim_data['actions'][index]
		
		self.update_anim_data(action)
		self.update_gui()
		
	def set_rotation(self, angle):
		""" set the rotation of the current instance """	
#		print "...setting instance rotation from %s to %s" % (self._rotation, angle)
		self._instances[0].setRotation(angle)
		self.get_instance_data(None, None, angle)
		self.update_gui()	
#		print "...new internal FIFE rotation ", int(self._instances[0].getRotation())
		
	def set_offset(self, x=None, y=None):
		""" set x/y offset of current selected instance """
		if x is not None:
			self._image.setXShift(x)
		if y is not None:
			self._image.setYShift(y)
			
	def update_anim_data(self, action=None):
		""" update animation data for the current selected instance from FIFE's data structure
		
		@type	animation	FIFE animation
		@return	animation	current selected animation
		"""
		if action:
			animation_id = action.get2dGfxVisual().getAnimationIndexByAngle(self._fixed_rotation)
			animation = self._animationpool.getAnimation(animation_id)		

		action_ids = []
		actions = []
		
		try:
			action_ids = self._object.getActionIds()
			for id in action_ids:
				actions.append(self._object.getAction(id))
		except:
			pass		
		
		self._anim_data = {}
		self._anim_data['obj'] = animation
		self._anim_data['id'] = animation_id
		self._anim_data['frames'] = animation.getNumFrames()
		self._anim_data['current'] = 0
		self._anim_data['actions'] = actions
		self._anim_data['action_ids'] = action_ids
		self._anim_data['default_action'] = self._object.getDefaultAction()	
		self._anim_data['action'] = action		

		return animation
		
	def get_instance_data(self, timestamp=None, frame=None, angle=-1, instance=None):
		"""
			- grabs all available data from both object and instance
		
		"""
		visual = None
		self._avail_rotations = []
			
		if instance is None:
			instance = self._instances[0]
			
		object = instance.getObject()
		self._object = object
		self._namespace = object.getNamespace()
		self._object_id = object.getId()
		
		self._instance_id = instance.getId()
	
		if self._instance_id == '':
			self._instance_id = 'None'

		if angle == -1:
			angle = int(instance.getRotation())
		else:
			angle = int(angle)	
			
		self._rotation = angle
		
		if object.isBlocking():
			self._object_blocking = 1

		if instance.isBlocking():
			self._instance_blocking = 1

		if object.isStatic():
			self._static = 1
		
		try:
			visual = object.get2dGfxVisual()
		except:
			self._editor.getStatusBar().setText(u"Fetching visual of object failed")
			raise			

		self._fixed_rotation = instance.getRotation()

		index = visual.getStaticImageIndexByAngle(self._fixed_rotation)

		if index is -1:
			# object is an animation
			self._animation = True
			self._image = None
			
			# no static image available, try default action
			action = object.getDefaultAction()

			if action:
				animation = self.update_anim_data(action)

				# update gui
				if animation:
					self._gui_anim_actions_dropdown._setItems(self._anim_data['action_ids'])
					self._gui_anim_actions_dropdown._setSelected(0)					
				
				if timestamp is None and frame is not None:
					self._image = animation.getFrame(frame)	
				elif timestamp is not None and frame is None:
					self._image = animation.getFrameByTimestamp(timestamp)
				else:
					self._image = animation.getFrameByTimestamp(0)
		elif index is not -1:
			# object is a static image
			self._animation = False
			self._image = self.imagepool.getImage(index)

		if not self._animation:
			rotations = visual.getStaticImageAngles()
			for angle in rotations:
				self._avail_rotations.append(angle)
	
			self._image_default_x_offset = self._image.getXShift()
			self._image_default_y_offset = self._image.getYShift()
		else:
			self._avail_rotations = object.getDefaultAction().get2dGfxVisual().getActionImageAngles()

	def show(self):
		""" show the plugin gui - and update it """
		self.update_gui()
		self.container.show()	
		self.container.adaptLayout(False)						
	
	def hide(self):
		""" hide the plugin gui - and reset it """
		self.container.hide()
		self._reset()		

	def input(self, instances):
		""" if called _and_ the user wishes to edit offsets,
			gets instance data and show gui

			(we only use the top instance of the selected cell)

		@type	instances:	list
		@param	instances:	a list of instances in the selected cell 
		"""
		if instances != self._instances:
			if self.active is True:
				self._reset()
				self._instances = instances
				
				if self._camera is None:
					self._camera = self._editor.getActiveMapView().getCamera()
					self.renderer = fife.InstanceRenderer.getInstance(self._camera)				
					
				self._layer = self._editor.getActiveMapView().getController()._layer
			
				if self._instances:
					self.highlight_selected_instance()
					self.get_instance_data()

					self.show()
				else:
					self.hide()
