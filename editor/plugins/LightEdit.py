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

""" a tool for FIFEdit to test and set lighting """

from fife import fife
from fife.extensions import pychan
from fife.extensions.pychan import widgets as widgets
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
import random

WHITE = {
	"r"	:	205,
	"g"	:	205,
	"b"	:	205
}
OUTLINE_SIZE = 1

DEFAULT_GLOBAL_LIGHT = {
	"R"	:	1.0,
	"G"	:	1.0,
	"B"	:	1.0,
	"A" :	1.0,
}

class LightEdit(plugin.Plugin):
	""" The B{LightEdit} module is a plugin for FIFedit and allows to use Lighting
	
	current features:
		- click instance to add SimpleLight, LightImage, LightAnimation
		- outline highlighting of the selected object
		- changeing all SimpleLigh values and Image, Animation source


	"""
	def __init__(self):
		self.active = False
		self._camera = None
		self._layer = None
		self._enabled = False

		self._light = {}
		self._color = {}
		self._color.update(DEFAULT_GLOBAL_LIGHT)

		random.seed()

	def _reset(self):
		"""
			resets all dynamic vars, but leaves out static ones (e.g. camera, layer)

		"""
		self._instances = None
		self._light["stencil"] = -1
		self._light["alpha"] = 0.0
		self._light["src"] = -1
		self._light["dst"] = -1
		
		self._light["intensity"] = 0
		self._light["red"] = 0
		self._light["green"] = 0
		self._light["blue"] = 0
		self._light["radius"] = 0
		self._light["subdivisions"] = 32
		self._light["xstretch"] = 1
		self._light["ystretch"] = 1

		self._light["image"] = ""
		self._light["animation"] = ""

		self._simple_l = False
		self._image_l = False
		self._animation_l = False
		self._global_l = False
		
		if self._camera is not None:
			self.renderer.removeAllOutlines()
			self._widgets["group"].text = unicode(str(""))
			self._widgets["image"].text = unicode(str(""))
			self._widgets["animation"].text = unicode(str(""))

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
		
		self._editor._toolsMenu.removeAction(self._showAction)

	def isEnabled(self):
		""" plugin method """
		return self._enabled;

	def getName(self):
		""" plugin method """
		return "Light editor"

	def create_gui(self):
		"""
			- creates the gui skeleton by loading the xml file
			
		FIXME:
			- move all dynamic widgets to dict
		"""
		self.container = pychan.loadXML('gui/lightedit.xml')
		self.container.mapEvents({
			"reset"				:	self.reset_light,
			"use"				:	self.use_light,
			"simple_but"		:	self.toggle_simple_gui,
			"image_but"			:	self.toggle_image_gui,
			"animation_but" 	:	self.toggle_animation_gui,
			"global_but" 		:	self.toggle_global_gui,
			"selec_image"		:	self.change_image,
			"selec_animation"	:	self.change_animation,

			"stencil_up" 		: cbwa(self.change_light, value=1, option="stencil"),
			"stencil_dn" 		: cbwa(self.change_light, value=-1, option="stencil"),
			"stencil/mouseWheelMovedUp"			:	cbwa(self.change_light, value=10, option="stencil"),
			"stencil/mouseWheelMovedDown" : cbwa(self.change_light, value=-10, option="stencil"),

			"alpha_up" 		: cbwa(self.change_light, value=0.01, option="alpha"),
			"alpha_dn" 		: cbwa(self.change_light, value=-0.01, option="alpha"),
			"alpha/mouseWheelMovedUp"			:	cbwa(self.change_light, value=0.1, option="alpha"),
			"alpha/mouseWheelMovedDown" : cbwa(self.change_light, value=-0.1, option="alpha"),			

			"intensity_up" 		: cbwa(self.change_light, value=1, option="intensity"),
			"intensity_dn" 		: cbwa(self.change_light, value=-1, option="intensity"),
			"intensity/mouseWheelMovedUp"			:	cbwa(self.change_light, value=10, option="intensity"),
			"intensity/mouseWheelMovedDown" : cbwa(self.change_light, value=-10, option="intensity"),

			"radius_up" 		: cbwa(self.change_light, value= 1, option="radius"),
			"radius_dn" 		: cbwa(self.change_light, value=-1, option="radius"),
			"radius/mouseWheelMovedUp"      : cbwa(self.change_light, value= 10, option="radius"),
			"radius/mouseWheelMovedDown"    : cbwa(self.change_light, value=-10, option="radius"),

			"subdivisions_up" 		: cbwa(self.change_light, value= 1, option="subdivisions"),
			"subdivisions_dn" 		: cbwa(self.change_light, value=-1, option="subdivisions"),
			"subdivisions/mouseWheelMovedUp"      : cbwa(self.change_light, value= 1, option="subdivisions"),
			"subdivisions/mouseWheelMovedDown"    : cbwa(self.change_light, value=-1, option="subdivisions"),

			"xstretch_up" 		: cbwa(self.change_light, value= 0.01, option="xstretch"),
			"xstretch_dn" 		: cbwa(self.change_light, value=-0.01, option="xstretch"),
			"xstretch/mouseWheelMovedUp"      : cbwa(self.change_light, value= 0.1, option="xstretch"),
			"xstretch/mouseWheelMovedDown"    : cbwa(self.change_light, value=-0.1, option="xstretch"),

			"ystretch_up" 		: cbwa(self.change_light, value= 0.01, option="ystretch"),
			"ystretch_dn" 		: cbwa(self.change_light, value=-0.01, option="ystretch"),
			"ystretch/mouseWheelMovedUp"      : cbwa(self.change_light, value= 0.1, option="ystretch"),
			"ystretch/mouseWheelMovedDown"    : cbwa(self.change_light, value=-0.1, option="ystretch"),

			"red_up" 		: cbwa(self.change_light, value= 1, option="red"),
			"red_dn" 		: cbwa(self.change_light, value=-1, option="red"),
			"red/mouseWheelMovedUp"         : cbwa(self.change_light, value= 10, option="red"),
			"red/mouseWheelMovedDown"       : cbwa(self.change_light, value=-10, option="red"),

			"green_up" 		: cbwa(self.change_light, value= 1, option="green"),
			"green_dn" 		: cbwa(self.change_light, value=-1, option="green"),
			"green/mouseWheelMovedUp"       : cbwa(self.change_light, value= 10, option="green"),
			"green/mouseWheelMovedDown"     : cbwa(self.change_light, value=-10, option="green"),

			"blue_up" 		: cbwa(self.change_light, value= 1, option="blue"),
			"blue_dn" 		: cbwa(self.change_light, value=-1, option="blue"),
			"blue/mouseWheelMovedUp"        : cbwa(self.change_light, value= 10, option="blue"),
			"blue/mouseWheelMovedDown"      : cbwa(self.change_light, value=-10, option="blue"),

			"src_up" 		: cbwa(self.change_light, value= 1, option="src"),
			"src_dn" 		: cbwa(self.change_light, value=-1, option="src"),
			"src/mouseWheelMovedUp"      : cbwa(self.change_light, value= 1, option="src"),
			"src/mouseWheelMovedDown"    : cbwa(self.change_light, value=-1, option="src"),

			"dst_up" 		: cbwa(self.change_light, value= 1, option="dst"),
			"dst_dn" 		: cbwa(self.change_light, value=-1, option="dst"),
			"dst/mouseWheelMovedUp"      : cbwa(self.change_light, value= 1, option="dst"),
			"dst/mouseWheelMovedDown"    : cbwa(self.change_light, value=-1, option="dst"),

			"random_global_light"	:	self.random_color,
			"reset_global_light"	:	self.reset_global_light,
			
			"increase_R"			:	cbwa(self.increase_color, r=True),
			"decrease_R"			:	cbwa(self.decrease_color, r=True),
			"value_R/mouseWheelMovedUp"			:	cbwa(self.increase_color, step=0.1, r=True),
			"value_R/mouseWheelMovedDown"		:	cbwa(self.decrease_color, step=0.1, r=True),
			
			"increase_G"			:	cbwa(self.increase_color, g=True),
			"decrease_G"			:	cbwa(self.decrease_color, g=True),
			"value_G/mouseWheelMovedUp"			:	cbwa(self.increase_color, step=0.1, g=True),
			"value_G/mouseWheelMovedDown"		:	cbwa(self.decrease_color, step=0.1, g=True),
			
			"increase_B"			:	cbwa(self.increase_color, b=True),
			"decrease_B"			:	cbwa(self.decrease_color, b=True),
			"value_B/mouseWheelMovedUp"			:	cbwa(self.increase_color, step=0.1, b=True),
			"value_B/mouseWheelMovedDown"		:	cbwa(self.decrease_color, step=0.1, b=True),
			
			"increase_A"			:	cbwa(self.increase_color, a=True),
			"decrease_A"			:	cbwa(self.decrease_color, a=True),			
			"value_A/mouseWheelMovedUp"			:	cbwa(self.increase_color, step=0.1, a=True),
			"value_A/mouseWheelMovedDown"		:	cbwa(self.decrease_color, step=0.1, a=True),			
		})

		self._widgets = {
			"group"				:	self.container.findChild(name="group"),
			"ins_id"			:	self.container.findChild(name="ins_id"),
			"obj_id"			:	self.container.findChild(name="obj_id"),
			"stencil"			:	self.container.findChild(name="stencil"),
			"alpha"				:	self.container.findChild(name="alpha"),
			
			"intensity"			:	self.container.findChild(name="intensity"),
			"red"                           :       self.container.findChild(name="red"),
			"green"                         :       self.container.findChild(name="green"),
			"blue"                          :       self.container.findChild(name="blue"),
			"radius"                        :       self.container.findChild(name="radius"),
			"subdivisions"                  :       self.container.findChild(name="subdivisions"),
			"xstretch"                      :       self.container.findChild(name="xstretch"),
			"ystretch"                      :       self.container.findChild(name="ystretch"),
			"src"	                        :       self.container.findChild(name="src"),
			"dst"	                        :       self.container.findChild(name="dst"),

			"image"	                        :       self.container.findChild(name="image"),
			"animation"						:       self.container.findChild(name="animation"),

			"value_R"				:	self.container.findChild(name="value_R"),
			"value_G"				:	self.container.findChild(name="value_G"),
			"value_B"				:	self.container.findChild(name="value_B"),
			"value_A"				:	self.container.findChild(name="value_A"),			
		}

		self._gui_simple_panel_wrapper = self.container.findChild(name="simple_panel_wrapper")
		self._gui_simple_panel = self._gui_simple_panel_wrapper.findChild(name="simple_panel")
		self._gui_image_panel_wrapper = self.container.findChild(name="image_panel_wrapper")
		self._gui_image_panel = self._gui_image_panel_wrapper.findChild(name="image_panel")
		self._gui_animation_panel_wrapper = self.container.findChild(name="animation_panel_wrapper")
		self._gui_animation_panel = self._gui_animation_panel_wrapper.findChild(name="animation_panel")
		self._gui_global_panel_wrapper = self.container.findChild(name="global_panel_wrapper")
		self._gui_global_panel = self._gui_global_panel_wrapper.findChild(name="global_panel")

	def update_gui(self):
		"""
			updates the gui
			
		"""

		self._widgets["ins_id"].text = unicode(str(self._instances[0].getId()))
		self._widgets["obj_id"].text = unicode(str(self._instances[0].getObject().getId()))
		self._widgets["stencil"].text = unicode(str(self._light["stencil"]))
		self._widgets["alpha"].text = unicode(str(self._light["alpha"]))
		self._widgets["src"].text = unicode(str(self._light["src"]))
		self._widgets["dst"].text = unicode(str(self._light["dst"]))
		
		self._widgets["intensity"].text = unicode(str(self._light["intensity"]))
		self._widgets["red"].text = unicode(str(self._light["red"]))
		self._widgets["green"].text = unicode(str(self._light["green"]))
		self._widgets["blue"].text = unicode(str(self._light["blue"]))
		self._widgets["radius"].text = unicode(str(self._light["radius"]))
		self._widgets["subdivisions"].text = unicode(str(self._light["subdivisions"]))
		self._widgets["xstretch"].text = unicode(str(self._light["xstretch"]))
		self._widgets["ystretch"].text = unicode(str(self._light["ystretch"]))

		self._widgets["value_R"].text = unicode(str(self._color["R"]))
		self._widgets["value_G"].text = unicode(str(self._color["G"]))
		self._widgets["value_B"].text = unicode(str(self._color["B"]))
		self._widgets["value_A"].text = unicode(str(self._color["A"]))		
		
		if self._simple_l:
			if not self._gui_simple_panel_wrapper.findChild(name="simple_panel"):
				self._gui_simple_panel_wrapper.addChild(self._gui_simple_panel)
		else:
			if self._gui_simple_panel_wrapper.findChild(name="simple_panel"):
				self._gui_simple_panel_wrapper.removeChild(self._gui_simple_panel)
		if self._image_l:
			if not self._gui_image_panel_wrapper.findChild(name="image_panel"):
				self._gui_image_panel_wrapper.addChild(self._gui_image_panel)
		else:
			if self._gui_image_panel_wrapper.findChild(name="image_panel"):
				self._gui_image_panel_wrapper.removeChild(self._gui_image_panel)
		if self._animation_l:
			if not self._gui_animation_panel_wrapper.findChild(name="animation_panel"):
				self._gui_animation_panel_wrapper.addChild(self._gui_animation_panel)
		else:
			if self._gui_animation_panel_wrapper.findChild(name="animation_panel"):
				self._gui_animation_panel_wrapper.removeChild(self._gui_animation_panel)
		if self._global_l:
			if not self._gui_global_panel_wrapper.findChild(name="global_panel"):
				self._gui_global_panel_wrapper.addChild(self._gui_global_panel)
		else:
			if self._gui_global_panel_wrapper.findChild(name="global_panel"):
				self._gui_global_panel_wrapper.removeChild(self._gui_global_panel)
		
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

	def toggle_simple_gui(self):
		if self._simple_l:
			self._simple_l = False
		else:
			self._simple_l = True
			self._image_l = False
			self._animation_l = False
		self.update_gui()

	def toggle_image_gui(self):
		if self._image_l:
			self._image_l = False
		else:
			self._simple_l = False
			self._image_l = True
			self._animation_l = False
		self.update_gui()

	def toggle_animation_gui(self):
		if self._animation_l:
			self._animation_l = False
		else:
			self._simple_l = False
			self._image_l = False
			self._animation_l = True
		self.update_gui()

	def toggle_global_gui(self):
		if self._global_l:
			self._global_l = False
		else:
			self._global_l = True
		self.update_gui()

	def init_data(self):
		color = self._camera.getLightingColor()
		self._color["R"] = color[0]
		self._color["G"] = color[1]
		self._color["B"] = color[2]
		self._color["A"] = color[3]
		
		groups = self.lightrenderer.getGroups()
		for group in groups:
			infos = self.lightrenderer.getLightInfo(group)
			for info in infos:
				node = info.getNode()
				if node.getInstance() is None: continue
				if node.getInstance().getId() == self._instances[0].getId():
					self._widgets["group"].text = unicode(str(group))
					self._light["stencil"] = info.getStencil()
					self._light["alpha"] = info.getAlpha()
					self._light["src"] = info.getSrcBlend()
					self._light["dst"] = info.getDstBlend()
					if str(info.getName()) == "simple":
						self._light["red"] = info.getColor()[0]
						self._light["green"] = info.getColor()[1]
						self._light["blue"] = info.getColor()[2]
						self._light["intensity"] = info.getColor()[3]
						self._light["radius"] = info.getRadius()
						self._light["subdivisions"] = info.getSubdivisions()
						self._light["xstretch"] = info.getXStretch()
						self._light["ystretch"] = info.getYStretch()
						self.toggle_simple_gui()
					elif str(info.getName()) == "image":
						if info.getId() == -1: continue
						img = self.imagepool.getImage(info.getId());
						name = img.getResourceFile()
						self._widgets["image"].text = unicode(str(name))
						self._light["image"] = info.getId()
						self.toggle_image_gui()
					elif str(info.getName()) == "animation":
						if info.getId() == -1: continue
						ani = self._animationpool.getAnimation(info.getId());
						count = 0
						newstr = ''
						image = ani.getFrame(ani.getActionFrame())
						fname = image.getResourceFile()
						strings = ([str(s) for s in fname.split('/')])
						leng = len(strings) -1
						while count < leng:
							newstr = str(newstr + strings[count] + '/')
							count += 1
						self._widgets["animation"].text = unicode(str(newstr + 'animation.xml'))
						self._light["animation"] = info.getId()
						self.toggle_animation_gui()

	def change_image(self):
		file = self._editor.getObject().getResourceFile()
		tree = ET.parse(file)
		img_lst = tree.findall("image")
		for image in img_lst:
			source = image.get('source')
			path = file.split('/')
			path.pop()
			path.append(str(source))
			self._widgets["image"].text = unicode(str('/'.join(path)))
			break

	def change_animation(self):
		file = self._editor.getObject().getResourceFile()
		tree = ET.parse(file)
		ani_lst = tree.findall("animation")
		if not ani_lst:
			act_lst = tree.findall("action")
			if not act_lst: return
			for act in act_lst:
				ani_lst = act.findall("animation")
				if ani_lst: break

		for animation in ani_lst:
			source = animation.get('source')
			path = file.split('/')
			path.pop()
			path.append(str(source))
			self._widgets["animation"].text = unicode(str('/'.join(path)))
			break

	def reset_light(self):
		self._light["stencil"] = -1
		self._light["alpha"] = 0.0
		self._light["src"] = -1
		self._light["dst"] = -1
		
		self._light["intensity"] = 0
		self._light["red"] = 0
		self._light["green"] = 0
		self._light["blue"] = 0
		self._light["radius"] = 0
		self._light["subdivisions"] = 32
		self._light["xstretch"] = 1
		self._light["ystretch"] = 1
		
		self._light["image"] = ""
		self._light["animation"] = ""
		
		self.lightrenderer.removeAll(str(self._widgets["group"]._getText()))
		self._widgets["group"].text = unicode(str(""))
		self._widgets["image"].text = unicode(str(""))
		self._widgets["animation"].text = unicode(str(""))
		self.update_gui()

	def use_light(self):
		if not self._instances[0]: return
		counter = 1
		if self._widgets["ins_id"]._getText() == "":
			objid = self._instances[0].getObject().getId()
			insid = str(objid + str(counter))
			while bool(self._layer.getInstance(insid)):
				counter = int(counter+1)
				insid = str(objid + str(counter))
			self._instances[0].setId(insid)
		
		if self._light["stencil"] is not -1 and self._light["alpha"] is not 0.0: self.stencil_test()
		if self._simple_l: self.simple_light()
		if self._image_l: self.image_light()
		if self._animation_l: self.animation_light()

	def highlight_selected_instance(self):
		""" highlights selected instance """
		self.renderer.removeAllOutlines() 
		self.renderer.addOutlined(self._instances[0], WHITE["r"], WHITE["g"], WHITE["b"], OUTLINE_SIZE)

	def change_light(self, value=0.01, option=None):
		self._light[option] = self._light[option] + value
		if self._light[option]+ value < -1 and (option == "src" or option == "dst" or option == "stencil"):
			self._light[option] = -1
		if self._light[option]+ value < 0 and option != "src" and option != "dst" and option != "stencil":
			self._light[option] = 0
		if self._light[option]+ value > 7 and (option == "src" or option == "dst"):
			self._light[option] = 7
		if self._light[option]+ value > 255 and (option == "intensity"
											or option == "red"
											or option == "green"
											or option == "blue"
											or option == "stencil"):
			self._light[option] = 255
		if self._light[option]+ value > 1 and option == "alpha":
			self._light[option] = 1.0			

		self.update_gui()

	def stencil_test(self):
		self.lightrenderer.addStencilTest(str(self._widgets["group"]._getText()), self._light["stencil"], self._light["alpha"])

	def simple_light(self):
		if not self._instances[0]: return
		self.lightrenderer.removeAll(str(self._widgets["group"]._getText()))

		node = fife.LightRendererNode(self._instances[0])
		self.lightrenderer.addSimpleLight(str(self._widgets["group"]._getText()),
											node,
											self._light["intensity"],
											self._light["radius"],
											self._light["subdivisions"],
											self._light["xstretch"],
											self._light["ystretch"],
											self._light["red"],
											self._light["green"],
											self._light["blue"],
											self._light["src"],
											self._light["dst"],)

	def image_light(self):
		if not self._instances[0]: return
		self.lightrenderer.removeAll(str(self._widgets["group"]._getText()))

		image = str(self._widgets["image"]._getText())
		if image == "": return
		img_id = self.imagepool.addResourceFromFile(image)
		self._light["image"] = int(img_id)
		node = fife.LightRendererNode(self._instances[0])
		self.lightrenderer.addImage(str(self._widgets["group"]._getText()),
											node,
											self._light["image"],
											self._light["src"],
											self._light["dst"],)

	def animation_light(self):
		if not self._instances[0]: return
		self.lightrenderer.removeAll(str(self._widgets["group"]._getText()))

		animation = str(self._widgets["animation"]._getText())
		if animation == "": return
		rloc = fife.ResourceLocation(animation)
		ani_id = self._animationpool.addResourceFromLocation(rloc)
		self._light["animation"] = int(ani_id)
		node = fife.LightRendererNode(self._instances[0])
		self.lightrenderer.addAnimation(str(self._widgets["group"]._getText()),
											node,
											self._light["animation"],
											self._light["src"],
											self._light["dst"],)

	def reset_global_light(self):
		""" reset global light to default values (1.0) """
		self._color.update(DEFAULT_GLOBAL_LIGHT)
		self.update_gui()
		self.set_global_light()
			
	def increase_color(self, step=0.1, r=None, g=None, b=None, a=None):
		"""	increase a given color value by step value
		
		@type	step	float
		@param	step	the step for changing the color channel
		@type	r		bool
		@param	r		flag to alter red color value
		@type	g		bool
		@param	g		flag to alter green color value
		@type	b		bool
		@param	b		flag to alter blue color value
		@type	a		bool
		@type	a		flag to alter alpha channel value (no effect atm)		
		"""
		if r:
			if self._color["R"] + step > 1.0:
				self._color["R"] = 1.0
			else:
				self._color["R"] += step
		if g:
			if self._color["G"] + step > 1.0:
				self._color["G"] = 1.0
			else:
				self._color["G"] += step
		if b:
			if self._color["B"] + step > 1.0:
				self._color["B"] = 1.0
			else:
				self._color["B"] += step
		if a:
			if self._color["A"] + step > 1.0:
				self._color["A"] = 1.0
			else:
				self._color["A"] += step

		self.update_gui()					
		self.set_global_light()
			
	def decrease_color(self, step=0.1, r=None, g=None, b=None, a=None):
		"""	decrease a given color value by step value
		
		@type	step	float
		@param	step	the step for changing the color channel
		@type	r		bool
		@param	r		flag to alter red color value
		@type	g		bool
		@param	g		flag to alter green color value
		@type	b		bool
		@param	b		flag to alter blue color value
		@type	a		bool
		@type	a		flag to alter alpha channel value (no effect atm)		
		"""
		if r:
			if self._color["R"] - step < 0.0:
				self._color["R"] = 0.0
			else:
				self._color["R"] -= step
		if g:
			if self._color["G"] - step < 0.0:
				self._color["G"] = 0.0
			else:
				self._color["G"] -= step
		if b:
			if self._color["B"] - step < 0.0:
				self._color["B"] = 0.0
			else:
				self._color["B"] -= step
		if a:
			if self._color["A"] - step < 0.0:
				self._color["A"] = 0.0
			else:
				self._color["A"] -= step
			
		self.update_gui()					
		self.set_global_light()
			
	def random_color(self):
		""" generate random values for color channels """
		self._color["R"] = random.uniform(0,1)
		self._color["G"] = random.uniform(0,1)
		self._color["B"] = random.uniform(0,1)
		self._color["A"] = random.uniform(0,1)

		self.update_gui()					
		self.set_global_light()
		
	def set_global_light(self):
		""" update the global light with the current set colors """
		self._camera.setLightingColor(self._color["R"],
									  self._color["G"],
									  self._color["B"],
									  self._color["A"]
									  )

	def input(self, instances):
		if instances != self._instances:
			if self.active is True:
				self._reset()
				self._instances = instances
				
				if self._camera is None:
					self._camera = self._editor.getActiveMapView().getCamera()
					self.renderer = fife.InstanceRenderer.getInstance(self._camera)
					self.lightrenderer = fife.LightRenderer.getInstance(self._camera)
					
				self._layer = self._editor.getActiveMapView().getController()._layer
			
				if self._instances != ():
					self.init_data()
					self.highlight_selected_instance()
					self.update_gui()
					self.container.show()
				else:
					self._reset()
					self.container.hide()
					
		self.container.adaptLayout(False)						
